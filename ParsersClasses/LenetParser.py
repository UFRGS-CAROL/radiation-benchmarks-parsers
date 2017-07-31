import struct

from ObjectDetectionParser import ObjectDetectionParser
import re
import csv


from SupportClasses.CNNLayerParser import CNNLayerParser

# 0 to 9 digits
MAX_LENET_ELEMENT = 9.0

class LenetParser(ObjectDetectionParser):
    __executionType = None
    __executionModel = None

    __weights = None
    __configFile = None
    _extendedHeader = False

    __errorTypes = ['allLayers', 'filtered2', 'filtered5', 'filtered50']
    __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']

    # _numMaskableErrors = [0 for i in xrange(32)]

    _smallestError = None
    _biggestError = None
    _numErrors = None
    _errorsAverage = None
    _errorsStdDeviation = None
    _numMaskableErrors = None

    _failed_layer = None
    _errorTypeList = None

    # these vars will turn writetocsv easier to implement
    _sizeOfDNN = 0

    # for CNNLayer Parser
    _cnnParser = None

    __layerDimensions = {
        0: [32, 32, 1],
        1: [28, 28, 6],
        2: [14, 14, 6],
        3: [10, 10, 16],
        4: [5, 5, 16],
        5: [100, 10, 1],
    }

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "precision",
                  "recall", "abft_type", "row_detected_errors",
                  "col_detected_errors", "failed_layer", "header"]

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
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
                          self._goldLines,
                          self._precision,
                          self._recall,
                          self._abftType,
                          self._rowDetErrors,
                          self._colDetErrors,
                          self._failed_layer,
                          self._header]

            if (self._parseLayers):
                outputList.extend(self._cnnParser.getOutputToCsv())

            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName

    def setSize(self, header):
        # gold_file: gold_test weights: ./lenet.weights iterations: 10
        lenetM = re.match("gold_file\: (\S+).*weights\: (\S+).*iterations\: (\d+).*", header)
        if lenetM:
            self._size = str(lenetM.group(1))
            self.__weights = str(lenetM.group(2))
            self._iterations = str(lenetM.group(3))
        else:
            self._size = ""
            self.__weights = ""
            self._iterations = ""

    # parse Darknet
    # returns a dictionary
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

        self._precision = abs(gold - read) / MAX_LENET_ELEMENT

        if read == gold:
            self._recall = 1.0
        else:
            self._recall = 0.0

        self._goldLines = 1
        self._abftType = "not_implemented"
        self._rowDetErrors = 0
        self._colDetErrors = 0


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
                                        imgListSize=1,
                                        machine=self._machine,
                                        loadLayerMethod=self.loadLayer)
    """
    this->in_width_ = this->load_layer_var<size_t>(in);
    this->in_height_ = this->load_layer_var<size_t>(in);
    this->in_depth_ = this->load_layer_var<size_t>(in);
    this->out_width_ = this->load_layer_var<size_t>(in);
    this->out_height_ = this->load_layer_var<size_t>(in);
    this->out_depth_ = this->load_layer_var<size_t>(in);
    this->alpha_ = this->load_layer_var<float_t>(in);
    this->lambda_ = this->load_layer_var<float_t>(in);
    this->err = this->load_layer_var<float_t>(in);
    this->exp_y = this->load_layer_var<int>(in);

    //vector attributes
    this->W_ = this->load_layer_vec<float_t>(in);
    this->b_ = this->load_layer_vec<float_t>(in);
    this->deltaW_ = this->load_layer_vec<float_t>(in);
    this->input_ = this->load_layer_vec<float_t>(in);
    this->output_ = this->load_layer_vec<float_t>(in);
    this->g_ = this->load_layer_vec<float_t>(in);
    this->exp_y_vec = this->load_layer_vec<float_t>(in);
    """
    def _loadBaseLayer(self, file):
        # 6 ints + 3 floats + 1 int
        varsSeekSize = 24 + 12 + 4
        file.read(varsSeekSize)

        # W_, b_, deltaW_, input_
        for i in xrange(0, 4):
            # first read w_ size, which is an int
            size = struct.unpack('i', file.read(4))[0]
            # because it's a vector of floats
            file.read(size * 4)

        # this is the data
        outputSize = struct.unpack('i', file.read(4))[0]
        outputData = struct.unpack('f' * outputSize, file.read(4 * outputSize))
        return outputSize, outputData



    def loadLayer(self, layerNum, isGold=False):
        if isGold:
            goldFilePath = self.__layersGoldPath + "/gold_layers_lenet.layer"

            goldFile = open(goldFilePath, "rb")
            
            for i in xrange(0, self._sizeOfDNN):
                # conv layer
                if i == layerNum:
                    if i in [0, 2, 4]:
                        self._loadBaseLayer(goldFile)
                        # this->kernel_size_ = this->load_layer_var<size_t>(in);
                        goldFile.read(4)
                    # maxpooling
                    elif i in [1, 3]:
                        self._loadBaseLayer(goldFile)
                        # this->max_loc = this->load_layer_vec<Pair>(in);
                        sizeMaxLoc =  struct.unpack('i', goldFile.read(4))[0]
                        # * 2 because it is Pair vector
                        goldFile.read(sizeMaxLoc * 2)

                    # fully connected
                    elif i == 5:
                        pass

        else:
            pass

        return None