import numpy
import sys
from ObjectDetectionParser import ObjectDetectionParser
import re
import csv
import os

from SupportClasses import PrecisionAndRecall
from SupportClasses import Rectangle
from SupportClasses import _GoldContent


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

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""
    _failed_layer = ""

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        try:
            if self._parseLayers:
                self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
                self.__layersPath = str(kwargs.pop("layersPath"))

                raise NotImplementedError

        except:
            print "\n Crash on create parse layers parameters"
            sys.exit(-1)

    def _writeToCSV(self, csvFileName):
        self._writeCSVHeader(csvFileName)

        try:
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
                raise NotImplementedError

            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName
            raise

    def setSize(self, header):
        sizeM = re.match(".*gold_file\: (\S+).*", header)
        if sizeM:
            self._goldFileName = sizeM.group(1)

        self._size = os.path.basename(self._goldFileName)

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
            raise NotImplementedError

        if self._imgOutputDir and (self._precision != 1 or self._recall != 1):
            drawImgFileName =  self._localRadiationBench + "/data/CALTECH/" \
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
