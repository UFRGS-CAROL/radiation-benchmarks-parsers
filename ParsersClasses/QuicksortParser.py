import re
from SortParser import SortParser


class QuicksortParser(SortParser):

    def __init__(self, **kwargs):
        # super(SortParser, self).__init__(kwargs)
        SortParser.__init__(self, **kwargs)

    #tem que dar um set para o size baseado no header
    #por exemplo se o size for um numero e o input
    #setar o _size para mergesort_input_1MB
    #porque as pastas dos csvs vao ter o nome do _size
    def setSize(self, header):
        self._size = None
        m = re.match(".*size\:(\d+).*", header)
        if m:
            try:
                self._size = int(m.group(1))
            except:
                self._size = None
        self._size = 'quicksort_input_' + str(self._size)



    def buildImageMethod(self):
        return False


