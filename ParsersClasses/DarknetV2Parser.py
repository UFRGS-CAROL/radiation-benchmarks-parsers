import sys
from SupportClasses import Rectangle
import os
import re
import glob, struct
from ObjectDetectionParser import ObjectDetectionParser
from SupportClasses import _GoldContent
from ObjectDetectionParser import ImageRaw
from SupportClasses import PrecisionAndRecall


class DarknetParser(ObjectDetectionParser):
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

    __layerDimentions = {
        0: [608, 608, 32],
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
        25: [0, 0, 0],
        26: [38, 38, 64],
        27: [19, 19, 256],
        28: [0, 0, 0],
        29: [19, 19, 1024],
        30: [19, 19, 425],
        31: [0, 0, 0]
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

        try:
            if self._parseLayers:
                self.__layersGoldPath = str(kwargs.pop("layersGoldPath"))
                self.__layersPath = str(kwargs.pop("layersPath"))
                self._extendedHeader = True
                self._csvHeader.extend(self.getLayerHeaderName(layerNum, infoName, filterName)
                                       for filterName in self.__filterNames
                                       for infoName in self.__infoNames
                                       for layerNum in xrange(32))
                self._csvHeader.extend(self.getLayerHeaderNameErrorType(layerNum)
                                       for layerNum in xrange(32))
                self._csvHeader.extend(self.getMaskableHeaderName(layerNum)
                                       for layerNum in xrange(32))
        except:
            print "\n Crash on create parse layers parameters"
            sys.exit(-1)
