import struct

from ObjectDetectionParser import ObjectDetectionParser
import re
import csv



# 0 to 9 digits
MAX_LENET_ELEMENT = 9.0


class ResnetParser(ObjectDetectionParser):


    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)
        self._parseLayers = bool(kwargs.pop("parseLayers"))

        self._sizeOfDNN = 200
