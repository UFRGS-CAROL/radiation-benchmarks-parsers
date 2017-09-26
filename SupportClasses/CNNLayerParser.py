"""
This class will be used
for parsing layers in CNN logs
"""
import collections
import glob
import numpy
import struct

import time


class CNNLayerParser():
    __layerDimentions = {}
    __layersGoldPath = ""
    __layersPath = ""
    _smallestError = None
    _biggestError = None
    _numErrors = None
    _errorsAverage = None
    _errorsStdDeviation = None
    _numMaskableErrors = None
    _failed_layer = None
    _sdcIteration = None
    _logFileName = None

    _machine = None

    _sizeOfDNN = 0
    _allProperties = None

    __threeLevelFiltered = [2, 5, 50]
    __errorTypes = ['allLayers'] + ['filtered' + str(i) for i in __threeLevelFiltered]

    __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']

    _correctableLayers = None
    _numCorrectableErrors = None
    _errorTypeList = None

    # set to true if you want debug
    __debug = False

    """
    Constructor
    layersDimention : A dict that will have for each layer its 3D dimentions, like this
    0: [224, 224, 64],  1: [112, 112, 64],   2: [112, 112, 192], ....
    layerGoldPath : Path for gold layers
    layerPath :  Path to detection layers

    """

    def __init__(self, *args, **kwargs):
        self.__layerDimentions = kwargs.pop("layersDimention")
        self.__layersGoldPath = kwargs.pop("layerGoldPath")
        self.__layersPath = kwargs.pop("layerPath")

        self._sizeOfDNN = kwargs.pop("dnnSize")
        self._correctableLayers = kwargs.pop("correctableLayers")

    def genCsvHeader(self):
        csvHeader = []
        csvHeader.extend(self._getLayerHeaderName(layerNum, infoName, filterName)
                         for filterName in self.__filterNames
                         for infoName in self.__infoNames
                         for layerNum in xrange(self._sizeOfDNN))
        csvHeader.extend(self._getLayerHeaderNameErrorType(layerNum)
                         for layerNum in xrange(self._sizeOfDNN))
        csvHeader.extend(self._getMaskableHeaderName(layerNum)
                         for layerNum in xrange(self._sizeOfDNN))

        csvHeader.extend(self._getNumCorrectableErrorsHeaderName(layerNum)
                         for layerNum in self._correctableLayers)

        return csvHeader

    # layer<layerNum>MaskableErrorsNum
    def _getMaskableHeaderName(self, layerNum):
        maskableHeaderName = 'layer' + str(layerNum) + 'MaskableErrorsNum'
        return maskableHeaderName

    # layer<layerNum>ErrorType
    def _getLayerHeaderNameErrorType(self, layerNum):
        layerHeaderName = 'layer' + str(layerNum) + 'ErrorType'
        return layerHeaderName

    """
    layerHeaderName :: layer<layerNum><infoName>_<filterName>
    <infoName> :: 'smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsVariance'
    <filterName> :: 'allErrors', 'newErrors', 'propagatedErrors'
    """

    def _getLayerHeaderName(self, layerNum, infoName, filterName):
        layerHeaderName = 'layer' + str(layerNum) + infoName + '_' + filterName
        return layerHeaderName

    # layer<layerNum>CorrectableErrorsNum
    def _getNumCorrectableErrorsHeaderName(self, layerNum):
        correctableHeaderName = 'layer' + str(layerNum) + 'CorrectableErrorsNum'
        return correctableHeaderName


    def _errorTypeToString(self, errorType):
        if len(errorType) == 0:
            return "same"
        if errorType[0] == 1:
            return "cubic"
        elif errorType[1] == 1:
            return "rectangle"
        elif errorType[2] == 1:
            return "line"
        elif errorType[3] == 1:
            return "single"
        elif errorType[4] == 1:
            return "random"
        else:
            return "no errors"

    """
    This will be used to write in the final CSV result
    it return the result information produced on parser
    """

    def getOutputToCsv(self):
        outputList = []
        for filterName in self.__filterNames:
            outputList.extend([self._smallestError[filterName][i] for i in xrange(self._sizeOfDNN)])
            outputList.extend([self._biggestError[filterName][i] for i in xrange(self._sizeOfDNN)])
            outputList.extend([self._numErrors[filterName][i] for i in xrange(self._sizeOfDNN)])
            outputList.extend([self._errorsAverage[filterName][i] for i in xrange(self._sizeOfDNN)])
            outputList.extend([self._errorsStdDeviation[filterName][i] for i in xrange(self._sizeOfDNN)])

        outputList.extend(self._errorTypeToString(self._errorTypeList[i]) for i in xrange(self._sizeOfDNN))
        outputList.extend(self._numMaskableErrors[i] for i in xrange(self._sizeOfDNN))
        outputList.extend(self._numCorrectableErrors[i] for i in self._correctableLayers)

        return outputList

    """
    return the layer values num
    assumes that layers which have 1D will be declared as [layer_n:[n, 1, 1]]
    """

    def _getSizeOfLayer(self, layerNum):
        dim = self.__layerDimentions[layerNum]
        if len(dim) == 3:
            return dim[0] * dim[1] * dim[2]
        elif len(dim) == 1:
            return dim[0]
        elif len(dim) == 2:
            return dim[0] * dim[1]
        elif len(dim) == 0:
            return 0

    def _printLayersSizes(self):
        layerSize = [0 for k in xrange(self._sizeOfDNN)]
        for i in xrange(0, self._sizeOfDNN):
            contentsLen = 0
            for filename in glob.glob(self.__layersPath + '*_' + str(i)):
                if (layerSize[i] == 0):
                    layerSize[i] = self._getSizeOfLayer(filename)

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

    def _getRelativeError(self, expected, read):
        absoluteError = abs(expected - read)
        relativeError = abs(absoluteError / expected) * 100
        return relativeError

    """
    sem filtered2 e etc
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorList :: [layerError]
    """

    def _get1DLayerErrorList(self, layerArray, goldArray, size):
        layerErrorList = []
        for i in range(0, size):
            if (layerArray[i] != goldArray[i]):
                relativeError = self._getRelativeError(goldArray[i], layerArray[i])
                layerError = [i, -1, -1, layerArray[i], goldArray[i]]
                layerErrorList.append(layerError)

        return layerErrorList

    """
    funcao otimizada (com filtered2 e etc)
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors], [filtered50LayerErrors]}
    """

    def _get1DLayerErrorLists(self, layerArray, goldArray, size):
        layerErrorLists = {errorTypeString: [] for errorTypeString in self.__errorTypes}
        for i in range(0, size):
            if (layerArray[i] != goldArray[i]):
                relativeError = self._getRelativeError(goldArray[i], layerArray[i])
                layerError = [i, -1, -1, layerArray[i], goldArray[i]]
                layerErrorLists['allLayers'].append(layerError)

                # if relativeError > self.__threeLevelFiltered[0]:
                #     layerErrorLists['filtered2'].append(layerError)
                # if relativeError > self.__threeLevelFiltered[1]:
                #     layerErrorLists['filtered5'].append(layerError)
                # if relativeError > self.__threeLevelFiltered[2]:
                #     layerErrorLists['filtered50'].append(layerError)
                for trFiltered in self.__threeLevelFiltered:
                    if relativeError > trFiltered:
                        layerErrorLists['filtered' + str(trFiltered)].append(layerError)

        return layerErrorLists

    """
    sem filtered2 e etc
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    """

    def _get3DLayerErrorList(self, layer, gold, width, height, depth):
        layerErrorList = []
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    if (layer[i][j][k] != gold[i][j][k]):
                        # relativeError = self.getRelativeError(gold[i][j][k], layer[i][j][k])
                        layerError = [i, j, k, layer[i][j][k], gold[i][j][k]]
                        layerErrorList.append(layerError)

        return layerErrorList

    """
    funcao otimizada (com filtered2 e etc)
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorLists :: {[allLayerErrors], [filtered2LayerErrors], [filtered5LayerErrors], [filtered50LayerErrors]}
    """

    def _get3DLayerErrorLists(self, layer, gold, width, height, depth):
        layerErrorLists = {errorTypeString: [] for errorTypeString in self.__errorTypes}
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    if (layer[i][j][k] != gold[i][j][k]):
                        relativeError = self._getRelativeError(gold[i][j][k], layer[i][j][k])
                        layerError = [i, j, k, layer[i][j][k], gold[i][j][k]]
                        layerErrorLists['allLayers'].append(layerError)

                        for trFiltered in self.__threeLevelFiltered:
                            if relativeError > trFiltered:
                                layerErrorLists['filtered' + str(trFiltered)].append(layerError)
        return layerErrorLists

    def _getLayerDimentions(self, layerNum):
        width = 0
        height = 0
        depth = 0
        isArray = False
        if len(self.__layerDimentions[layerNum]) == 3:
            width = self.__layerDimentions[layerNum][0]
            height = self.__layerDimentions[layerNum][1]
            depth = self.__layerDimentions[layerNum][2]
        elif len(self.__layerDimentions[layerNum]) == 1:
            # some layers are only arrays
            width = self.__layerDimentions[layerNum][0]
            isArray = True

        elif len(self.__layerDimentions[layerNum]) != 0:
            raise NotImplementedError

        return isArray, width, height, depth

    """
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorLists :: [layerError]
    """

    def _getLayerErrorList(self, layer, gold, layerNum):
        isArray, width, height, depth = self._getLayerDimentions(layerNum)
        errorList = []
        if (isArray):
            errorList = self._get1DLayerErrorList(layer, gold, width)
        else:
            errorList = self._get3DLayerErrorList(layer, gold, width, height, depth)
        return errorList

    def _printErrorType(self, errorType):
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

    def _jaccard_similarity(self, x, y):
        intersection_cardinality = len(set.intersection(*[set(x), set(y)]))
        union_cardinality = len(set.union(*[set(x), set(y)]))
        return intersection_cardinality / float(union_cardinality)

    def _layer3DToArray(self, layer, layerNum):
        width, height, depth = self.__layerDimentions[layerNum]
        layerSize = self._getSizeOfLayer(layerNum)
        layerArray = [0] * layerSize
        for i in range(0, width):
            for j in range(0, height):
                for k in range(0, depth):
                    arrayIndex = (i * height + j) * depth + k
                    layerArray[arrayIndex] = layer[i][j][k]
        return layerArray

    """
    retorna True se existe erros vizinhos ao erro em questao
    retorna False caso contrario
    """

    def _existsErrorNeighbor(self, layerError, layerErrorList):
        for otherLayerError in layerErrorList:
            if (otherLayerError != layerError):
                # erros imediatamente ao lado, com msm zPos
                if (layerError[2] == otherLayerError[2]):
                    if (layerError[0] == otherLayerError[0]) \
                            or (layerError[0] == otherLayerError[0] + 1) \
                            or (layerError[0] == otherLayerError[0] - 1):
                        if (layerError[1] == otherLayerError[1]) \
                                or (layerError[1] == otherLayerError[1] + 1) \
                                or (layerError[1] == otherLayerError[1] - 1):
                            # print("DEBUG\nerror: " + str(layerError))
                            # print("otherError: " + str(otherLayerError))
                            return True
        # se nao achou nenhum vizinho ate aqui, eh pq nao tem nenhum
        return False

    """
    dada uma error list com todos os layerError tendo mesmo Z
    retorna o numero dos erros que sao corrigiveis
    """

    def _getGroupedNumCorrectableErrors(self, layerErrorList):
        numCorrectableErrors = 0
        for layerError in layerErrorList:
            if not self._existsErrorNeighbor(layerError, layerErrorList):
                numCorrectableErrors += 1

        ##DEBUG
        # print "\nDEBUG\nlayerErrorList:\n" + str(layerErrorList)
        # print "numCorrectableErrors: " + str(numCorrectableErrors)
        return numCorrectableErrors

    # retorna o numero de erros corrigiveis por smartpooling
    def _getNumCorrectableErrors(self, layerErrorList):
        tic = time.clock()
        sortedLayerErrorList = sorted(layerErrorList, key=lambda layerError: layerError[2])  # zPos
        numCorrectableErrors = 0
        print "Sort is spending ", time.clock() - tic , " vector size ", len(sortedLayerErrorList)
        # debug
        currentZ = -20  # iterador
        currentLayerErrorList = []
        tic = time.clock()
        for layerError in sortedLayerErrorList:
            if currentZ == -20:  # primeiro item da lista
                currentLayerErrorList.append(layerError)
                currentZ = layerError[2]
            elif currentZ > layerError[2]:
                print "\nERRO que nao era pra acontecer: getNumCorrectableErrors"
            elif currentZ == layerError[2]:
                currentLayerErrorList.append(layerError)
            elif currentZ < layerError[2]:
                numCorrectableErrors += self._getGroupedNumCorrectableErrors(currentLayerErrorList)
                currentZ = layerError[2]
                currentLayerErrorList = []
                currentLayerErrorList.append(layerError)
        numCorrectableErrors += self._getGroupedNumCorrectableErrors(currentLayerErrorList)
        print "other procedure is spending", time.clock() - tic
        return numCorrectableErrors

    # layerError :: xPos, yPos, zPos, found(?), expected(?)
    def _getErrorListInfos(self, layerErrorList, numLayer):
        smallest = 0.0
        biggest = 0.0
        average = 0.0
        stdDeviation = 0.0
        maxpoolAbftThreshold = 110
        numMaskableErrors = 0
        numCorrectableErrors = 0
        # totalSum = long(0)
        relativeErrorsList = numpy.empty_like(layerErrorList)
        errListSize = len(layerErrorList)

        for i in xrange(0, errListSize):
            layerError = layerErrorList[i]
            if abs(layerError[3]) > maxpoolAbftThreshold:
                numMaskableErrors += 1

            # cost only O(1)
            relativeError = self._getRelativeError(layerError[4], layerError[3])
            relativeErrorsList[i] = relativeError

            average += relativeError / errListSize

            if smallest == 0.0 and biggest == 0.0:
                smallest = relativeError
                biggest = relativeError
            else:
                if relativeError < smallest:
                    smallest = relativeError
                if relativeError > biggest:
                    biggest = relativeError

        if average != 0.0:
            stdDeviation = numpy.std(relativeErrorsList)

        # calculando numCorrectableErrors:
        # TODO: it will work only for darknetv1, must change in a generic way
        if numLayer in [0, 2, 7, 18] and layerErrorList != []:  # layers logo antes dos maxpooling
            tic = time.clock()
            numCorrectableErrors = self._getNumCorrectableErrors(layerErrorList)
            print "getNumCorrectableErrors time ", time.clock() - tic
        # print('debug numMaskableErrors: ' + str(numMaskableErrors))
        return smallest, biggest, average, stdDeviation, numMaskableErrors, numCorrectableErrors

    """
    Parser all layers on an i iteration
    Parameters:
     sdcIteration = which iteration SDC appeared
     logFilename = the name of the log file
     machine = testing device
     loadLayerMethod = an external method which open an specific layer on an external class

    generated information:
     errorType :: [cubic, square, colOrRow, single, random]
     layerError :: xPos, yPos, zPos, found(?), expected(?)
     layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors]}
    """

    def parseLayers(self, sdcIteration=None, logFilename=None, machine=None, loadLayer=None):
        self._sdcIteration = sdcIteration
        self._logFileName = logFilename
        self._machine = machine

        # default for most of all CNNs
        self._smallestError = {filterName: [0.0 for i in xrange(self._sizeOfDNN)] for filterName in self.__filterNames}
        self._biggestError = {filterName: [0.0 for i in xrange(self._sizeOfDNN)] for filterName in self.__filterNames}
        self._numErrors = {filterName: [0 for i in xrange(self._sizeOfDNN)] for filterName in self.__filterNames}
        self._errorsAverage = {filterName: [0.0 for i in xrange(self._sizeOfDNN)] for filterName in self.__filterNames}
        self._errorsStdDeviation = {filterName: [0.0 for i in xrange(self._sizeOfDNN)] for filterName in
                                    self.__filterNames}
        self._numMaskableErrors = [0 for i in xrange(self._sizeOfDNN)]
        self._numCorrectableErrors = [0 for i in xrange(self._sizeOfDNN)]
        self._failed_layer = ""
        logsNotFound = False
        goldsNotFound = False
        self._errorFound = False
        self._errorTypeList = [[] for i in range(0, self._sizeOfDNN)]

        for i in range(0, self._sizeOfDNN):
            print '\n----layer ' + str(i) + ' :'
            layer = loadLayer(i)
            gold = loadLayer(i, True)

            if layer is None and len(self.__layerDimentions[i]) != 0:
                # print "\n", self._machine + ' it: ' + str(self._sdcIteration) + ' layer ' + str(i) + ' log not found'
                logsNotFound = True
                continue
            elif gold is None and len(self.__layerDimentions[i]) != 0:
                print('gold ' + str(i) + ' log not found')
                goldsNotFound = True
                break
            else:
                print "getLayerErrorList"
                layerErrorList = self._getLayerErrorList(layer, gold, i)
                if len(layerErrorList) > 0:
                    self._numErrors['allErrors'][i] = len(layerErrorList)

                print "getErrorListInfos"
                smallest, biggest, average, stdDeviation, numMaskableErrors, numCorrectableErrors = self._getErrorListInfos(
                    layerErrorList, i)


                self._smallestError['allErrors'][i] = smallest
                self._biggestError['allErrors'][i] = biggest
                self._errorsAverage['allErrors'][i] = average
                self._errorsStdDeviation['allErrors'][i] = stdDeviation
                self._numMaskableErrors[i] = numMaskableErrors
                self._numCorrectableErrors[i] = numCorrectableErrors

                if i in self._correctableLayers:
                    print (
                        "\nDEBUG\ncamada: " + str(i) + "\nnumCorrectableErrors: " + str(
                            numCorrectableErrors) + " / " + str(
                            self._numErrors['allErrors'][i]))

                # print('\n numMaskableErrors: ' + str(numMaskableErrors) + ' :: ' + str(self._numMaskableErrors[i]))
                if self._errorFound:
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
                if self.__debug:
                    print('\nlogName : ' + self._logFileName)
                    print('numErrors camada ' + str(i) + ' :: ' + str(len(layerErrorList)))
                    print('smallestError camada ' + str(i) + ' :: ' + str(smallest))
                    print('biggestError camada ' + str(i) + ' :: ' + str(biggest))
                    print('errorsAverage camada ' + str(i) + ' :: ' + str(average))
                    print('errorsStdDeviation camada ' + str(i) + ' :: ' + str(stdDeviation))
                    print('ja deu erro? ' + str(self._errorFound))
                    # print('Precision: ' + str(self._precision) + '  Recall: ' + str(self._recall) + '\n')

                print "\nDebug, passou antes", i
                # check if it is a 3D Layer or it is a 1D one
                # parser locality error
                self.__localityParser(dim=len(self.__layerDimentions[i]), i=i, layerErrorList=layerErrorList)
                print "depois"

        if logsNotFound and goldsNotFound:
            self._failed_layer += 'golds and logs not found'
        elif logsNotFound:
            self._failed_layer += 'logs not found'
        elif goldsNotFound:
            self._failed_layer += 'golds not found'

    """
    generic locality parser
    dim = dimention of layer
    i = layer num
    layerErrorList = List of layer errors
    """
    def __localityParser(self, dim, i, layerErrorList):
        print "inside locality"
        # no size
        if dim == 0:
            print "Layer has no size "
        # 1D
        elif dim == 1:
            self._errorTypeList[i] = self._localityParser1D(layerErrorList)
        # 2D
        elif dim == 2:
            raise NotImplemented
        # 3D
        elif dim == 3:
            # layer 3D
            self._errorTypeList[i] = self._localityParser3D(layerErrorList)
        else:
            raise NotImplementedError

        if self._errorTypeList[i] != [0, 0, 0, 0, 0] and not self._errorFound:
        # aconteceu algum tipo de erro
            self._failed_layer = str(i)
            self._errorFound = True

    """
    errorType :: cubic, square, colOrRow, single, random
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors]}
    """
    def _localityParser3D(self, errList):
        if len(errList) < 1:
            return [0, 0, 0, 0, 0]
        elif len(errList) == 1:
            return [0, 0, 0, 1, 0]
        else:
            allXPositions = [x[0] for x in errList]  # Get all positions of X
            allYPositions = [x[1] for x in errList]  # Get all positions of Y
            allZPositions = [x[2] for x in errList]  # Get all positions of Y
            counterXPositions = collections.Counter(allXPositions)  # Count how many times each value is in the list
            counterYPositions = collections.Counter(allYPositions)  # Count how many times each value is in the list
            counterZPositions = collections.Counter(allZPositions)  # Count how many times each value is in the list
            rowError = any(
                x > 1 for x in counterXPositions.values())  # Check if any value is in the list more than one time
            colError = any(
                x > 1 for x in counterYPositions.values())  # Check if any value is in the list more than one time
            heightError = any(
                x > 1 for x in counterZPositions.values())  # Check if any value is in the list more than one time
            if rowError and colError and heightError:  # cubic error
                return [1, 0, 0, 0, 0]
            if (rowError and colError) or (rowError and heightError) or (heightError and colError):  # square error
                return [0, 1, 0, 0, 0]
            elif rowError or colError or heightError:  # line error
                return [0, 0, 1, 0, 0]
            else:  # random error
                return [0, 0, 0, 0, 1]

    """
    errorType :: cubic, square, colOrRow, single, random
    layerError :: xPos, yPos, zPos, found(?), expected(?)
    layerErrorLists :: {[allLlayerErrors], [filtered2LayerErrors], [filtered5LayerErrors]}
    """
    def _localityParser1D(self, layerErrorList):
        if len(layerErrorList) < 1:
            return [0, 0, 0, 0, 0]
        elif len(layerErrorList) == 1:
            return [0, 0, 0, 1, 0]
        else:
            errorInSequence = False
            lastErrorPos = -2
            for layerError in layerErrorList:
                if layerError[0] == lastErrorPos + 1:
                    errorInSequence = True
                lastErrorPos = layerError[0]
            if errorInSequence:
                return [0, 0, 1, 0, 0]
            else:
                return [0, 0, 0, 0, 1]