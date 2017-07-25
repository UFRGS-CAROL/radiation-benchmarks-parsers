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
                raise  NotImplementedError

            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName
            # raise

    def setSize(self, header):
        print "passou"
        self._size = str(self._goldFileName)

    def _relativeErrorParser(self, errList):
        raise NotImplementedError


    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        print "passou"

        raise NotImplementedError