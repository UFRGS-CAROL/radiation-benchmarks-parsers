import re
from SortParser import SortParser


class MergesortParser(SortParser):
    def __init__(self, **kwargs):
        SortParser.__init__(self, **kwargs)


    """
    input: header is the logfilename header
    no return
    must set _size attribute to a string,
    this string will be used to create the csv file
    """
    def setSize(self, header):
        self._size = None
        m = re.match(".*size\:(\d+).*", header)
        if m:
            try:
                self._size = int(m.group(1))
            except:
                self._size = None
        self._size = 'mergesort_input_' + str(self._size)