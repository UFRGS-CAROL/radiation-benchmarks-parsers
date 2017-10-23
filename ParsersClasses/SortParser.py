from Parser import Parser
import csv

class SortParser(Parser):

    def __init__(self, **kwargs):
        Parser.__init__(self, **kwargs)

    #tem que setar essas variaveis no _relatievErrorParser
    _timestamp = None
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
    _itLink  = None
    _itLinkOOO = None
    _itLinkSync = None
    _itLinkCorr = None
    _itMultiple = None
    _itDetected = None
    _balanceMismatches = None

    _csvHeader = ['Timestamp','Machine','Benchmark','Header','SDC','LOGGED_ERRORS','ACC_ERR',
                  'ACC_TIME','ERR_OUTOFORDER','ERR_CORRUPTED','ERR_LINK','ERR_SYNC','DETECTED',
                  'IT_OOO','IT_CORRUPTED','IT_LINK','IT_SYNC','IT_OOO_CORR','IT_SYNC_CORR',
                  'IT_SYNC_OOO','IT_LINK_OOO','IT_LINK_CORR','IT_LINK_SYNC','IT_MULTIPLE','IT_DETECTED',
                  'BALANCE_MISMATCHES','logFileName']


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
            # ['Timestamp','Machine','Benchmark','Header','SDC','LOGGED_ERRORS','ACC_ERR',
            #  'ACC_TIME','ERR_OUTOFORDER','ERR_CORRUPTED','ERR_LINK','ERR_SYNC','DETECTED',
            #  'IT_OOO','IT_CORRUPTED','IT_LINK','IT_SYNC','IT_OOO_CORR','IT_SYNC_CORR',
            #  'IT_SYNC_OOO','IT_LINK_OOO','IT_LINK_CORR','IT_LINK_SYNC','IT_MULTIPLE','IT_DETECTED',
            #  'BALANCE_MISMATCHES','logFileName']
            #arrumar para ficar as variaveis igual a ordem do do header
            outputList = [self._timestamp,
                          self._machine,
                          self._benchmark,
                          self._header,
                          self._sdcIteration,
                          self._iteErrors,
                          self._accIteErrors,
                          self._errOutOfOrder,
                          self._errCorrupted,
                          self._errLink,
                          self._errSync,
						  self._errDetected,
                          self._itOOO,
                          self._itCorrupted,
                          self._itLink,
                          self._itOOOCorr,
                          self._itSyncCorr,
                          self._itSyncOOO,
                          self._itLinkOOO,
                          self._itLinkCorr,
                          self._itLinkSync,
                          self._itMultiple,
						  self._itDetected,
                          self._balanceMismatches,
                          self._logFileName,
                    ]

            # if self._abftType != 'no_abft' and self._abftType != None:
            #     outputList.extend([])

            writer.writerow(outputList)
            csvWFP.close()

        except:
            #ValueError.message += ValueError.message + "Error on writing row to " + str(csvFileName)
            print "Error on writing row to " + str(csvFileName)
            raise

    def relativeErrorParser(self):
        self._relativeErrorParser(self._errors["errorsParsed"])



    def parseErrMethod(self, errString):

        # n += 1
        # if (n % 100) == 0:  # status para verificar se o parser engasgou
        #     print("Parsing... ", int((n * 100) / num_lines), "%", end='\t\t\t\t\t\r')

        # extrai informacoes usando expressao regular nas linhas
        # m = re.match(".*HEADER size\:(\d*).*", line)
        # if m:
        #     header = m.group(1)
        #     header.replace(",", "-")

        #TODO: transformar em  analise de errString
        #----------------------------------------------------
        m = re.match(".*INF.*", line)
        if m:
            if inf_flag == 0:
                inf_flag = 1
                it_err_counters[11] += 1
            err_counters[4] += 1

        m = re.match(".*#IT.*", line)
        if m:
            inf_flag = 0

        m = re.match(".*SDC.*", line)
        if m:  # ocorre o SDC no log apos todos os erros da execucao terem sido printados no log
            inf_flag = 0
            sdc += 1
            errors = []
            if balance != 0:
                print(">>>Warning: Balance is wrong:", balance)
                balance_mismatches += 1
            balance = 0

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

        m = re.match(".*ERR.*\Elements not ordered.*index=(\d+) ([0-9\-]+)\>([0-9\-]+)", line)
        if m:
            err_counters[0] += 1
            it_flags[0] = 1
            parsed_errors += 1

        m = re.match(".*ERR.*\The histogram from element ([0-9\-]+) differs.*srcHist=(\d+) dstHist=(\d+)",
                     line)
        if m:
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

        # ERR The link between Val and Key arrays in incorrect. index=2090080
        # wrong_key=133787990 val=54684 correct_key_pointed_by_val=-1979613866
        m = re.match(".*ERR.*\The link between Val and Key arrays in incorrect.*", line)
        if m:
            err_counters[2] += 1
            it_flags[2] = 1
            parsed_errors += 1

        #----------------------------------------------------
        # m = re.match(".*AccTime:(\d+.\d+)", line)
        # if m:
        #     acc_time = float(m.group(1))
        #
        # m = re.match(".*AccErr:(\d+)", line)
        # if m:
        #     acc_err = int(m.group(1))
        #
        # m = re.match(".*ABORT.*", line)
        # if m:
        #     abort = 1
        #
        # m = re.match(".*END.*", line)
        # if m:
        #     end = 1


