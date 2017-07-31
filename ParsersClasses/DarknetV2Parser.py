import glob

import numpy
import sys

import struct

from ObjectDetectionParser import ObjectDetectionParser
import re
import csv
import os

from SupportClasses import PrecisionAndRecall
from SupportClasses import Rectangle
from SupportClasses import _GoldContent
from SupportClasses.CNNLayerParser import CNNLayerParser


class DarknetV2Parser(ObjectDetectionParser):
    __executionType = None
    __executionModel = None
    __weights = None
    __configFile = None

    __errorTypes = ['allLayers', 'filtered2', 'filtered5', 'filtered50']
    __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "precision",
                  "recall", "false_negative", "false_positive", "true_positive", "abft_type", "row_detected_errors",
                  "col_detected_errors", "failed_layer", "header"]

    __layerDimensions = {0: [608, 608, 32],
                         1: [304, 304, 32],
                         2: [304, 304, 64],
                         3: [152, 152, 64],
                         4: [152, 152, 128],
                         5: [152, 152, 64],
                         6: [152, 152, 128],
                         7: [76, 76, 128],
                         8: [76, 76, 256],
                         9: [76, 76, 128],
                         10: [76, 76, 256],
                         11: [38, 38, 256],
                         12: [38, 38, 512],
                         13: [38, 38, 256],
                         14: [38, 38, 512],
                         15: [38, 38, 256],
                         16: [38, 38, 512],
                         17: [19, 19, 512],
                         18: [19, 19, 1024],
                         19: [19, 19, 512],
                         20: [19, 19, 1024],
                         21: [19, 19, 512],
                         22: [19, 19, 1024],
                         23: [19, 19, 1024],
                         24: [19, 19, 1024],
                         25: [],
                         26: [38, 38, 64],
                         27: [19, 19, 256],
                         28: [],
                         29: [19, 19, 1024],
                         30: [19, 19, 425],
                         31: []}

    _sizeOfDnn = 0

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""
    _failed_layer = ""
    _cnnParser = None

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        self._sizeOfDnn = len(self.__layerDimensions)

        if self._parseLayers:
            self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
            self.__layersPath = str(kwargs.pop("layersPath"))
            self._cnnParser = CNNLayerParser(layersDimention=self.__layerDimensions,
                                             layerGoldPath=self.__layersGoldPath,
                                             layerPath=self.__layersPath, dnnSize=self._sizeOfDnn, correctableLayers=[])

            self._csvHeader.extend(self._cnnParser.genCsvHeader())

    def _writeToCSV(self, csvFileName):
        self._writeCSVHeader(csvFileName)

        csvWFP = open(csvFileName, "a")
        writer = csv.writer(csvWFP, delimiter=';')

        outputList = [self._logFileName,
                      self._machine,
                      self._benchmark,
                      self._sdcIteration,
                      self._accIteErrors,
                      self._iteErrors,
                      self._goldLines,
                      self._detectedLines,
                      self._wrongElements,
                      self._precision,
                      self._recall,
                      self._falseNegative,
                      self._falsePositive,
                      self._truePositive,
                      self._abftType,
                      self._rowDetErrors,
                      self._colDetErrors,
                      self._failed_layer,
                      self._header]

        if (self._parseLayers):
            outputList.extend(self._cnnParser.getOutputToCsv())

        writer.writerow(outputList)
        csvWFP.close()

    def setSize(self, header):
        ##HEADER gold_file: temp.csv save_layer: 1 abft_type: 0 iterations: 1
        sizeM = re.match(".*gold_file\: (\S+).*save_layer\: (\d+).*abft_type\: (\S+).*iterations\: (\d+).*", header)
        if sizeM:
            self._goldFileName = sizeM.group(1)
            self._saveLayer = sizeM.group(2)
            self._abftType = sizeM.group(3)
            self._iterations = sizeM.group(4)
        self._size = "gold_file_" + os.path.basename(self._goldFileName) + "_abft_" + str(self._abftType)

    def _relativeErrorParser(self, errList):
        if len(errList) == 0:
            return
        # ---------------------------------------------------------------------------------------------------------------
        # open and load gold
        goldKey = self._machine + "_" + self._benchmark + "_" + self._size

        if self._machine in self._goldBaseDir:
            goldPath = self._goldBaseDir[self._machine] + "/darknetv2/" + self._goldFileName
        else:
            print 'not indexed machine: ', self._machine, " set it on Parameters.py"
            return

        if goldKey not in self._goldDatasetArray:
            g = _GoldContent._GoldContent(nn='darknetv2', filepath=goldPath)
            self._goldDatasetArray[goldKey] = g

        gold = self._goldDatasetArray[goldKey]

        # for layers parser
        self._imgListSize = gold.getPlistSize()
        # ---------------------------------------------------------------------------------------------------------------
        # img path
        # this is possible since errList has at least 1 element, due verification
        imgFilename = errList[0]["img"]
        goldPb = gold.getProbArray(imgPath=imgFilename)
        goldRt = gold.getRectArray(imgPath=imgFilename)

        foundPb = numpy.empty_like(goldPb)
        foundPb[:] = goldPb

        foundRt = numpy.empty_like(goldRt)
        foundRt[:] = goldRt

        for err in errList:
            # NEED TO BE CHECK
            i = err["prob_i"]
            class_ = err["prob_j"]

            lr = err["x_r"]
            br = err["y_r"]
            hr = err["h_r"]
            wr = err["w_r"]
            # gold correct
            le = err["x_e"]
            be = err["y_e"]
            he = err["h_e"]
            we = err["w_e"]

            foundRt[i] = Rectangle.Rectangle(lr, br, wr, hr)
            # t = goldRt[rectPos].deepcopy()
            goldRt[i] = Rectangle.Rectangle(le, be, we, he)

            foundPb[i][class_] = err["prob_r"]
            goldPb[i][class_] = err["prob_e"]

        #############
        # before keep going is necessary to filter the results
        h, w, c = gold.getImgDim(imgPath=imgFilename)
        gValidRects, gValidProbs, gValidClasses = self.__filterResults(rectangles=goldRt, probabilites=goldPb,
                                                                       total=gold.getTotalSize(),
                                                                       classes=gold.getClasses(), h=h, w=w)
        fValidRects, fValidProbs, fValidClasses = self.__filterResults(rectangles=foundRt, probabilites=foundPb,
                                                                       total=gold.getTotalSize(),
                                                                       classes=gold.getClasses(), h=h, w=w)

        precisionRecallObj = PrecisionAndRecall.PrecisionAndRecall(self._prThreshold)
        gValidSize = len(gValidRects)
        fValidSize = len(fValidRects)

        precisionRecallObj.precisionAndRecallParallel(gValidRects, fValidRects)
        self._precision = precisionRecallObj.getPrecision()
        self._recall = precisionRecallObj.getRecall()

        if self._parseLayers:
            """
             sdcIteration = which iteration SDC appeared
             logFilename = the name of the log file
             imgListSize = size of images dataset
             machine = testing device
             loadLayerMethod = an external method which open an specific layer on an external class
            """
            self._cnnParser.parseLayers(sdcIteration=self._sdcIteration,
                                        logFilename=self._logFileName,
                                        machine=self._machine,
                                        loadLayerMethod=self.loadLayer)

        if self._imgOutputDir and (self._precision != 1 or self._recall != 1):
            drawImgFileName = self._localRadiationBench + "/data/CALTECH/" \
                              + os.path.basename(imgFilename.rstrip())

            self.buildImageMethod(drawImgFileName, gValidRects, fValidRects, str(self._sdcIteration)
                                  + '_' + self._logFileName, self._imgOutputDir)

        self._falseNegative = precisionRecallObj.getFalseNegative()
        self._falsePositive = precisionRecallObj.getFalsePositive()
        self._truePositive = precisionRecallObj.getTruePositive()
        # set all
        self._goldLines = gValidSize
        self._detectedLines = fValidSize

    def __filterResults(self, rectangles, probabilites, total, classes, h, w):
        validRectangles = []
        validProbs = []
        validClasses = []

        for i in range(0, total):
            box = rectangles[i]
            # Keep in mind that it is not the left and botton
            # it is the CENTER of darknet box
            bX = box.left
            bY = box.bottom

            left = (bX - box.width / 2.) * w
            right = (bX + box.width / 2.) * w
            top = (bY + box.height / 2.) * h
            bot = (bY - box.height / 2.) * h

            width = box.width * w
            height = box.height * h

            for j in range(0, classes):
                if probabilites[i][j] >= self._detectionThreshold:
                    validProbs.append(probabilites[i][j])
                    rect = Rectangle.Rectangle(int(left), int(bot), int(width), int(height))
                    validRectangles.append(rect)
                    validClasses.append(self._classes[j])

        return validRectangles, validProbs, validClasses

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        ret = {}
        darknetM = re.match(
            ".*img\: \[(\S+)\].*prob\[(\d+)\]\[(\d+)\].*r\:(\S+).*e\:(\S+).*x_r\: (\S+).*x_e\: "
            "(\S+).*y_r\: (\S+).*y_e\: (\S+).*w_r\: (\S+).*w_e\: (\S+).*h_r\: (\S+).*h_e\: (\S+).*",
            errString)

        if darknetM:
            ret["img"] = str(darknetM.group(1))
            # ERR img: [0] prob[60][0] r:0.0000000000000000e+00 e:0.0000000000000000e+00
            ret["prob_i"] = int(darknetM.group(2))
            ret["prob_j"] = int(darknetM.group(3))

            try:
                ret["prob_r"] = float(darknetM.group(4))
            except:
                ret["prob_r"] = 1e10

            try:
                ret["prob_e"] = float(darknetM.group(5))
            except:
                ret["prob_e"] = 1e10

            # x_r: 1.7303885519504547e-01 x_e: 3.3303898572921753e-01
            try:
                ret["x_r"] = float(darknetM.group(6))
            except:
                ret["x_r"] = 1e10

            try:
                ret["x_e"] = float(darknetM.group(7))
            except:
                ret["x_e"] = 1e10

            # y_r: 1.0350487381219864e-01 y_e: 1.0350500047206879e-01
            try:
                ret["y_r"] = float(darknetM.group(8))
            except:
                ret["y_r"] = 1e10

            try:
                ret["y_e"] = float(darknetM.group(9))
            except:
                ret["y_e"] = 1e10

            # w_r: 2.0466668531298637e-02 w_e: 2.0467000082135201e-02
            try:
                ret["w_r"] = float(darknetM.group(10))
            except:
                ret["w_r"] = 1e10

            try:
                ret["w_e"] = float(darknetM.group(11))
            except:
                ret["w_e"] = 1e10

            # h_r: 4.1410662233829498e-02 h_e: 4.1411001235246658e-02
            try:
                ret["h_r"] = float(darknetM.group(12))
            except:
                ret["h_r"] = 1e10

            try:
                ret["h_e"] = float(darknetM.group(13))
            except:
                ret["h_e"] = 1e10

            return ret

        return None

    # ---------------------------------------------------------------------------------------------------------------------
    """
    loadLayer
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    # carrega de um log para uma matriz
    def loadLayer(self, layerNum, isGold = False):
        # it is better to programing one function only than two almost equal
        imgListpos = int(self._sdcIteration) % self._imgListSize
        if isGold:
            # 2017_07_28_19_21_26_cudaDarknetv2_ECC_ON_carol.log_layer_0_img_0_test_it_0.layer
            layerFilename = self.__layersPath + self._logFileName + "_layer_" + str(layerNum) + "_img_" + str(
                imgListpos) + "_test_it_" + str(self._sdcIteration) + ".layer"
        else:
            # carrega de um log para uma matriz
            # goldIteration = str(int(self._sdcIteration) % self._imgListSize)
            # gold_layers/gold_layer_0_img_0_test_it_0.layer
            layerFilename = self.__layersGoldPath + "gold_layer_darknet_v2_" + str(layerNum) + "_img_" + str(
                imgListpos) + "_test_it_0.layer"

        filenames = glob.glob(layerFilename)

        if (len(filenames) == 0):
            return None
        elif (len(filenames) > 1):
            print('+de 1 layer encontrada para \'' + layerFilename + '\'')

        filename = filenames[0]
        layerSize = self.getSizeOfLayer(layerNum)

        layerFile = open(filename, "rb")
        numItens = layerSize  # float size = 4bytes

        layerContents = struct.unpack('f' * numItens, layerFile.read(4 * numItens))
        layer = None
        # botar em matriz 3D
        if len(self.__layerDimensions[layerNum]) == 3 :
            layer = self.tupleTo3DMatrix(layerContents, layerNum)
        elif len(self.__layerDimensions[layerNum]) == 1:
            layer = self.tupleToArray(layerContents, layerNum)

        layerFile.close()

        return layer

    """
    tupleTo3DMatrix
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    def tupleTo3DMatrix(self, layerContents, layerNum):
        dim = self.__layerDimensions[layerNum]  # width,height,depth
        layer = [[[0 for k in xrange(dim[2])] for j in xrange(dim[1])] for i in xrange(dim[0])]
        for i in range(0, dim[0]):
            for j in range(0, dim[1]):
                for k in range(0, dim[2]):
                    contentsIndex = (i * dim[1] + j) * dim[2] + k
                    layer[i][j][k] = layerContents[contentsIndex]
        return layer

    """
    tupleToArray
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    def tupleToArray(self, layerContents, layerNum):
        size = self.__layerDimensions[layerNum][0]
        layer = [0 for i in xrange(0, size)]
        for i in range(0, size):
            layer[i] = layerContents[i]
        return layer

    """
    getSizeOfLayer
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    def getSizeOfLayer(self, layerNum):
        dim = self.__layerDimensions[layerNum]
        if len(dim) == 3:
            return dim[0] * dim[1] * dim[2]
        elif len(dim) == 1:
            return dim[0]
        elif len(dim) == 0:
            return 0

        # ---------------------------------------------------------------------------------------------------------------------
