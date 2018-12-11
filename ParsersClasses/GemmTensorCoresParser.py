import re

from Parser import Parser


class GemTensorCoresParser(Parser):

    def parseErrMethod(self, errString):
        try:
            # ERR stream: 0, p: [0, 0], r: 3.0815771484375000e+02, e: 0.0000000000000000e+00
            m = re.match(".*p\: \[(\d+), (\d+)\].*r\: (\S+),.*e\: (\S+).*", errString)
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
        # iterations: 10 precision: half matrix_n_dim: 8192 triplicated: 0
        m = re.match(".*iterations: (\d+).*precision: (\S+) matrix_n_dim: (\S+) triplicated: (\d+).*", header)
        iterations = precision = size = triplicated = None
        if m:
            iterations = int(m.group(1))
            precision = m.group(2)
            size = int(m.group(3))
            triplicated = int(m.group(4))

        self._size = "iterations_{}_precision_{}_size_{}_triplicated_{}".format(iterations, precision, size,
                                                                                triplicated)
