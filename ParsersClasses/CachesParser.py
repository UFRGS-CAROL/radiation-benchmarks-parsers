import re

from ParsersClasses import Parser


MAX_INT_LENGHT = 32


class CachesParser(Parser.Parser):
    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors",
                  "#Iteration_Errors", "zeroToOne", "oneToZero", "singleErrors", "doubleErrors", "multipleErrors"]

    def parseErrMethod(self, errString):
        # "#ERR  i:56159 cache_line:438 e:18446744073709551615 r:18446744065119617023 hits: 0 misses: 0 false_hits: 0"
        pattern = '.*i:(\d+) (register|cache_line):(\S+) e:(\d+) r:(\d+)'
        pattern += '(.*hits: (\d+) misses: (\d+) false_hits: (\d+))?.*'
        m = re.match(pattern, errString)

        if m:
            ret = {
                "i": int(m.group(1)),
                "type": m.group(2),
                "index": m.group(3),
                "e": int(m.group(4)),
                "r": int(m.group(5))
            }

            try:
                ret["hits"] = int(m.group(6))
                ret["false_hit"] = int(m.group(7))
            finally:
                return ret

    def setSize(self, header):
        # iterations: 100000 board: TITAN V number_sms: 80 shared_
        # mem: 98304 l2_size: 4718592 one_second_cycles: 0 test_mode: L1

        m = re.match(".*iterations: (\d+).*board:(.*?)number_sms: (\d+).*shared_mem: (\d+).*l2_size: (\d+).*"
                     "one_second_cycles: (\d+).*test_mode: (\S+).*", header)
        self.__iterations = self.__board  = self.__numberSms = self.__testMode = None
        if m:
            self.__iterations = int(m.group(1))
            self.__board = m.group(2).replace(" ", "")
            self.__numberSms = int(m.group(3))
            self.__sharedMem = int(m.group(4))
            self.__l2Size = int(m.group(5))
            self.__testMode = m.group(7)

        self._size = "iterations_{}_board_{}_number_sms_{}_test_mode_{}".format(self.__iterations, self.__board,
                                                                                self.__numberSms, self.__testMode)

    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
                                 self._machine,
                                 self._benchmark,
                                 self._sdcIteration,
                                 self._accIteErrors,
                                 self._iteErrors,
                                 self._zeroToOne,
                                 self._oneToZero,
                                 self._SBF,
                                 self._DBF,
                                 self._MBF]

    def _relativeErrorParser(self, errList):
        self._SBF = 0
        self._MBF = 0
        self._DBF = 0
        self._zeroToOne = 0
        self._oneToZero = 0
        print()
        # get the 0 to 1, or 1 to 0 errors
        for err in errList:
            expected = err['e']
            read = err['r']

            es = "{0:b}".format(expected)
            rs = "{0:b}".format(read)

            eb = '0' * (MAX_INT_LENGHT - len(es)) + es
            rb = '0' * (MAX_INT_LENGHT - len(rs)) + rs

            print(es, rs)

            count = 0
            for ie, ir in zip(eb, rb):
                if ie != ir:
                    count += 1

            # Count the 0 to 1
            if expected == 0 and read != 0:
                self._zeroToOne += 1
            # Count the 1 to 0
            if expected != 0 and read < expected:
                self._oneToZero += 1

    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass
