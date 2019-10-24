import re

"""All benchmarks must be an atribute of MatchBenchmark, it will turn allmost all parser process invisible"""


class MatchBenchmark():
    # all fucking benchmarks here
    __radiationBenchmarks = None

    # for the current processing benchmark
    __currBench = None
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    __notMatchedBenchs = []
    """sdcItem is => [logfile name, header, sdc iteration, iteration total amount error, iteration accumulated error, list of errors ]"""

    def __init__(self, **kwargs):
        self.__currBench = None

        # must have the radiationBenchmarks parameter
        self.__radiationBenchmarks = kwargs.get("radiation_benchmarks")

    #

    def processHeader(self, sdcItem, benchmarkMachineName):
        logFileName = sdcItem[0]
        try:
            logFileNameNoExt = (logFileName.split("."))[0]
        except:
            logFileNameNoExt = ""

        try:
            pureHeader = sdcItem[1]
            header = re.sub(r"[^\w\s]", '-', pureHeader)  # keep only numbers and digits
            sdcIteration = sdcItem[2]
            iteErrors = sdcItem[3]
            accIteErrors = sdcItem[4]
            errList = sdcItem[5]
            # print "\n" , len(errList)
            m = re.match("(.*)_(.*)", benchmarkMachineName)
            benchmark = "default"
            machine = "carol"
        except:
            return None
        if m:
            benchmark = m.group(1)
            machine = m.group(2)

        isBench = False
        key = None
        for key, values in self.__radiationBenchmarks.items():
            isBench = re.search(str(key), benchmark, flags=re.IGNORECASE)
            if isBench:
                # print "\n\ncurrent bench ", key
                # print "\n\n len " ,logFileName, machine, benchmark, header, sdcIteration, accIteErrors, iteErrors
                self.__currBench = self.__radiationBenchmarks[str(key)]

                # doind it I will have duplicate data, but it is the cost of generalization
                self.__currBench.setDefaultValues(logFileName, machine, benchmark, header, sdcIteration, accIteErrors,
                                                  iteErrors, errList, logFileNameNoExt, pureHeader)
                # print self.__currBench.debugAttPrint()

                break

        if not isBench:
            if key not in self.__notMatchedBenchs:
                self.__notMatchedBenchs.append(benchmark)
        return isBench

    def checkNotDoneBenchs(self):
        if len(self.__notMatchedBenchs) == 0:
            return ""

        return "These benchmarks were not found on radiation_list " + str(set(self.__notMatchedBenchs))

    def getCurrentObj(self):
        return self.__currBench

    def parseErrCall(self):
        self.__currBench.parseErr()

    def relativeErrorParserCall(self):
        self.__currBench.relativeErrorParser()

    def localityParserCall(self):
        self.__currBench.localityParser()

    def jaccardCoefficientCall(self):
        self.__currBench.jaccardCoefficient()

    def buildImageCall(self):
        self.__currBench.buildImageMethod()

    def writeToCSVCall(self):
        self.__currBench.writeToCSV()
