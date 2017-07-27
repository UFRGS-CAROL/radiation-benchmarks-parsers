

"""
This class will be used
for parsing layers in CNN logs
"""
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
    _errorTypeList = None
    _sizeOfDNN = 0
    _allProperties = None

    __errorTypes = ['allLayers', 'filtered2', 'filtered5', 'filtered50']
    __infoNames = ['smallestError', 'biggestError', 'numErrors', 'errorsAverage', 'errorsStdDeviation']
    __filterNames = ['allErrors', 'newErrors', 'propagatedErrors']


    """
    Constructor
    layersDimention : A dict that will have for each layer its 3D dimentions, like this
    0: [224, 224, 64],  1: [112, 112, 64],   2: [112, 112, 192], ....
    layerGoldPath : Path for gold layers
    layerPath :  Path to detection layers
    externalMethodGenerateGoldLayerName : Generate gold layer name from outside
    externalMethodGenerateLayerName     : Generate layer name from outside
    """
    def __init__(self, *args, **kwargs):
        self.__layerDimentions = kwargs.pop("layersDimention")
        self.__layersGoldPath = kwargs.pop("layerGoldPath")
        self.__layersPath = kwargs.pop("layerPath")


    def genCsvHeader(self, layersGoldPath, layersPath):
        self.__layersGoldPath = str(layersGoldPath)
        self.__layersPath = str(layersPath)

        csvHeader = []
        csvHeader.extend(self._getLayerHeaderName(layerNum, infoName, filterName)
                               for filterName in self.__filterNames
                               for infoName in self.__infoNames
                               for layerNum in xrange(32))
        csvHeader.extend(self._getLayerHeaderNameErrorType(layerNum)
                               for layerNum in xrange(32))
        csvHeader.extend(self._getMaskableHeaderName(layerNum)
                               for layerNum in xrange(32))
        csvHeader.extend(self._getNumCorrectableErrorsHeaderName(layerNum)
                               for layerNum in [0, 2, 7, 18])

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

    """
    This method receives an external method and its parameters to open
    the layer files
    """
    def _openLayers(self, externalMethod, parameter1):
        raise NotImplemented


    def parserLayer(self):
        raise NotImplemented