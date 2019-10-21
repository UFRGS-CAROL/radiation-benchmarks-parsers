import re
import struct
import sys

from Parser import Parser


class MicroParser(Parser):
    _csvHeader = ['logFileName', 'Machine', 'Benchmark', 'Header',
                  'SDC', 'LOGGED_ERRORS', 'ACC_ERR', 'corrupted_elements', 'detected_elements']
    _corrupted_elements = 0
    _detected_elements = 0

    def parseErrMethod(self, errString):
        if '#INF detected_dmr_errors:' in errString:
            pattern = '#INF detected_dmr_errors: (\d+)'
            m = re.match(pattern, errString)
            return int(m.group(1))
        elif '#ERR p:' in errString:

            pattern = '#ERR p: \[(\d+)\], r: (\S+), e: (\S+)(,)?(.*smaller_precision: (\S+))?'
            m = re.match(pattern, errString)
            i = int(m.group(1))
            r = float(m.group(2))
            e = float(m.group(3).replace(",", ""))
            try:
                s = float(m.group(6))
                return [i, r, e, s]
            except TypeError:
                return [i, r, e]
        else:
            return None

    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass

    def setSize(self, header):
        #   gridsize-131072 blocksize-1024 type-add-double-precision hard-dmr
        #  kernel_type-non-persistent checkblock-100 nonconst-0 numop-100
        pattern = '.*gridsize:.*blocksize:.*type:(\S+)-double-precision '
        pattern += 'hard:(\S+) kernel_type:non-persistent checkblock:(\d+) nonconst:0 numop:(\d+).*'
        m = re.match(pattern, header)
        micro_type, hardening, checkblock = [None] * 3
        if m:
            try:
                micro_type = m.group(1)
                hardening = m.group(2)
                checkblock = m.group(3)
            except TypeError:
                micro_type = hardening = checkblock = None

        # return size
        self._size = "{}_{}_{}".format(micro_type, hardening, checkblock)

    """
     no return
     this method will be called by parent classes,
     so it needs only be adjusted to write the final content to self._outputListError
     this method will be clalled in every SDC processing
    """

    def _placeOutputOnList(self):
        # 'logFileName', 'Machine', 'Benchmark', 'Header',
        self._outputListError = [self._logFileName, self._machine, self._benchmark, self._header,

                                 # 'SDC', 'LOGGED_ERRORS', 'ACC_ERR', 'ACC_TIME',
                                 self._sdcIteration, self._iteErrors, self._accIteErrors,
                                 self._corrupted_elements, self._detected_elements]

    def float_to_int(self, f):
        t = hex(struct.unpack('<Q', struct.pack('<d', f))[0])
        return long(t, 0)

    """
    errList = list of dicts parsed by parseErrMethod
    no return
    set the class atributes which will be write by _writeToCSV method
    """
    def _relativeErrorParser(self, errList):
        if len(errList) < 1:
            return
        self._corrupted_elements = self._detected_elements = 0
        for err in errList:
            if type(err) is int or type(err) is long:
                self._detected_elements += 1
            elif len(err) == 3 or len(err) == 4:
                self._corrupted_elements += 1


