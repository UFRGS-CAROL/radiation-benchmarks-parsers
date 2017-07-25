import sys
from ObjectDetectionParser import ObjectDetectionParser
import re
import csv
import os


class DarknetV2Parser(ObjectDetectionParser):
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
    _allProperties = None

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "precision",
                  "recall", "false_negative", "false_positive", "true_positive", "abft_type", "row_detected_errors",
                  "col_detected_errors", "failed_layer", "header"]

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        self._sizeOfDNN = 32

        try:
            if self._parseLayers:
                self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
                self.__layersPath = str(kwargs.pop("layersPath"))
                self._extendedHeader = True
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
            # raise

    def setSize(self, header):
        sizeM = re.match(".*gold_file\: (\S+).*", header)
        if sizeM:
            print sizeM.group(1)

        self._size = str(self._goldFileName)

    def _relativeErrorParser(self, errList):
        if len(errList) == 0:
            return

        print self._goldFileName
        for i in errList:
            pass

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        ret = {}
        darknetM = re.match(
            ".*img\: \[(\d+)\].*prob\[(\d+)\]\[(\d+)\].*r\:(\S+).*e\:(\S+).*x_r\: (\S+).*x_e\: "
            "(\S+).*y_r\: (\S+).*y_e\: (\S+).*w_r\: (\S+).*w_e\: (\S+).*h_r\: (\S+).*h_e\: (\S+).*",
            errString)

        if darknetM:
            ret["img"] = int(darknetM.group(1))
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
