import re

from Parser import Parser


class CachesParser(Parser):
    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors",
                  "#Iteration_Errors", "zeroToOne", "oneToZero", "cacheLineErrors", "singleErrors",
                  "multipleErros", "smsCorrupted", "header"]

    __cacheLineSize = 128  # size in bytes
    __wordSize = 32 / 8  # word size in bytes

    def parseErrMethod(self, errString):
        reg_or_cache = "cache_line"
        if "register" in errString:
            reg_or_cache = "register"

        # ERR  i:1589618 cache_line:12418 e:255 r:253 hits: 30720 false_hit: 0
        pattern = ".*ERR.*i\:(\d+).*" + reg_or_cache + "\:(\d+).*e\:(\d+).*r\:(\d+).*hits\: (\d+).*false_hit\: (\d+).*"
        m = re.match(pattern, errString)

        ret = None
        if m:
            ret = {}
            ret["i"] = int(m.group(1))
            ret[reg_or_cache] = int(m.group(2))
            ret["e"] = int(m.group(3))
            ret["r"] = int(m.group(4))
            ret["hits"] = int(m.group(5))
            ret["false_hit"] = int(m.group(6))
        return ret

    def setSize(self, header):
        # iterations: 100000 board: TITAN V number_sms: 80 shared_mem: 98304 l2_size: 4718592 one_second_cycles: 0 test_mode: L1

        m = re.match(".*iterations: (\d+).*board:(.*?)number_sms: (\d+).*shared_mem: (\d+).*l2_size: (\d+).*"
                     "one_second_cycles: (\d+).*test_mode: (\S+).*", header)
        self.__iterations = self.__board  = self.__numberSms = self.__testMode = None
        if m:
            self.__iterations = int(m.group(1))
            self.__board = m.group(2).replace(" ", "")
            self.__numberSms = int(m.group(3))
            self.__sharedMem = int(m.group(4))
            self.__l2Size = int(m.group(5))
            if "TITANV" in self.__board:
                self.__l1Size = 96 * 1024
            elif "K20" in self.__board or "K40" in self.__board:
                self.__l1Size = 48 * 1024

            self.__testMode = m.group(7)

        self._size = "iterations_{}_board_{}_number_sms_{}_test_mode_{}".format(self.__iterations, self.__board, self.__numberSms,
                                                                                self.__testMode)

    def _relativeErrorParser(self, errList):
        self._cacheLineErrors = 0
        self._SBF = 0
        self._MBF = 0
        self._zeroToOne = 0
        self._oneToZero = 0
        self._smsCorrupted = 0

        if len(errList) <= 0 or self.__testMode == 'REGISTERS':
            self._cacheLineErrors = -1
            self._SBF = -1
            self._MBF = -1
            self._zeroToOne = -1
            self._oneToZero = -1
            self._smsCorrupted = -1
            return

        errorDict = {}
        # get the 0 to 1, or 1 to 0 errors
        for err in errList:
            expected = err['e']
            read = err['r']

            # save for future uses
            errorDict[err['i']] = True

            xor = bin(expected ^ read)
            countOnes = xor.count('1')
            if countOnes > 1:
                self._MBF += 1
            elif countOnes == 1:
                self._SBF += 1

            if expected != read and countOnes == 0:
                print "\nPau log ", self._logFileName, self._sdcIteration

            # Count the 0 to 1
            if expected == 0 and read != 0:
                self._zeroToOne += 1
            # Count the 1 to 0
            if expected != 0 and read < expected:
                self._oneToZero += 1

        # Check which lines were corrupted by the single event
        vSize = self.__l1Size / self.__cacheLineSize
        if self.__testMode == "L2":
            vSize = self.__l2Size / self.__cacheLineSize
        elif self.__testMode == "SHARED":
            vSize = self.__sharedMem / self.__cacheLineSize

        vSize = int(vSize)

        for sm in range(self.__numberSms):
            smError = False
            for thread in range(vSize):
                bytesCorrupted = 0
                for byte in range(self.__cacheLineSize):
                    i = (sm * vSize + thread) * self.__cacheLineSize + byte
                    if i in errorDict:
                        bytesCorrupted += 1

                if bytesCorrupted != 0:
                    smError = True

                # bigger than a word size
                if bytesCorrupted > self.__wordSize:
                    self._cacheLineErrors += 1

            self._smsCorrupted += int(smError)

    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass

    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
                                 self._machine,
                                 self._benchmark,
                                 self._sdcIteration,
                                 self._accIteErrors,
                                 self._iteErrors,
                                 self._zeroToOne,
                                 self._oneToZero,
                                 self._cacheLineErrors,
                                 self._SBF,
                                 self._MBF,
                                 self._smsCorrupted,
                                 self._header]
