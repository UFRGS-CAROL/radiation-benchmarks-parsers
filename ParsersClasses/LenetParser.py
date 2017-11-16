import os
import struct
from Parser import Parser
import re
import csv
from SupportClasses.CNNLayerParser import CNNLayerParser

# 0 to 9 digits
MAX_LENET_ELEMENT = 9.0


class LenetParser(Parser):
    __executionType = None
    __executionModel = None

    __weights = None
    __configFile = None
    _extendedHeader = False

    # __errorTypes = ['allLayers', 'filtered2', 'filtered5', 'filtered50']
    # __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    # __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']

    # _numMaskableErrors = [0 for i in xrange(32)]

    _smallestError = None
    _biggestError = None
    _numErrors = None
    _errorsAverage = None
    _errorsStdDeviation = None
    _numMaskableErrors = None

    _failed_layer = -1
    _errorTypeList = None
    _abftType = 'none'

    # these vars will turn writetocsv easier to implement
    _sizeOfDNN = 0

    # for CNNLayer Parser
    _cnnParser = None

    __layerDimensions = {
        0: [28, 28, 6],
        1: [14, 14, 6],
        2: [10, 10, 16],
        3: [5, 5, 16],
        4: [100, 1, 1]
    }

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "relative_error", "abft_type",
                  "failed_layer", "header"]

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""

    def __init__(self, **kwargs):
        # ObjectDetectionParser.__init__(self, **kwargs)
        Parser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        self._sizeOfDNN = len(self.__layerDimensions)
        if self._parseLayers:
            self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
            self.__layersPath = str(kwargs.pop("layersPath"))
            self._cnnParser = CNNLayerParser(layersDimention=self.__layerDimensions,
                                             layerGoldPath=self.__layersGoldPath,
                                             layerPath=self.__layersPath, dnnSize=self._sizeOfDNN, correctableLayers=[])

            self._csvHeader.extend(self._cnnParser.genCsvHeader())

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
                          self._minRelErr,
                          self._abftType,
                          self._failed_layer,
                          self._header]

            if (self._parseLayers):
                outputList.extend(self._cnnParser.getOutputToCsv())

            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName

    def setSize(self, header):
        #  gold_file: /home/carol/radiation-benchmarks/data/lenet/gold_t10k_images.test weights:
        # /home/carol/radiation-benchmarks/data/lenet/lenet_base.weights iterations: 1000
        lenetM = re.match(".*gold_file\: (\S+).*weights\: (\S+).*iterations\: (\d+).*", header)
        if lenetM:
            self._goldFile = str(lenetM.group(1))
            self.__weights = str(lenetM.group(2))
            self._iterations = str(lenetM.group(3))
            if 'L2' in self.__weights.upper():
                self._abftType = 'L2'
            elif 'L1' in self.__weights.upper():
                self._abftType = 'L1'
            else:
                self._abftType = 'none'
            self._size = os.path.basename(self._goldFile) + "_" + os.path.basename(self.__weights)

        else:
            self._size = ""
            self.__weights = ""
            self._iterations = ""
            self._abftType = ""

    def parseErrMethod(self, errString):
        if len(errString) == 0:
            return

        ret = {}
        # img: [6] expected_first: [3] read_first: [4] expected_second: [1] read_second: [1]
        errM = re.match(
            ".*img\: \[(\d+)\].*expected_first\: \[(\d+)\].*read_first\: \[(\d+)\].*expected_second\: \[(\d+)\].*read_second\: \[(\d+)\].*",
            errString)

        if errM:
            ret["img"] = errM.group(1)
            ret["expected_first"] = errM.group(2)
            ret["read_first"] = errM.group(3)
            ret["expected_second"] = errM.group(4)
            ret["read_second"] = errM.group(5)

            try:
                ret["img"] = int(ret["img"])
            except:
                ret["img"] = -1

            try:
                ret["expected_first"] = int(ret["expected_first"])
            except:
                ret["expected_first"] = 1e10

            try:
                ret["read_first"] = int(ret["read_first"])
            except:
                ret["read_first"] = 1e10

            try:
                ret["expected_second"] = int(ret["expected_second"])
            except:
                ret["expected_second"] = 1e10

            try:
                ret["read_second"] = int(ret["read_second"])
            except:
                ret["read_second"] = 1e10

            return ret

        return None

    def _relativeErrorParser(self, errList):
        errListLen = len(errList)
        if errListLen == 0:
            return

        if errListLen != 1:
            raise

        read = errList[0]["read_first"]
        gold = errList[0]["expected_first"]

        self._minRelErr = abs(gold - read) / MAX_LENET_ELEMENT

        if self._parseLayers:
            self._img = errList[0]["img"]
            """
             sdcIteration = which iteration SDC appeared
             logFilename = the name of the log file
             imgListSize = size of images dataset
             machine = testing device
             loadLayerMethod = an external method which open an specific layer on an external class
            """
            self._cnnParser.parseLayers(sdcIteration=self._sdcIteration,
                                        logFilename=self._logFileName,
                                        imgListSize=1,
                                        machine=self._machine,
                                        loadLayerMethod=self.loadLayer)



    """

    """

    def loadLayer(self, layerNum, isGold=False):
        imgListpos = self._img
        realIteration = imgListpos - int(self._sdcIteration)
        layerFilename = self.__layersPath + "/" + self._logFileName + "_it_" + str(realIteration) + "_img_" + str(
            imgListpos) + "_layer_" + str(layerNum) + ".layer"

        if isGold:
            layerFilename = self.__layersPath + "/gold_layer_lenet_img_" + str(
                imgListpos) + "_layer_" + str(layerNum) + ".layer"

        layerFile = open(layerFilename, "rb")
        layerDim = struct.unpack('I', layerFile.read(4))[0]

        dim = self.__layerDimensions[layerNum]

        assert layerDim == (dim[0] * dim[1] * dim[2])

        layerContents = struct.unpack('f' * layerDim, layerFile.read(4 * layerDim))

        layer = None
        if len(self.__layerDimensions[layerNum]) == 3:
            layer = self.tupleTo3DMatrix(layerContents, dim)

        layerFile.close()

        return layer

    """
    tupleTo3DMatrix
    THIS function WILL only be used inside CNNLayerParser class
    DO NOT USE THIS OUTSIDE
    """

    def tupleTo3DMatrix(self, layerContents, dim):
        layer = [[[0] * (dim[2] + 1)] * (dim[1] + 1)] * (dim[0] + 1)
        for i in range(0, dim[0]):
            for j in range(0, dim[1]):
                for k in range(0, dim[2]):
                    contentsIndex = (i * dim[1] + j) * dim[2] + k
                    layer[i][j][k] = layerContents[contentsIndex]

        return layer

    def buildImageMethod(self, *args): return False


    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass
