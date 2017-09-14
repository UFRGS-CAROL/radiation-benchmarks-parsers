
from Parser import Parser
import re

class BezierSurfaceParser(Parser):

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)



    def parseErrMethod(self, errString):
        # print errString
        m = re.match(".*([X-Y-Z]+),.*p\: \[(\d+), (\d+)\],.*r\: (\S+),.*e\: (\S+).*", errString)
        ret = None
        if m:
            ret = [0] * 5
            ret[0] = str(m.group(1))
            ret[1] = int(m.group(2))
            ret[2] = int(m.group(3))
            ret[3] = float(m.group(4))
            ret[4] = float(m.group(5))

        return ret

    ## tem que retornar tudo isso
    #[self._maxRelErr, self._minRelErr, self._avgRelErr, self._zeroOut, self._zeroGold,
    # self._relErrLowerLimit,
    # self._errors["errListFiltered"], self._relErrLowerLimit2,
    # self._errors["errListFiltered2"]]
    def _relativeErrorParser(self, errList):
        if len(errList) <= 0:
            return

        for i in errList:
            print i


    # def relativeErrorParser(self):
    #     # print "done"
    #     pass



    def buildImageMethod(self):
        return False

    def setSize(self, header):
        ##HEADER -i 5 -g 5 -a 1.00 -t 4 -n 2500
        m = re.match(".*\-i (\d+).*\-g (\d+).*\-a (\S+).*\-t (\d+).*\-n (\d+).*", header)
        if m:
            self._i = m.group(1)
            self._g = m.group(2)
            self._a = float(m.group(3))
            self._t = m.group(4)
            self._n = m.group(5)
            self._size = str(self._i) + "_" + str(self._g) + "_" + str(self._a)\
                         + "_" + str(self._t) + "_" + str(self._n)



    def getBenchmark(self):
        return 'beziersurface'