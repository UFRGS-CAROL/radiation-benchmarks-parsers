import sys
from ObjectDetectionParser import ObjectDetectionParser, ImageRaw
import re
import csv
import glob, struct
import os
import numpy

from SupportClasses import PrecisionAndRecall
from SupportClasses import _GoldContent


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

        self._sizeOfDNN = 32
        # self._allProperties = [self._smallestError, self._biggestError, self._numErrors, self._errorsAverage,
        #                        self._errorsStdDeviation, self._numMaskableErrors]

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
        # layerHeaderName :: layer<layerNum><infoName>_<filterName>
        # <infoName> :: 'smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsVariance'
        # <filterName> :: 'allErrors', 'newErrors', 'propagatedErrors'
        layerHeaderName = 'layer' + str(layerNum) + infoName + '_' + filterName
        return layerHeaderName

    def _writeToCSV(self, csvFileName):
        self._writeCSVHeader(csvFileName)

        try:
            csvWFP = open(csvFileName, "a")
            writer = csv.writer(csvWFP, delimiter=';')
            # ["logFileName", "Machine", "Benchmark", "imgFile", "SDC_Iteration",
            #     "#Accumulated_Errors", "#Iteration_Errors", "gold_lines",
            #     "detected_lines", "x_center_of_mass", "y_center_of_mass",
            #     "precision", "recall", "false_negative", "false_positive",
            #     "true_positive", "abft_type", "row_detected_errors",
            #     "col_detected_errors", "failed_layer", "header"]
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
            # raise

    def setSize(self, header):
        if "abft" in header:
            darknetM = re.match(
                ".*execution_type\:(\S+).*execution_model\:(\S+).*img_list_path\:"
                "(\S+).*weights\:(\S+).*config_file\:(\S+).*iterations\:(\d+).*abft: (\S+).*",
                header)
        else:
            darknetM = re.match(
                ".*execution_type\:(\S+).*execution_model\:(\S+).*img_list_path\:"
                "(\S+).*weights\:(\S+).*config_file\:(\S+).*iterations\:(\d+).*",
                header)

        if darknetM:
            try:
                self.__executionType = darknetM.group(1)
                self.__executionModel = darknetM.group(2)
                self._imgListPath = darknetM.group(3)
                self.__weights = darknetM.group(4)
                self.__configFile = darknetM.group(5)
                self._iterations = darknetM.group(6)
                if "abft" in header:
                    self._abftType = darknetM.group(7)

                self._goldFileName = self._datasets[os.path.basename(self._imgListPath)][self._abftType]

            except:
                self._imgListPath = None

        # return self.__imgListFile
        # tempPath = os.path.basename(self.__imgListPath).replace(".txt","")
        self._size = str(self._goldFileName)

    def getSizeOfLayer(self, layerNum):
        # retorna o numero de valores de uma layer
        dim = self.__layerDimentions[layerNum]
        layerSize = 0
        if (layerNum < 29):
            layerSize = dim[0] * dim[1] * dim[2]
        else:
            layerSize = dim[0]
        return layerSize

    def tupleToArray(self, layerContents, layerNum):
        size = self.__layerDimentions[layerNum][0]
        layer = [0 for i in xrange(0, size)]
        for i in range(0, size):
            layer[i] = layerContents[i]
        return layer

    def tupleTo3DMatrix(self, layerContents, layerNum):
        dim = self.__layerDimentions[layerNum]  # width,height,depth
        layer = [[[0 for k in xrange(dim[2])] for j in xrange(dim[1])] for i in xrange(dim[0])]
        for i in range(0, dim[0]):
            for j in range(0, dim[1]):
                for k in range(0, dim[2]):
                    contentsIndex = (i * dim[1] + j) * dim[2] + k
                    layer[i][j][k] = layerContents[contentsIndex]
        return layer

    def printLayersSizes(self):
        layerSize = [0 for k in xrange(32)]
        for i in range(0, 32):
            contentsLen = 0
            for filename in glob.glob(self.__layersPath + '*_' + str(i)):
                if (layerSize[i] == 0):
                    layerSize[i] = self.getSizeOfLayer(filename)

                layerFile = open(filename, "rb")
                numItens = layerSize[i] / 4  # float size = 4bytes
                layerContents = struct.unpack('f' * numItens, layerFile.read(4 * numItens))

                # print(filename + " :")
                # layerSize[i] = len(layerContents)
                # print("len: " + str(layerSize[i]))
                # for item in layerContents:
                # print(str(type(item)))
                layerFile.close()
                contentsLen = len(layerContents)
            print("layer " + str(i) + " size=" + str(layerSize[i]) + " contentSize=" + str(contentsLen))

    def getRelativeError(self, expected, read):
        absoluteError = abs(expected - read)
        relativeError = abs(absoluteError / expected) * 100
        return relativeError

    def get1DLayerErrorList(self, layerArray, goldArray, size):
        # sem filtered2 e etc
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorList :: [layerError]
        layerErrorList = []
        for i in range(0, size):
            if (layerArray[i] != goldArray[i]):
                relativeError = self.getRelativeError(goldArray[i], layerArray[i])
                layerError = [i, -1, -1, layerArray[i], goldArray[i]]
                layerErrorList.append(layerError)

        return layerErrorList

    def get1DLayerErrorLists(self, layerArray, goldArray, size):
        # funcao otimizada (com filtered2 e etc)
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors], [filtered50LayerErrors]}
        layerErrorLists = {errorTypeString: [] for errorTypeString in self.__errorTypes}
        for i in range(0, size):
            if (layerArray[i] != goldArray[i]):
                relativeError = self.getRelativeError(goldArray[i], layerArray[i])
                layerError = [i, -1, -1, layerArray[i], goldArray[i]]
                layerErrorLists['allLayers'].append(layerError)
                if (relativeError > 2):
                    layerErrorLists['filtered2'].append(layerError)
                if (relativeError > 5):
                    layerErrorLists['filtered5'].append(layerError)
                if (relativeError > 50):
                    layerErrorLists['filtered50'].append(layerError)

        return layerErrorLists

    def get3DLayerErrorList(self, layer, gold, width, height, depth):
        # sem filtered2 e etc
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        layerErrorList = []
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    if (layer[i][j][k] != gold[i][j][k]):
                        relativeError = self.getRelativeError(gold[i][j][k], layer[i][j][k])
                        layerError = [i, j, k, layer[i][j][k], gold[i][j][k]]
                        layerErrorList.append(layerError)

        return layerErrorList

    def get3DLayerErrorLists(self, layer, gold, width, height, depth):
        # funcao otimizada (com filtered2 e etc)
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorLists :: {[allLayerErrors], [filtered2LayerErrors], [filtered5LayerErrors], [filtered50LayerErrors]}
        layerErrorLists = {errorTypeString: [] for errorTypeString in self.__errorTypes}
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    if (layer[i][j][k] != gold[i][j][k]):
                        relativeError = self.getRelativeError(gold[i][j][k], layer[i][j][k])
                        layerError = [i, j, k, layer[i][j][k], gold[i][j][k]]
                        layerErrorLists['allLayers'].append(layerError)
                        if (relativeError > 2):
                            layerErrorLists['filtered2'].append(layerError)
                        if (relativeError > 5):
                            layerErrorLists['filtered5'].append(layerError)
                        if (relativeError > 50):
                            layerErrorLists['filtered50'].append(layerError)
        return layerErrorLists

    def getLayerDimentions(self, layerNum):
        width = 0
        height = 0
        depth = 0
        isArray = False
        if (len(self.__layerDimentions[layerNum]) == 3):
            width = self.__layerDimentions[layerNum][0]
            height = self.__layerDimentions[layerNum][1]
            depth = self.__layerDimentions[layerNum][2]
        elif (len(self.__layerDimentions[layerNum]) == 1):
            # as camadas 29, 30 e 31 sao apenas arrays
            width = self.__layerDimentions[layerNum][0]
            isArray = True
        else:
            print("erro: dicionario ta bugado")

        return isArray, width, height, depth

    def loadLayer(self, layerNum):
        # carrega de um log para uma matriz
        # print('_logFileName: ' + self._logFileName[])
        # print('_sdcIteration: ' + self._sdcIteration)
        sdcIteration = self._sdcIteration
        if self._isFaultInjection:
            sdcIteration = str(int(sdcIteration) + 1)
            # print 'debug' + sdcIteration
        layerFilename = self.__layersPath + self._logFileName + "_it_" + sdcIteration + "_layer_" + str(layerNum)
        # layerFilename = self.__layersPath  + '2017_03_15_04_15_52_cudaDarknet_carolk402.log_it_0_layer_' + str(layerNum)
        # layerFilename = self.__layersGoldPath + '2017_02_22_09_08_51_cudaDarknet_carol-k402.log_it_64_layer_' + str(layerNum)
        # print self.__layersPath   + layerFilename
        filenames = glob.glob(layerFilename)
        # print '_logFilename: ' + self._logFileName
        # print str(filenames)
        if (len(filenames) == 0):
            return None
        elif (len(filenames) > 1):
            print('+de 1 log encontrado para \'' + layerFilename + '\'')

        filename = filenames[0]
        layerSize = self.getSizeOfLayer(layerNum)

        layerFile = open(filename, "rb")
        numItens = layerSize  # float size = 4bytes

        layerContents = struct.unpack('f' * numItens, layerFile.read(4 * numItens))
        # botar em matriz 3D
        if (layerNum < 29):
            layer = self.tupleTo3DMatrix(layerContents, layerNum)
        else:
            layer = self.tupleToArray(layerContents, layerNum)
        layerFile.close()
        # print("load layer " + str(layerNum) + " size = " + str(layerSize) + " filename: " + filename + " len(layer) = " + str(len(layer)))
        return layer

    def getDatasetName(self):
        if self._goldFileName == 'gold.caltech.1K.test' or self._goldFileName == 'gold.caltech.abft.1K.test':
            return '_caltech1K'
        elif self._goldFileName == 'gold.voc.2012.1K.test' or self._goldFileName == 'gold.voc.2012.abft.1K.test':
            return '_voc2012'
        elif self._goldFileName == 'gold.caltech.critical.1K.test' or self._goldFileName == 'gold.caltech.critical.abft.1K.test':
            return '_caltechCritical'
        else:
            print 'erro getDatasetName: ' + self._goldFileName + ' nao classificado'
            return ''

    def loadGoldLayer(self, layerNum):
        # carrega de um log para uma matriz
        datasetName = self.getDatasetName()
        goldIteration = str(int(self._sdcIteration) % self._imgListSize)
        # print 'dataset? ' + self._goldFileName + '  it ' + self._sdcIteration + '  abft: ' + self._abftType
        layerFilename = self.__layersGoldPath + "gold_" + self._machine + datasetName + '_it_' + goldIteration + '_layer_' + str(
            layerNum)
        # layerFilename = self.__layersGoldPath + '2017_02_22_09_08_51_cudaDarknet_carol-k402.log_it_64_layer_' + str(layerNum)
        # print layerFilename
        filenames = glob.glob(layerFilename)
        # print str(filenames)
        if (len(filenames) == 0):
            return None
        elif (len(filenames) > 1):
            print('+de 1 gold encontrado para \'' + layerFilename + str(layerNum) + '\'')

        layerSize = self.getSizeOfLayer(layerNum)

        layerFile = open(filenames[0], "rb")
        numItens = layerSize  # float size = 4bytes

        layerContents = struct.unpack('f' * numItens, layerFile.read(4 * numItens))

        # botar em matriz 3D
        if (layerNum < 29):
            layer = self.tupleTo3DMatrix(layerContents, layerNum)
        else:
            layer = self.tupleToArray(layerContents, layerNum)
        layerFile.close()
        # print("load layer " + str(layerNum) + " size = " + str(layerSize) + " filename: " + filename + " len(layer) = " + str(len(layer)))
        return layer

    def _localityParser1D(self, layerErrorList):
        # errorType :: cubic, square, colOrRow, single, random
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors]}
        if len(layerErrorList) < 1:
            return [0, 0, 0, 0, 0]
        elif len(layerErrorList) == 1:
            return [0, 0, 0, 1, 0]
        else:
            errorInSequence = False
            lastErrorPos = -2
            for layerError in layerErrorList:
                if (layerError[0] == lastErrorPos + 1):
                    errorInSequence = True
                lastErrorPos = layerError[0]
            if errorInSequence:
                return [0, 0, 1, 0, 0]
            else:
                return [0, 0, 0, 0, 1]

    def getLayerErrorList(self, layer, gold, layerNum):
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorLists :: [layerError]
        isArray, width, height, depth = self.getLayerDimentions(layerNum)
        errorList = []
        if (isArray):
            errorList = self.get1DLayerErrorList(layer, gold, width)
        else:
            errorList = self.get3DLayerErrorList(layer, gold, width, height, depth)
        return errorList

    def printErrorType(self, errorType):
        if (errorType[0] == 1):
            print("cubic error")
        elif (errorType[1] == 1):
            print("square error")
        elif (errorType[2] == 1):
            print("column or row error")
        elif (errorType[3] == 1):
            print("single error")
        elif (errorType[4] == 1):
            print("random error")
        else:
            print("no errors")

    def jaccard_similarity(self, x, y):

        intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
        union_cardinality = len(set.union(*[set(x), set(y)]))
        return intersection_cardinality / float(union_cardinality)

    def layer3DToArray(self, layer, layerNum):
        width, height, depth = self.__layerDimentions[layerNum]
        layerSize = self.getSizeOfLayer(layerNum)
        layerArray = [0 for k in xrange(layerSize)]
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    arrayIndex = (i * height + j) * depth + k
                    layerArray[arrayIndex] = layer[i][j][k]
        return layerArray

    def getErrorListInfos(self, layerErrorList):
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        smallest = 0.0
        biggest = 0.0
        average = 0.0
        stdDeviation = 0.0
        maxpoolAbftThreshold = 110
        numMaskableErrors = 0
        # totalSum = long(0)
        relativeErrorsList = []
        for layerError in layerErrorList:
            # print('\nlayer error: ' + str(layerError))
            if (abs(layerError[3]) > maxpoolAbftThreshold):
                numMaskableErrors += 1
            relativeError = self.getRelativeError(layerError[4], layerError[3])
            # if(relativeError>1000000000):#debug
            # print('big relative error, value: ' + str(layerError[3]))
            # print('numMaskableErrors: ' + str(numMaskableErrors))
            relativeErrorsList.append(relativeError)
            # print('\nlayer error: ' + str(layerError))
            # print('relative error: ' + str(relativeError))
            # totalSum = totalSum + relativeError
            average += relativeError / len(layerErrorList)

            if (smallest == 0.0 and biggest == 0.0):
                smallest = relativeError
                biggest = relativeError
            else:
                if (relativeError < smallest):
                    smallest = relativeError
                if (relativeError > biggest):
                    biggest = relativeError
        # print('\ndebug totalSum: ' + str(totalSum))
        # average = totalSum/len(layerErrorList)
        # average = numpy.average(relativeErrorsList)
        if (average != 0.0):
            stdDeviation = numpy.std(relativeErrorsList)

        return smallest, biggest, average, stdDeviation, numMaskableErrors

    def parseLayers(self):
        ### faz o parsing de todas as camadas de uma iteracao
        # errorType :: [cubic, square, colOrRow, single, random]
        # layerError :: xPos, yPos, zPos, found(?), expected(?)
        # layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors]}
        # print ('\n' + self._logFileName + ' :: ' + self._goldFileName + ' :: ' + self._imgListPath)
        # kernelTime = int(self._accIteErrors) // int(self._sdcIteration)
        # print '\nkerneltime: ' + str(kernelTime)

        self._smallestError = {filterName: [0.0 for i in xrange(32)] for filterName in self.__filterNames}
        self._biggestError = {filterName: [0.0 for i in xrange(32)] for filterName in self.__filterNames}
        self._numErrors = {filterName: [0 for i in xrange(32)] for filterName in self.__filterNames}
        self._errorsAverage = {filterName: [0.0 for i in xrange(32)] for filterName in self.__filterNames}
        self._errorsStdDeviation = {filterName: [0.0 for i in xrange(32)] for filterName in self.__filterNames}
        self._numMaskableErrors = [0 for i in xrange(32)]
        self._failed_layer = ""
        logsNotFound = False
        goldsNotFound = False
        self._errorFound = False
        self.errorTypeList = [[] for i in range(0, 32)]

        for i in range(0, 32):
            # print '\n----layer ' + str(i) + ' :'
            layer = self.loadLayer(i)
            gold = self.loadGoldLayer(i)
            if (layer is None):
                print(self._machine + ' it: ' + str(self._sdcIteration) + ' layer ' + str(i) + ' log not found')
                logsNotFound = True
                break
            elif (gold is None):
                print('gold ' + str(i) + ' log not found')
                goldsNotFound = True
                break
            else:
                layerErrorList = self.getLayerErrorList(layer, gold, i)
                if (len(layerErrorList) > 0):
                    self._numErrors['allErrors'][i] = len(layerErrorList)
                smallest, biggest, average, stdDeviation, numMaskableErrors = self.getErrorListInfos(layerErrorList)
                self._smallestError['allErrors'][i] = smallest
                self._biggestError['allErrors'][i] = biggest
                self._errorsAverage['allErrors'][i] = average
                self._errorsStdDeviation['allErrors'][i] = stdDeviation
                self._numMaskableErrors[i] = numMaskableErrors
                # print('\n numMaskableErrors: ' + str(numMaskableErrors) + ' :: ' + str(self._numMaskableErrors[i]))
                if (self._errorFound):
                    # ja tinha erros em alguma camada anterior
                    self._numErrors['propagatedErrors'][i] = self._numErrors['allErrors'][i]
                    self._smallestError['propagatedErrors'][i] = self._smallestError['allErrors'][i]
                    self._biggestError['propagatedErrors'][i] = self._biggestError['allErrors'][i]
                    self._errorsAverage['propagatedErrors'][i] = self._errorsAverage['allErrors'][i]
                    self._errorsStdDeviation['propagatedErrors'][i] = self._errorsStdDeviation['allErrors'][i]
                else:
                    self._numErrors['newErrors'][i] = self._numErrors['allErrors'][i]
                    self._smallestError['newErrors'][i] = self._smallestError['allErrors'][i]
                    self._biggestError['newErrors'][i] = self._biggestError['allErrors'][i]
                    self._errorsAverage['newErrors'][i] = self._errorsAverage['allErrors'][i]
                    self._errorsStdDeviation['newErrors'][i] = self._errorsStdDeviation['allErrors'][i]
                if (False):  # i == 31):
                    print('\nlogName : ' + self._logFileName)
                    print('numErrors camada ' + str(i) + ' :: ' + str(len(layerErrorList)))
                    print('smallestError camada ' + str(i) + ' :: ' + str(smallest))
                    print('biggestError camada ' + str(i) + ' :: ' + str(biggest))
                    print('errorsAverage camada ' + str(i) + ' :: ' + str(average))
                    print('errorsStdDeviation camada ' + str(i) + ' :: ' + str(stdDeviation))
                    print('ja deu erro? ' + str(self._errorFound))
                    print('Precision: ' + str(self._precision) + '  Recall: ' + str(self._recall) + '\n')
                if (i < 29):
                    # layer 3D
                    self.errorTypeList[i] = self._localityParser3D(layerErrorList)
                    if (self.errorTypeList[i] != [0, 0, 0, 0, 0]):
                        # aconteceu algum tipo de erro
                        if (not self._errorFound):
                            self._failed_layer = str(i)
                            self._errorFound = True
                            # layerArray = self.layer3DToArray(layer, i)
                            # goldArray = self.layer3DToArray(gold, i)
                            # jaccardCoef = self.jaccard_similarity(layerArray,goldArray)
                    else:
                        # nao teve nenhum erro
                        jaccardCoef = 1
                else:
                    # layer 1D
                    self.errorTypeList[i] = self._localityParser1D(layerErrorList)
                    if (self.errorTypeList[i] != [0, 0, 0, 0, 0]):
                        # aconteceu algum tipo de erro
                        if (not self._errorFound):
                            self._failed_layer = str(i)
                            self._errorFound = True
                            # jaccardCoef = self.jaccard_similarity(layer,gold)
                    else:
                        # nao teve nenhum erro
                        jaccardCoef = 1
                        # print('jaccard = ' + str(jaccardCoef))

                        # print('\n numMaskableErrors: ' + str(self._numMaskableErrors))
        if logsNotFound and goldsNotFound:
            self._failed_layer += 'golds and logs not found'
        elif logsNotFound:
            self._failed_layer += 'logs not found'
        elif goldsNotFound:
            self._failed_layer += 'golds not found'
        # print('failed_layer: ' + self._failed_layer + '\n')
        pass


    def _relativeErrorParser(self, errList):
        if len(errList) <= 0:
            return

        # goldKey = self._machine + "_" + self._benchmark + "_" + self._goldFileName
        #
        # if self._machine in self._goldBaseDir:
        #     goldPath = self._goldBaseDir[self._machine] + "/darknet/" + self._goldFileName
        # else:
        #     print 'not indexed machine: ', self._machine, " set it on Parameters.py"
        #     return
        #
        # if goldKey not in self._goldDatasetArray:
        #     g = _GoldContent._GoldContent(nn='darknet', filepath=goldPath)
        #     self._goldDatasetArray[goldKey] = g
        #
        # gold = self._goldDatasetArray[goldKey]
        # imgFilename = ''
        # imgObj = ImageRaw(imgFilename)
        #
        # gValidRects = []
        # fValidRects = []
        # for i in errList:
        #     pass
        #
        #
        # precisionRecallObj = PrecisionAndRecall.PrecisionAndRecall(self._prThreshold)
        # gValidSize = len(gValidRects)
        # fValidSize = len(fValidRects)
        #
        # precisionRecallObj.precisionAndRecallParallel(gValidRects, fValidRects)
        # self._precision = precisionRecallObj.getPrecision()
        # self._recall = precisionRecallObj.getRecall()
        #
        # if self._parseLayers:  # and self.hasLayerLogs(self._sdcIteration):
        #     # print self._sdcIteration + 'debug'
        #     self.parseLayers()
        #     # print self._machine + self._abftType
        #
        # if self._imgOutputDir and (self._precision != 1 or self._recall != 1):
        #     self.buildImageMethod(imgFilename.rstrip(), gValidRects, fValidRects, str(self._sdcIteration)
        #                           + '_' + self._logFileName, self._imgOutputDir)
        #
        # self._falseNegative = precisionRecallObj.getFalseNegative()
        # self._falsePositive = precisionRecallObj.getFalsePositive()
        # self._truePositive = precisionRecallObj.getTruePositive()
        # # set all
        # self._goldLines = gValidSize
        # self._detectedLines = fValidSize
        # self._xCenterOfMass, self._yCenterOfMass = precisionRecallObj.centerOfMassGoldVsFound(gValidRects, fValidRects,
        #                                                                                       imgObj.w, imgObj.h)


    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        # parse errString for darknet
        ret = {}
        imgListPosition = ""


        return ret if len(ret) > 0 else None





