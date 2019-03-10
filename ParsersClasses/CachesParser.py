import re

from Parser import Parser


class CachesParser(Parser):
    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors",
                  "#Iteration_Errors", "zeroToOne", "oneToZero", "cachLineErrors", "singleErrors", "header"]

    __cacheLineSize = 128  # size in bytes

    def parseErrMethod(self, errString):
        reg_or_cache = "cache_line"
        if "register" in errString:
            reg_or_cache = "register"

        # ERR  i:1589618 cache_line:12418 e:255 r:253 hits: 30720 false_hit: 0
        pattern = ".*i\:(\d+).*" + reg_or_cache + "\:(\d+).*e\:(\d+).*r\:(\d+).*hits\: (\d+).*false_hit\: (\d+).*"
        m = re.match(pattern, errString)
        if m:
            ret = {}
            i = 1
            ret["i"] = int(m.group(i))
            i += 1
            ret[reg_or_cache] = (m.group(i))
            i += 1
            ret["e"] = (m.group(i))
            i += 1
            ret["r"] = (m.group(i))
            i += 1
            ret["hits"] = (m.group(i))
            i += 1
            ret["false_hit"] = (m.group(i))
            return ret
        else:
            return None

    def setSize(self, header):
        # iterations: 100000 board: TITAN V number_sms: 80 shared_mem: 98304 l2_size: 4718592 one_second_cycles: 0 test_mode: L1

        m = re.match(
            ".*iterations: (\d+).*board:(.*?)number_sms: (\d+).*shared_mem: (\d+).*l2_size: (\d+).*one_second_cycles: (\d+).*test_mode: (\S+).*",
            header)
        iterations = board = number_sms = test_mode = None
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

        self._size = "iterations_{}_board_{}_number_sms_{}_test_mode_{}".format(iterations, board, number_sms,
                                                                                test_mode)

    def _relativeErrorParser(self, errList):
        if len(errList) <= 0:
            return

        self.__cacheLineErrors = 0
        self.__singleErrors = 0

        self.__zeroToOne = 0
        self.__oneToZero = 0

        self.__SBF = 0
        self.__MBF = 0
        # get the 0 to 1, or 1 to 0 errors
        for err in errList:
            expected = int(err['e'])
            read = int(err['r'])
            xor = bin(expected ^ read)
            countOnes = xor.count('1')
            if countOnes > 1:
                self.__MBF += 1
            elif countOnes == 1:
                self.__SBF += 1

            # Count the 0 to 1
            if expected == 0 and read != 0:
                self.__zeroToOne += 1
            # Count the 1 to 0
            if expected != 0 and read < expected:
                self.__oneToZero += 1

        # Check which lines were corrupted by the single event
        vSize = self.__l1Size / self.__cacheLineSize
        if self.__testMode == "L2":
            vSize = self.__l2Size / self.__cacheLineSize
        elif self.__testMode == "SHARED":
            vSize = self.__sharedMem / self.__cacheLineSize

        for sm in range(self.__numberSms):
            for threads in range(vSize):
                lowerBound = sm * threads
                upperBound = sm * threads + self.__cacheLineSize

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
                                 self.__zeroToOne,
                                 self.__oneToZero,
                                 self.__cacheLineErrors,
                                 self.__singleErrors,
                                 self._header]
