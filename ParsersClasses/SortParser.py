import re
from Parser import Parser
import csv


class SortParser(Parser):
    # tem que setar essas variaveis no _relatievErrorParser
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
    # _itDetected = None
    _balanceMismatches = None
    _hardDetec = None
    _itHardDetec = None

    # from caio's parser
    balance = 0
    parsed_errors = 0
    balance_mismatches = 0
    err_counters = [0, 0, 0, 0, 0]  # outoforder, corrupted, link error, sync/analisys error
    it_err_counters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       0]  # outoforder, corrupted, link error, sync/analisys error, ooo and corrupted,
    # sync and corrupted, sync and ooo, link and corruption, link and ooo, link and sync, 3+ combinations
    it_flags = [0, 0, 0, 0]

    _csvHeader = ['logFileName', 'Machine', 'Benchmark', 'Header',
                  'SDC', 'LOGGED_ERRORS', 'ACC_ERR',  # 'ACC_TIME',
                  'ERR_OUTOFORDER', 'ERR_CORRUPTED', 'ERR_LINK', 'ERR_SYNC',
                  'IT_OOO', 'IT_CORRUPTED', 'IT_LINK', 'IT_SYNC',
                  'IT_OOO_CORR', 'IT_SYNC_CORR', 'IT_SYNC_OOO', 'IT_LINK_OOO',
                  'IT_LINK_CORR', 'IT_LINK_SYNC', 'IT_MULTIPLE', 'BALANCE_MISMATCHES',
                  'HARD_DETEC', 'IT_HARD_DETEC']

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)

    def getBenchmark(self):
        return self._benchmark

    def localityParser(self):
        pass

    def jaccardCoefficient(self):
        pass

    # esse metodo tambem vai ser chamado na classe pai, entao so tem que estar ajustado para escrever
    # o conteudo certo,
    # ele vai ser chamado em cada processamento de sdc
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
            self.__eraseVars()

        except:
            # ValueError.message += ValueError.message + "Error on writing row to " + str(csvFileName)
            print "Error on writing row to " + str(csvFileName)
            raise

    def relativeErrorParser(self):
        self._relativeErrorParser(self._errors["errorsParsed"])

    """
    errString = ERR or INF string
    return
    balance, parsed_errors, balance_mismatches, err_counters, it_err_counters, it_flags, inf_flag
    """

    def parseErrMethod(self, errString):
        inf_flag = 0

        if "INF" in errString:
            m = re.match(".*INF.*", errString)
            if m:
                if inf_flag == 0:
                    inf_flag = 1
                    self.it_err_counters[11] += 1
                self.err_counters[4] += 1

        elif "ERR" in errString:
            # m = re.match(".*#IT.*", line)
            # if m:
            #     inf_flag = 0
            # m = re.match(".*SDC.*", line)
            # if m:  # ocorre o SDC no log apos todos os erros da execucao terem sido printados no log
            # inf_flag = 0
            # sdc += 1
            # errors = []

            if self.balance != 0:
                print(">>>Warning: Balance is wrong:", self.balance)
                self.balance_mismatches += 1
            self.balance = 0

            err_type_count = 0
            for flag in self.it_flags:
                if flag != 0:
                    err_type_count += 1
            if err_type_count >= 3:
                self.it_err_counters[10] += 1  # more than 3 types of errors
                for f in range(len(self.it_flags)):
                    self.it_flags[f] = 0

            if self.it_flags[0] and self.it_flags[1]:
                self.it_err_counters[4] += 1  # ooo and corrupted
                self.it_flags[0] = 0
                self.it_flags[1] = 0
            if self.it_flags[0] and self.it_flags[3]:
                self.it_err_counters[5] += 1  # sync and corrupted
                self.it_flags[0] = 0
                self.it_flags[3] = 0
            if self.it_flags[1] and self.it_flags[3]:
                self.it_err_counters[6] += 1  # sync and ooo
                self.it_flags[1] = 0
                self.it_flags[3] = 0
            if self.it_flags[2] and self.it_flags[0]:
                self.it_err_counters[7] += 1  # link and ooo
                self.it_flags[2] = 0
                self.it_flags[0] = 0
            if self.it_flags[2] and self.it_flags[1]:
                self.it_err_counters[8] += 1  # link and corrupted
                self.it_flags[2] = 0
                self.it_flags[1] = 0
            if self.it_flags[2] and self.it_flags[3]:
                self.it_err_counters[9] += 1  # link and sync
                self.it_flags[2] = 0
                self.it_flags[3] = 0
            for f in range(len(self.it_flags)):
                if self.it_flags[f]:
                    self.it_err_counters[f] += 1
                self.it_flags[f] = 0

            m = re.match(".*ERR.*\Elements not ordered.*index=(\d+) ([0-9\-]+)\>([0-9\-]+)", errString)
            if m:
                self.err_counters[0] += 1
                self.it_flags[0] = 1
                self.parsed_errors += 1

            m = re.match(".*ERR.*\The histogram from element ([0-9\-]+) differs.*srcHist=(\d+) dstHist=(\d+)",
                         errString)
            if m:
                if (int(m.group(2)) >= 32) or (((int(m.group(3)) - int(m.group(2))) >= 32) and (
                            ((int(m.group(3)) - int(m.group(2))) % 2) == 0)):
                    self.err_counters[3] += 1
                    self.it_flags[3] = 1
                    self.parsed_errors += 1
                    # print(">>>>Warning: Ignoring element corruption - Element: ", m.group(1), "srcHist: ", m.group(2), "dstHist: ", m.group(3))
                else:
                    self.err_counters[1] += 1
                    self.it_flags[1] = 1
                    self.parsed_errors += 1
                    self.balance += int(m.group(2)) - int(m.group(3))

            # ERR The link between Val and Key arrays in incorrect. index=2090080
            # wrong_key=133787990 val=54684 correct_key_pointed_by_val=-1979613866
            m = re.match(".*ERR.*\The link between Val and Key arrays in incorrect.*", errString)
            if m:
                self.err_counters[2] += 1
                self.it_flags[2] = 1
                self.parsed_errors += 1

        return inf_flag

    def _relativeErrorParser(self, errList):
        self._errOutOfOrder = self.err_counters[0]
        self._errCorrupted = self.err_counters[1]
        self._errLink = self.err_counters[2]
        self._errSync = self.err_counters[3]

        self._itOOO = self.it_err_counters[0]
        self._itCorrupted = self.it_err_counters[1]
        self._itLink = self.it_err_counters[2]
        self._itSync = self.it_err_counters[3]
        self._itOOOCorr = self.it_err_counters[4]
        self._itSyncCorr = self.it_err_counters[5]
        self._itSyncOOO = self.it_err_counters[6]
        self._itLinkOOO = self.it_err_counters[7]
        self._itLinkCorr = self.it_err_counters[8]
        self._itLinkSync = self.it_err_counters[9]
        self._itMultiple = self.it_err_counters[10]

        self._balanceMismatches = self.balance_mismatches
        self._hardDetec = self.err_counters[4]
        self._itHardDetec = self.it_err_counters[11]

    def __debug(self):
        print "\n", self._errOutOfOrder, self._errCorrupted, self._errLink, self._errSync, \
            self._itOOO, self._itCorrupted, self._itLink, self._itOOOCorr, self._itSyncCorr, \
            self._itSyncOOO, self._itLinkOOO, self._itLinkCorr, self._itLinkSync, self._itMultiple, \
            self._balanceMismatches, self._hardDetec, self._itHardDetec

    def __eraseVars(self):
        # from caio's parser
        self.balance = 0
        self.parsed_errors = 0
        self.balance_mismatches = 0
        self.err_counters = [0, 0, 0, 0, 0]  # outoforder, corrupted, link error, sync/analisys error
        self.it_err_counters = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                0]  # outoforder, corrupted, link error, sync/analisys error, ooo and corrupted,
        # sync and corrupted, sync and ooo, link and corruption, link and ooo, link and sync, 3+ combinations
        self.it_flags = [0, 0, 0, 0]
