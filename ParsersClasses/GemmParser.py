import re

from Parser import Parser


class GemmParser(Parser):

    def parseErrMethod(self, errString):
        try:
            # ERR stream: 0, p: [0, 0], r: 3.0815771484375000e+02, e: 0.0000000000000000e+00
            if 'nan' in errString:
                m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\:.*nan.*e\: ([0-9e\+\-\.]+)", errString)
                if m:
                    posX = int(m.group(1))
                    posY = int(m.group(2))
                    read = float('nan')
                    expected = float(m.group(3))
                    return [posX, posY, read, expected]
                else:
                    return None
            else:
                m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\: ([0-9e\+\-\.]+).*e\: ([0-9e\+\-\.]+)", errString)
                if m:
                    posX = int(m.group(1))
                    posY = int(m.group(2))
                    read = float(m.group(3))
                    expected = float(m.group(4))
                    return [posX, posY, read, expected]
                else:
                    return None

        except ValueError:
            return None

    def setSize(self, header):
        size = None
        m = re.match(".*size\:(\d+).*", header)
        if m:
            try:
               size = int(m.group(1))
            except:
               size = None

        self._size = str(size)

