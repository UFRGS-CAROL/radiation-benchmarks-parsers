import re
import sys
from ParsersClasses import Parser


class LavaMDParser(Parser.Parser):
    _box = None
    _blockSize = None
    _streams = None
    _hasThirdDimention = True

    _csvHeader = ["logFileName", "Machine", "Benchmark", "Header", "SDC Iteration", "#Accumulated Errors",
                  "#Iteration Errors", "Max Relative Error", "Min Rel Error",
                  "Average Rel Err", "detectedErrors"]

    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
                                 self._machine,
                                 self._benchmark,
                                 self._header,
                                 self._sdcIteration,
                                 self._accIteErrors,
                                 self._iteErrors,
                                 self._maxRelErr,
                                 self._minRelErr,
                                 self._avgRelErr,
                                 self._detectedErrors]

    def _jaccardCoefficient(self, errListJaccard):
        pass

    def parseErrMethod(self, errString):
        if self._box is None:
            print ("box is None!!!\nerrString: ", errString)
            print("header: ", self._header)
            sys.exit(1)

        pattern = ".*detected_dmr_errors: (\d+).*"
        try:
            m = re.match(pattern, errString)
            return int(m.group(1))
        except AttributeError:
            pass

        try:
            # ERR p: [357361], ea: 4, v_r: 1.5453305664062500e+03, v_e: 1.5455440673828125e+03,
            # x_r: 9.4729260253906250e+02, x_e: 9.4630560302734375e+02, y_r: -8.0158099365234375e+02,
            # y_e: -8.0218914794921875e+02, z_r: 9.8227819824218750e+02, z_e: 9.8161871337890625e+02
            m = re.match(
                ".*ERR.*\[(\d+)\].*v_r\: ([0-9e\+\-\.]+).*v_e\: ([0-9e\+\-\.]+).*x_r\: ([0-9e\+\-\.]+).*"
                "x_e\: ([0-9e\+\-\.]+).*y_r\: ([0-9e\+\-\.]+).*y_e\: ([0-9e\+\-\.]+).*z_r\: ([0-9e\+\-\.]+).*"
                "z_e\: ([0-9e\+\-\.]+)",
                errString)
            if m:
                pos = int(m.group(1))
                boxSquare = self._box * self._box
                posZ = int(pos / boxSquare)
                posY = int((pos - (posZ * boxSquare)) / self._box)
                posX = pos - (posZ * boxSquare) - (posY * self._box)

                vr = float(m.group(2))
                ve = float(m.group(3))
                xr = float(m.group(4))
                xe = float(m.group(5))
                yr = float(m.group(6))
                ye = float(m.group(7))
                zr = float(m.group(8))
                ze = float(m.group(9))
                result = [posX, posY, posZ, vr, ve, xr, xe, yr, ye, zr, ze]

                dmrPattern = ".*s_v_r: (\S+), s_x_r: (\S+), s_y_r: (\S+), s_z_r: (\S+).*"
                m = re.match(dmrPattern, errString)
                if m:
                    result.extend([float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))])
                return result
            else:
                return None
        except ValueError:
            return None

    def setSize(self, header):
        # old versions of lava
        m = re.match(".*size\:(\d+).*", header)
        if m:
            try:
                self._size = int(m.group(1))
            except:
                self._size = None

        self._box = None
        m = re.match(".*boxes[\:-](\d+).*", header)
        if m:
            try:
                self._box = int(m.group(1))
            except:
                self._box = None

        m = re.match(".*box[\:-](\d+).*", header)
        if m:
            try:
                self._box = int(m.group(1))
            except:
                self._box = None

        # new versions of lava
        # HEADER streams: 1 boxes:6 block_size:192
        m = re.match(".*streams\: (\d+).*boxes\:(\d+).*block_size\:(\d+).*", header)
        if m:
            self._streams = int(m.group(1))
            self._box = int(m.group(2))
            self._blockSize = int(m.group(3))

        if self._blockSize and self._streams:
            self._size = "streams_" + str(self._streams) + "_boxes_" + str(self._box) + "_block_size_" + str(
                self._blockSize)
        else:
            self._size = "old_lava_boxes_" + str(self._box)

        m = re.match(".*type:(\S+) streams.*redundancy:(\S+) check_block:(\d+).*", header)
        if m:
            self._size += "type_{}_dmr_{}_check_block_{}".format(m.group(1), m.group(2), m.group(3))

    def buildImageMethod(self):
        return False

    def _relativeErrorParser(self, errList):
        self._detectedErrors = 0
        self._countErrors = len(errList)
        self._maxRelErr = -2222
        self._minRelErr = 33333
        self._avgRelErr = 0

        for err in errList:
            if type(err) == list:
                for i in range(3, 11, 2):
                    if err[i] is None or err[i + 1] is None:
                        continue
                    read = float(err[i])
                    expected = float(err[i + 1])
                    absoluteErr = abs(expected - read)
                    relError = abs(absoluteErr / expected) * 100

                    # error average calculation
                    self._maxRelErr = max(relError, self._maxRelErr)
                    self._minRelErr = min(relError, self._maxRelErr)
                    self._avgRelErr = relError / float(self._countErrors * 4)
            elif type(err) == int:
                self._detectedErrors = err

    def localityParser(self):
        pass
