import sys
from ObjectDetectionParser import ObjectDetectionParser, ImageRaw
import re
import csv
import glob, struct
import os
import numpy

from SupportClasses import PrecisionAndRecall
from SupportClasses import _GoldContent


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
    _allProperties = None

    #change it for Lenet
    __layerDimentions = {
        0: [608, 608, 32],
        1: [304, 304, 32],
        2: [304, 304, 64],
        3: [152, 152, 64],
        4: [152, 152, 128],
        5: [152, 152, 64],
    }

    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "x_center_of_mass", "y_center_of_mass", "precision",
                  "recall", "false_negative", "false_positive", "true_positive", "abft_type", "row_detected_errors",
                  "col_detected_errors", "failed_layer", "header"]

    # it is only for darknet for a while
    _parseLayers = False
    __layersGoldPath = ""
    __layersPath = ""

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        self._sizeOfDNN = 5
        raise NotImplementedError

    def errorTypeToString(self, errorType):
        if (errorType[0] == 1):
            return "cubic"
        elif (errorType[1] == 1):
            return "square"
        elif (errorType[2] == 1):
            return "line"
        elif (errorType[3] == 1):
            return "single"
        elif (errorType[4] == 1):
            return "random"
        else:
            return "no errors"

    def getMaskableHeaderName(self, layerNum):
        # layer<layerNum>MaskableErrorsNum
        maskableHeaderName = 'layer' + str(layerNum) + 'MaskableErrorsNum'
        return maskableHeaderName

    def getLayerHeaderNameErrorType(self, layerNum):
        # layer<layerNum>ErrorType
        layerHeaderName = 'layer' + str(layerNum) + 'ErrorType'
        return layerHeaderName

    def getLayerHeaderName(self, layerNum, infoName, filterName):
        raise NotImplementedError

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
                          self._xCenterOfMass,
                          self._yCenterOfMass,
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
                # for i in xrange(32): #debug
                # print(str(self._numMaskableErrors[i]))
                for filterName in self.__filterNames:
                    outputList.extend([self._smallestError[filterName][i] for i in xrange(32)])
                    outputList.extend([self._biggestError[filterName][i] for i in xrange(32)])
                    outputList.extend([self._numErrors[filterName][i] for i in xrange(32)])
                    outputList.extend([self._errorsAverage[filterName][i] for i in xrange(32)])
                    outputList.extend([self._errorsStdDeviation[filterName][i] for i in xrange(32)])
                outputList.extend(self.errorTypeToString(self._errorTypeList[i]) for i in xrange(32))
                outputList.extend(self._numMaskableErrors[i] for i in xrange(32))

            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName


    def setSize(self, header):
        raise NotImplementedError

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        raise NotImplementedError



    def _relativeErrorParser(self, errList):
        raise NotImplementedError