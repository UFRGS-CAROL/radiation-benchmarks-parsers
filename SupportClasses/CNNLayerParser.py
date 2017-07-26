

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




    """
    Constructor
    layersDimention : A dict that will have for each layer its 3D dimentions, like this
    0: [224, 224, 64],  1: [112, 112, 64],   2: [112, 112, 192], ....
    layerGoldPath : Path for gold layers
    layerPath :  Path to detection layers
    externalMethodGenerateGoldLayerName : Generate gold layer name from outside
    externalMethodGenerateLayerName     : Generate layer name from outside
    """
    def __init__(self, **kwargs):
        self.__layerDimentions = kwargs.pop("layersDimention")
        self.__layersGoldPath = kwargs.pop("layerGoldPath")
        self.__layersPath = kwargs.pop("layerPath")




    """
    This method receives an external method and its parameters to open
    the layer files
    """
    def _openLayers(self, externalMethod, parameter1):
        raise NotImplemented


    def parserLayer(self):
        raise NotImplemented