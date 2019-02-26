import re

from Parser import Parser


class CachesParser(Parser):
    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors",
                  "#Iteration_Errors", "header"]

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
            ret["i"] = (m.group(i))
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
        # iterations: 10000 precision: half matrix_n_dim: 8192 triplicated: 1
        m = re.match(".*iterations: (\d+).*precision: (\S+) matrix_n_dim: (\S+) triplicated: (\d+).*", header)
        iterations = precision = size = triplicated = None
        if m:
            iterations = int(m.group(1))
            precision = m.group(2)
            size = int(m.group(3))
            triplicated = int(m.group(4))

        self._size = "iterations_{}_precision_{}_size_{}_triplicated_{}".format(iterations, precision, size,
                                                                                triplicated)

    def _relativeErrorParser(self, errList):

        for err in errList:
            print err
        raise NotImplementedError


    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
                                 self._machine,
                                 self._benchmark,
                                 self._sdcIteration,
                                 self._accIteErrors,
                                 self._iteErrors,
                                 self._header]
