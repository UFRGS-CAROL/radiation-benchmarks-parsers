import re
import struct
import sys

from Parser import Parser
from sklearn.metrics import jaccard_similarity_score


class LavaMDParser(Parser):
    _box = None
    _blockSize = None
    _streams = None
    _hasThirdDimention = True

    def _jaccardCoefficient(self, errListJaccard):
        # print "\n\nPassou no jaccard lava \n\n"
        expected = []
        read = []
        for err in errListJaccard:
            try:
                readGStr = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[2]))
                expectedGStr = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[3]))
                readGStr2 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[4]))
                expectedGStr2 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[5]))
                readGStr3 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[6]))
                expectedGStr3 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[7]))
                readGStr4 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[8]))
                expectedGStr4 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!f', err[9]))
            except OverflowError:
                readGStr = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[2]))
                expectedGStr = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[3]))
                readGStr2 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[4]))
                expectedGStr2 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[5]))
                readGStr3 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[6]))
                expectedGStr3 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[7]))
                readGStr4 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[8]))
                expectedGStr4 = ''.join(bin(ord(c)).replace('0b', '').rjust(8, '0') for c in struct.pack('!d', err[9]))

            read.extend([n for n in readGStr])
            read.extend([n for n in readGStr2])
            read.extend([n for n in readGStr3])
            read.extend([n for n in readGStr4])
            expected.extend([n for n in expectedGStr])
            expected.extend([n for n in expectedGStr2])
            expected.extend([n for n in expectedGStr3])
            expected.extend([n for n in expectedGStr4])

        try:
            jac = jaccard_similarity_score(expected, read)
            dissimilarity = float(1.0 - jac)
            return dissimilarity
        except:
            return None

    def parseErrMethod(self, errString):
        if self._box is None:
            print ("box is None!!!\nerrString: ", errString)
            print("header: ", self._header)
            sys.exit(1)
        try:
            ##ERR p: [357361], ea: 4, v_r: 1.5453305664062500e+03, v_e: 1.5455440673828125e+03, x_r: 9.4729260253906250e+02, x_e: 9.4630560302734375e+02, y_r: -8.0158099365234375e+02, y_e: -8.0218914794921875e+02, z_r: 9.8227819824218750e+02, z_e: 9.8161871337890625e+02
            m = re.match(
                ".*ERR.*\[(\d+)\].*v_r\: ([0-9e\+\-\.]+).*v_e\: ([0-9e\+\-\.]+).*x_r\: ([0-9e\+\-\.]+).*x_e\: ([0-9e\+\-\.]+).*y_r\: ([0-9e\+\-\.]+).*y_e\: ([0-9e\+\-\.]+).*z_r\: ([0-9e\+\-\.]+).*z_e\: ([0-9e\+\-\.]+)",
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
        super(LavaMDParser, self)._relativeErrorParser(errList)
        self._keys = ['detected_errors']
        for key in self._keys:
            self._outputListError.extend(self._locality[key])
