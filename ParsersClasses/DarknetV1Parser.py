import numpy
import sys
from SupportClasses import Rectangle
import os
import re
import glob, struct
from ObjectDetectionParser import ObjectDetectionParser
from SupportClasses import GoldContent
from SupportClasses import PrecisionAndRecall
from SupportClasses.CNNLayerParser import CNNLayerParser

from operator import add

MAX_NUM_OF_OBJECTS = 200


class DarknetV1Parser(ObjectDetectionParser):
    __executionType = None
    __executionModel = None

    __weights = None
    __configFile = None
    _extendedHeader = False

    __errorTypes = ['allLayers', 'filtered2', 'filtered5', 'filtered50']
    __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']

    _classes = ["aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
                "car", "cat", "chair", "cow", "diningtable", "dog", "horse",
                "motorbike", "person", "pottedplant", "sheep", "sofa", "train",
                "tvmonitor"]

    _smallestError = None
    _biggestError = None
    _numErrors = None
    _errorsAverage = None
    _errorsStdDeviation = None
    _numMaskableErrors = None
    _numCorrectableErrors = None

    __layerDimensions = {
        0: [224, 224, 64],
        1: [112, 112, 64],
        2: [112, 112, 192],
        3: [56, 56, 192],
        4: [56, 56, 128],
        5: [56, 56, 256],
        6: [56, 56, 256],
        7: [56, 56, 512],
        8: [28, 28, 512],
        9: [28, 28, 256],
        10: [28, 28, 512],
        11: [28, 28, 256],
        12: [28, 28, 512],
        13: [28, 28, 256],
        14: [28, 28, 512],
        15: [28, 28, 256],
        16: [28, 28, 512],
        17: [28, 28, 512],
        18: [28, 28, 1024],
        19: [14, 14, 1024],
        20: [14, 14, 512],
        21: [14, 14, 1024],
        22: [14, 14, 512],
        23: [14, 14, 1024],
        24: [14, 14, 1024],
        25: [7, 7, 1024],
        26: [7, 7, 1024],
        27: [7, 7, 1024],
        28: [7, 7, 256],
        29: [12544],
        30: [1175],
        31: [1175]}

    _sizeOfDnn = len(__layerDimensions)
    _failedLayer = -1
    _smartPoolingSize = 4
    _smartPooling = [0] * _smartPoolingSize

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "precision",
                  "recall", "false_negative", "false_positive", "true_positive", "abft_type", "failed_layer", "header"]

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""

    _cnnParser = None

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        # I write by default
        self._csvHeader[len(self._csvHeader) - 1: 1] = ["row_detected_errors", "collum_detected_error"]
        self._csvHeader[len(self._csvHeader) - 1: 1] = ["smart_pooling_" + str(i) for i in
                                                        xrange(1, self._smartPoolingSize + 1)]

        try:
            if self._parseLayers:
                self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
                self.__layersPath = str(kwargs.pop("layersPath"))
                self._cnnParser = CNNLayerParser(layersDimention=self.__layerDimensions,
                                                 layerGoldPath=self.__layersGoldPath,
                                                 layerPath=self.__layersPath, dnnSize=self._sizeOfDnn,
                                                 correctableLayers=[],
                                                 maxPoolLayers=[0, 2, 7, 18])

                self._csvHeader.extend(self._cnnParser.genCsvHeader())

        except:
            print "\n Crash on create parse layers parameters"
            sys.exit(-1)

    def _placeOutputOnList(self):
        # ["logFileName", "Machine", "Benchmark", "imgFile", "SDC_Iteration",
        #     "#Accumulated_Errors", "#Iteration_Errors", "gold_lines",
        #     "detected_lines", "x_center_of_mass", "y_center_of_mass",
        #     "precision", "recall", "false_negative", "false_positive",
        #     "true_positive", "abft_type", "row_detected_errors",
        #     "col_detected_errors", "failed_layer", "header"]
        self._outputListError = [self._logFileName,
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
                                 self._failedLayer]

        self._outputListError.extend([self._rowDetErrors, self._colDetErrors])
        self._outputListError.extend(self._smartPooling)

        self._outputListError.append(self._header)

        if self._parseLayers and self._saveLayer:
            self._outputListError.extend(self._cnnParser.getOutputToCsv())

    def setSize(self, header):
        # HEADER gold_file: /home/carol/radiation-benchmarks/data/darknet/darknet_v1_gold.urban.street.1.1K.csv save_layer: 0 abft_type: none iterations: 10000
        darknetM = re.match(".*gold_file\: (\S+).*save_layer\: (\d+).*abft_type\: (\S+).*iterations\: (\d+).*", header)

        if darknetM:
            self._goldFileName = darknetM.group(1)
            self._saveLayer = True if int(darknetM.group(2)) == 1 else False
            self._abftType = darknetM.group(3)
            self._iterations = darknetM.group(4)

        # return self.__imgListFile
        # tempPath = os.path.basename(self.__imgListPath).replace(".txt","")
        self._size = "gold_file_" + os.path.basename(self._goldFileName) + "_save_layer_" + str(
            self._saveLayer) + "_abft_" + str(self._abftType)

    def _relativeErrorParser(self, errList):
        if len(errList) == 0:
            return
        gold = self._loadGold()

        if gold == None:
            return

        # for layers parser
        self._imgListSize = gold.getPlistSize()
        # ---------------------------------------------------------------------------------------------------------------
        # img path
        # this is possible since errList has at least 1 element, due verification
        try:
            imgFilename = errList[0]["img"]
        except:
            # if only detection took place
            imgIt = int(self._sdcIteration) % int(self._imgListSize)
            imgFilename = gold.getImgsLocationList()[imgIt]

        goldPb = gold.getProbArray(imgPath=imgFilename)
        goldRt = gold.getRectArray(imgPath=imgFilename)

        foundPb = numpy.empty_like(goldPb)
        foundPb[:] = goldPb

        foundRt = numpy.empty_like(goldRt)
        foundRt[:] = goldRt

        self._detectionThreshold = gold.getThresh()

        # errors detected on smart pooling
        self._smartPooling = [0] * self._smartPoolingSize
        self._rowDetErrors = 0
        self._colDetErrors = 0

        for y in errList:
            if y["type"] == "err":
                err = y["rect"]
                # NEED TO BE CHECK
                i_prob_e = err["prob_e_i"]
                class_e = err["class_e_j"]

                i_prob_r = err["prob_r_i"]
                class_r = err["class_r_j"]

                lr = err["x_r"]
                br = err["y_r"]
                hr = err["h_r"]
                wr = err["w_r"]
                # gold correct
                le = err["x_e"]
                be = err["y_e"]
                he = err["h_e"]
                we = err["w_e"]
                foundRt[i_prob_r] = Rectangle.Rectangle(lr, br, wr, hr)
                # t = goldRt[rectPos].deepcopy()
                goldRt[i_prob_e] = Rectangle.Rectangle(le, be, we, he)

                foundPb[i_prob_r][class_r] = err["prob_r"]
                goldPb[i_prob_e][class_e] = err["prob_e"]


            elif y["type"] == "abft":
                # for i_prob_e in xrange(1, self._smartPoolingSize):
                #     self._smartPooling[i_prob_e] += err[i_prob_e]
                self._smartPooling = map(add, self._smartPooling, y["abft_det"])

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
        # print "\nGold ---- ", gValidRects, "\nFound ----- ", fValidRects
        gValidSize = len(gValidRects)
        fValidSize = len(fValidRects)
        if gValidSize > MAX_NUM_OF_OBJECTS:
            print "\nFuck, it's here"
            return

        precisionRecallObj.precisionAndRecallParallel(gValidRects, fValidRects)
        self._precision = precisionRecallObj.getPrecision()
        self._recall = precisionRecallObj.getRecall()

        # tic = time.clock()
        if self._parseLayers and self._saveLayer:
            """
             sdcIteration = which iteration SDC appeared
             logFilename = the name of the log file
             imgListSize = size of images dataset
             machine = testing device
             loadLayerMethod = an external method which open an specific layer on an external class
            """
            self._imgListPath = gold.getImgListPath()
            self._cnnParser.parseLayers(sdcIteration=self._sdcIteration,
                                        logFilename=self._logFileName,
                                        machine=self._machine,
                                        loadLayer=self.loadLayer)
            # print "\nTime spent on parsing layers", time.clock() - tic

        if self._imgOutputDir and (self._precision != 1 or self._recall != 1):
            drawImgFileName = self._localRadiationBench + imgFilename.split("/radiation-benchmarks")[1]
            gValidRectsDraw = [
                Rectangle.Rectangle(left=int(i.left), bottom=int(i.top), width=int(i.width), height=int(i.height),
                                    right=int(i.right), top=int(i.bottom)) for i in gValidRects]

            fValidRectsDraw = [
                Rectangle.Rectangle(left=int(i.left), bottom=int(i.top), width=int(i.width), height=int(i.height),
                                    right=int(i.right), top=int(i.bottom)) for i in fValidRects]

            self.buildImageMethod(drawImgFileName, gValidRectsDraw, fValidRectsDraw, str(self._sdcIteration)
                                  + '_' + self._logFileName, self._imgOutputDir)

        self._falseNegative = precisionRecallObj.getFalseNegative()
        self._falsePositive = precisionRecallObj.getFalsePositive()
        self._truePositive = precisionRecallObj.getTruePositive()
        # set all
        self._goldLines = gValidSize
        self._detectedLines = fValidSize
        self._wrongElements = abs(gValidSize - fValidSize)

    def _loadGold(self):
        # ---------------------------------------------------------------------------------------------------------------
        # open and load gold
        pureMachine = self._machine.split('-ECC')[0]
        goldKey = pureMachine + "_" + self._benchmark + "_" + self._size
        if pureMachine in self._goldBaseDir:
            goldPath = self._goldBaseDir[pureMachine] + "/darknet_v1/" + os.path.basename(self._goldFileName)
        else:
            print 'not indexed machine: ', pureMachine, " set it on Parameters.py"
            return None
        if goldKey not in self._goldDatasetArray:
            g = GoldContent.GoldContent(nn='darknetv1', filepath=goldPath)
            self._goldDatasetArray[goldKey] = g
        gold = self._goldDatasetArray[goldKey]
        return gold

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
            # print box
            # print w, h

            left = (bX - box.width / 2.) * w
            right = (bX + box.width / 2.) * w
            top = (bY + box.height / 2.) * h
            bot = (bY - box.height / 2.) * h

            width = box.width * w
            height = box.height * h

            if width > w - 1:
                width = w - 1

            if height > h - 1:
                height = h - 1

            if left < 0:
                left = 0

            if right > w - 1:
                right = w - 1

            if top < 0:
                top = 0

            if bot > h - 1:
                bot = h - 1

            for j in range(0, classes):
                if probabilites[i][j] > self._detectionThreshold:
                    validProbs.append(probabilites[i][j])
                    rect = Rectangle.Rectangle(left=int(left), bottom=int(bot), width=int(width), height=int(height),
                                               right=int(right), top=int(top))
                    validRectangles.append(rect)
                    validClasses.append(self._classes[j])

        return validRectangles, validProbs, validClasses

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        # parse errString for darknet
        ret = {}
        if 'ERR' in errString:
            dictRect = self.__processRect(errString)
            if dictRect:
                ret["rect"], ret['img'] = dictRect
                ret["type"] = "rect"
        elif 'INF' in errString:
            dictAbft = self.__processAbft(errString)
            if dictAbft:
                ret["abft_det"] = dictAbft
                ret["type"] = "abft"

        return ret if len(ret) > 0 else None

    # parse Darknet
    # returns a dictionary
    def __processRect(self, errString):
        ret = {}
        # ERR img: [/home/carol/radiation-benchmarks/data/URBAN_STREET/sequence01/images_right/cam2-20080702-162456-298.jpg]
        # prob_r[184][0]: 0.0000000000000000e+00 prob_e[184][0]: 0.0000000000000000e+00 x_r: 7.3684209585189819e-01 x_e: 7.0744901895523071e-01
        # y_r: 4.4771245121955872e-01 y_e: 4.9482199549674988e-01
        # w_r: inf w_e: 2.7612999081611633e-02 h_r: inf h_e: 9.3471996486186981e-02
        darknetM = re.match(
            ".*img\: \[(\S+)\].*prob_r\[(\d+)\]\[(\d+)\]\: (\S+).*prob_e\[(\d+)\]\[(\d+)\]\: "
            "(\S+).*x_r\: (\S+).*x_e\: (\S+).*y_r\: (\S+).*y_e\: (\S+).*w_r\: "
            "(\S+).*w_e\: (\S+).*h_r\: (\S+).*h_e\: (\S+).*",
            errString)

        if darknetM:
            i = 1
            img = str(darknetM.group(i))
            i += 1
            # ERR img: [0] prob[60][0] r:0.0000000000000000e+00 e:0.0000000000000000e+00
            ret["prob_r_i"] = int(darknetM.group(i))
            i += 1
            ret["class_r_j"] = int(darknetM.group(i))
            i += 1

            try:
                ret["prob_r"] = float(darknetM.group(i))
            except:
                ret["prob_r"] = 1e10

            i += 1

            ret["prob_e_i"] = int(darknetM.group(i))
            i += 1
            ret["class_e_j"] = int(darknetM.group(i))
            i += 1

            try:
                ret["prob_e"] = float(darknetM.group(i))
            except:
                ret["prob_e"] = 1e10

            i += 1

            # x_r: 1.7303885519504547e-01 x_e: 3.3303898572921753e-01
            try:
                ret["x_r"] = float(darknetM.group(i))
            except:
                ret["x_r"] = 1e10
            i += 1

            try:
                ret["x_e"] = float(darknetM.group(i))
            except:
                ret["x_e"] = 1e10
            i += 1

            # y_r: 1.0350487381219864e-01 y_e: 1.0350500047206879e-01
            try:
                ret["y_r"] = float(darknetM.group(i))
            except:
                ret["y_r"] = 1e10
            i += 1

            try:
                ret["y_e"] = float(darknetM.group(i))
            except:
                ret["y_e"] = 1e10
            i += 1

            # w_r: 2.0466668531298637e-02 w_e: 2.0467000082135201e-02
            try:
                ret["w_r"] = float(darknetM.group(i))
            except:
                ret["w_r"] = 1e10
            i += 1

            try:
                ret["w_e"] = float(darknetM.group(i))
            except:
                ret["w_e"] = 1e10
            i += 1

            # h_r: 4.1410662233829498e-02 h_e: 4.1411001235246658e-02
            try:
                ret["h_r"] = float(darknetM.group(i))
            except:
                ret["h_r"] = 1e10
            i += 1

            try:
                ret["h_e"] = float(darknetM.group(i))
            except:
                ret["h_e"] = 1e10
            i += 1

            return ret, img

        return None

    def __processAbft(self, errString):
        # #INF error_detected[0]: 0 error_detected[1]: 13588 error_detected[2]: 8650 error_detected[3]: 141366
        m = re.match(
            ".*error_detected\[(\d+)\]\: (\d+).*error_detected\[(\d+)\]\: (\d+).*error_detected\[(\d+)\]\: "
            "(\d+).*error_detected\[(\d+)\]\: (\d+).*",
            errString)
        ret = [0] * self._smartPoolingSize
        if m:
            ret[int(m.group(1))] = int(m.group(2))
            ret[int(m.group(3))] = int(m.group(4))
            ret[int(m.group(5))] = int(m.group(6))
            ret[int(m.group(7))] = int(m.group(8))

        return ret

    # ---------------------------------------------------------------------------------------------------------------------
    """
    loadLayer
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    # carrega de um log para uma matriz
    def loadLayer(self, layerNum, isGold=False):
        # it is better to programing one function only than two almost equal
        imgListpos = int(self._sdcIteration) % self._imgListSize
        # correcting the sdc iteration iteration
        correctIt = int(int(self._sdcIteration) / self._imgListSize)

        if isGold:
            # carrega de um log para uma matriz
            # goldIteration = str(int(self._sdcIteration) % self._imgListSize)
            # /media/fernando/U/data_K40/data/voc.2012.10.txt_darknet_v2_gold_layer_7_img_7_test_it_0.layer
            layerFilename = self.__layersGoldPath + "/" + os.path.basename(
                self._imgListPath) + "_darknet_v1_gold_layer_" + str(layerNum) + "_img_" + str(
                imgListpos) + "_test_it_0.layer"
        else:
            # 2017_09_10_10_00_29_cudaDarknetV1_ECC_OFF_carol-k401.log_darknet_v1_layer_3_img_4_test_it_95.layer
            layerFilename = self.__layersPath + "/" + self._logFileName + "_darknet_v1_layer_" + str(
                layerNum) + "_img_" + str(
                imgListpos) + "_test_it_" + str(correctIt) + ".layer"

        # print "\nLayerPath", layerFilename
        filenames = glob.glob(layerFilename)
        if len(filenames) == 0:
            print "\n", layerFilename, self._sdcIteration
            return None
        elif len(filenames) > 1:
            print('+de 1 layer encontrada para \'' + layerFilename + '\'')

        filename = filenames[0]
        layerSize = self.getSizeOfLayer(layerNum)

        layerFile = open(filename, "rb")
        numItens = layerSize  # float size = 4bytes

        try:
            layerContents = struct.unpack('f' * numItens, layerFile.read(4 * numItens))
        except:
            layerFile.close()
            return None
        
        layer = None
        # botar em matriz 3D
        if len(self.__layerDimensions[layerNum]) == 3:
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
