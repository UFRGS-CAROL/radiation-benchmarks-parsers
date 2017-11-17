
import re
from Parser import Parser

class GaussianParser(Parser):

    _dim = None
    def parseErrMethod(self, errString):
        m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\: ([0-9e\+\-\.]+).*e\: ([0-9e\+\-\.]+)", errString)
        if m:
            posX = int(m.group(1))
            posY = int(m.group(2))
            read = float(m.group(3))
            expected = float(m.group(4))
            return [posX, posY, read, expected]
        else:
            return None


    def setSize(self, header):
        # size:1024
        m = re.match(".*size\:(\d+).*", header)
        if m:
            self._dim = int(m.group(1))
        self._size = "size_" + str(self._dim)