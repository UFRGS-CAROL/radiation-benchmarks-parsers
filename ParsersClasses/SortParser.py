import re
from Parser import Parser
import csv


class SortParser(Parser):
    # must set this values in the _relativeErrorParser
    _errOutOfOrder = None
    _errCorrupted = None
    _errLink = None
    _errSync = None
    _errDetected = None
    _itOOO = None
    _itCorrupted = None
    _itSync = None
    _itOOOCorr = None
    _itSyncCorr = None
    _itSyncOOO = None
    _itLink = None
    _itLinkOOO = None
    _itLinkSync = None
    _itLinkCorr = None
    _itMultiple = None
    _balanceMismatches = None
    _hardDetec = None
    _itHardDetec = None

    _csvHeader = ['logFileName', 'Machine', 'Benchmark', 'Header',
                  'SDC', 'LOGGED_ERRORS', 'ACC_ERR',  # 'ACC_TIME',
                  'ERR_OUTOFORDER', 'ERR_CORRUPTED', 'ERR_LINK', 'ERR_SYNC',
                  'IT_OOO', 'IT_CORRUPTED', 'IT_LINK', 'IT_SYNC',
                  'IT_OOO_CORR', 'IT_SYNC_CORR', 'IT_SYNC_OOO', 'IT_LINK_OOO',
                  'IT_LINK_CORR', 'IT_LINK_SYNC', 'IT_MULTIPLE', 'BALANCE_MISMATCHES',
                  'HARD_DETEC', 'IT_HARD_DETEC']

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)

    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass

    """
     input csvFileName is the csv directory
     no return
     this method will be called by parent classes,
     so it needs only be adjusted to write the final content to csvFileName
     this method will be clalled in every SDC processing
    """

    def _writeToCSV(self, csvFileName):
        self._writeCSVHeader(csvFileName)

        try:

            csvWFP = open(csvFileName, "a")
            writer = csv.writer(csvWFP, delimiter=';')

            # 'logFileName', 'Machine', 'Benchmark', 'Header',
            outputList = [self._logFileName, self._machine, self._benchmark, self._header,

                          # 'SDC', 'LOGGED_ERRORS', 'ACC_ERR', 'ACC_TIME',
                          self._sdcIteration, self._iteErrors, self._accIteErrors,

                          # 'ERR_OUTOFORDER', 'ERR_CORRUPTED', 'ERR_LINK', 'ERR_SYNC',
                          self._errOutOfOrder, self._errCorrupted, self._errLink, self._errSync,

                          # 'IT_OOO', 'IT_CORRUPTED', 'IT_LINK', 'IT_SYNC',
                          self._itOOO, self._itCorrupted, self._itLink, self._itSync,

                          # 'IT_OOO_CORR', 'IT_SYNC_CORR', 'IT_SYNC_OOO', 'IT_LINK_OOO',
                          self._itOOOCorr, self._itSyncCorr, self._itSyncOOO, self._itLinkOOO,

                          # 'IT_LINK_CORR', 'IT_LINK_SYNC', 'IT_MULTIPLE', 'BALANCE_MISMATCHES',
                          self._itLinkCorr, self._itLinkSync, self._itMultiple, self._balanceMismatches,

                          # 'HARD_DETEC', 'IT_HARD_DETEC'
                          self._hardDetec, self._itHardDetec
                          ]

            writer.writerow(outputList)
            csvWFP.close()

        except:
            # ValueError.message += ValueError.message + "Error on writing row to " + str(csvFileName)
            print "Error on writing row to " + str(csvFileName)
            raise

    """
    errString = ERR or INF string
    return
    a dict with: inf or err indexes, if err is set it could be
    not_ordered, histogram_diff or link_key
    """

    def parseErrMethod(self, errString):
        ret = {}
        if "INF" in errString:
            ret['inf'] = 1
            m = re.match(".*INF.*", errString)
            if m:
                ret['inf_err_string'] = errString
        elif "ERR" in errString:
            ret['err'] = 1
            m = re.match(".*ERR.*\Elements not ordered.*index=(\d+) ([0-9\-]+)\>([0-9\-]+)", errString)
            if m:
                ret['not_ordered'] = 1

            m = re.match(".*ERR.*\The histogram from element ([0-9\-]+) differs.*srcHist=(\d+) dstHist=(\d+)",
                         errString)
            if m:
                ret['histogram_diff'] = 1
                ret['m_value'] = m

            # ERR The link between Val and Key arrays in incorrect. index=2090080
            # wrong_key=133787990 val=54684 correct_key_pointed_by_val=-1979613866
            m = re.match(".*ERR.*\The link between Val and Key arrays in incorrect.*", errString)
            if m:
                ret['link_key'] = 1

        return ret if len(ret) > 0 else None

    """
    errList = list of dicts parsed by parseErrMethod
    no return
    set the class atributes which will be write by _writeToCSV method
    """

    def _relativeErrorParser(self, errList):
        if len(errList) < 1:
            return

        # from caio's parser
        balance = 0
        parsed_errors = 0
        balance_mismatches = 0
        err_counters = [0, 0, 0, 0, 0]  # outoforder, corrupted, link error, sync/analisys error
        it_err_counters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                           0]  # outoforder, corrupted, link error, sync/analisys error, ooo and corrupted,
        # sync and corrupted, sync and ooo, link and corruption, link and ooo, link and sync, 3+ combinations
        it_flags = [0, 0, 0, 0]

        for i in errList:
            if 'inf' in i:
                # if inf_flag == 0:
                #     inf_flag = 1
                it_err_counters[11] += 1
                err_counters[4] += 1

            elif 'err' in i:
                if 'not_ordered' in i:
                    err_counters[0] += 1
                    it_flags[0] = 1
                    parsed_errors += 1

                if 'histogram_diff' in i:
                    m = i['m_value']
                    if (int(m.group(2)) >= 32) or (((int(m.group(3)) - int(m.group(2))) >= 32) and (
                                ((int(m.group(3)) - int(m.group(2))) % 2) == 0)):
                        err_counters[3] += 1
                        it_flags[3] = 1
                        parsed_errors += 1
                        # print(">>>>Warning: Ignoring element corruption - Element: ", m.group(1), "srcHist: ", m.group(2), "dstHist: ", m.group(3))
                    else:
                        err_counters[1] += 1
                        it_flags[1] = 1
                        parsed_errors += 1
                        balance += int(m.group(2)) - int(m.group(3))

                if 'link_key' in i:
                    err_counters[2] += 1
                    it_flags[2] = 1
                    parsed_errors += 1

        if balance != 0:
            # print(">>>Warning: Balance is wrong:", balance)
            balance_mismatches += 1
        # balance = 0

        err_type_count = 0
        for flag in it_flags:
            if flag != 0:
                err_type_count += 1
        if err_type_count >= 3:
            it_err_counters[10] += 1  # more than 3 types of errors
            for f in range(len(it_flags)):
                it_flags[f] = 0

        if it_flags[0] and it_flags[1]:
            it_err_counters[4] += 1  # ooo and corrupted
            it_flags[0] = 0
            it_flags[1] = 0
        if it_flags[0] and it_flags[3]:
            it_err_counters[5] += 1  # sync and corrupted
            it_flags[0] = 0
            it_flags[3] = 0
        if it_flags[1] and it_flags[3]:
            it_err_counters[6] += 1  # sync and ooo
            it_flags[1] = 0
            it_flags[3] = 0
        if it_flags[2] and it_flags[0]:
            it_err_counters[7] += 1  # link and ooo
            it_flags[2] = 0
            it_flags[0] = 0
        if it_flags[2] and it_flags[1]:
            it_err_counters[8] += 1  # link and corrupted
            it_flags[2] = 0
            it_flags[1] = 0
        if it_flags[2] and it_flags[3]:
            it_err_counters[9] += 1  # link and sync
            it_flags[2] = 0
            it_flags[3] = 0
        for f in range(len(it_flags)):
            if it_flags[f]:
                it_err_counters[f] += 1
            it_flags[f] = 0

        self._errOutOfOrder = err_counters[0]
        self._errCorrupted = err_counters[1]
        self._errLink = err_counters[2]
        self._errSync = err_counters[3]

        self._itOOO = it_err_counters[0]
        self._itCorrupted = it_err_counters[1]
        self._itLink = it_err_counters[2]
        self._itSync = it_err_counters[3]
        self._itOOOCorr = it_err_counters[4]
        self._itSyncCorr = it_err_counters[5]
        self._itSyncOOO = it_err_counters[6]
        self._itLinkOOO = it_err_counters[7]
        self._itLinkCorr = it_err_counters[8]
        self._itLinkSync = it_err_counters[9]
        self._itMultiple = it_err_counters[10]

        self._balanceMismatches = balance_mismatches
        self._hardDetec = err_counters[4]
        self._itHardDetec = it_err_counters[11]


    """
    LEGACY METHODS SECTION
    """
    """
    legacy method
    """
    # def buildImageMethod(self):
    #     return False