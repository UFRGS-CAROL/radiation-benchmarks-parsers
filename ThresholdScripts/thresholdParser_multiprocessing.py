#!/usr/bin/env python

import sys
import csv
import re
import parseUtils
import parseErrorUtils
import shelve
import threading
from multiprocessing import Process, Queue

class parserThread (threading.Thread):
    def __init__(self, benchmarkname_machinename, sdcItemList):
        threading.Thread.__init__(self)
        self.benchmarkname_machinename = benchmarkname_machinename
        self.sdcItemList = sdcItemList
        self.threadTotals = dict()
        self.errLimitList = [float(i)/precision for i in range(0, precision*limitRange+1)]
        self.errLimitList.sort()
        #threadsOutput.append("["+str(len(threadsOutput))+" Starting] ")
        #self.idx = len(threadsOutput)-1
    def run(self):
        processErrors(self.benchmarkname_machinename, self.sdcItemList, self.threadTotals, self.errLimitList)
        
class parserProcess (Process):
    def __init__(self, benchmarkname_machinename, sdcItemList, precision, limitRange, processesTotals_queue):
        super(parserProcess, self).__init__()
        self.benchmarkname_machinename = benchmarkname_machinename
        self.sdcItemList = sdcItemList
        self.processTotals = dict()
        self.errLimitList = [float(i)/precision for i in range(0, precision*limitRange+1)]
        self.errLimitList.sort()
        #threadsOutput.append("["+str(len(threadsOutput))+" Starting] ")
        #self.idx = len(threadsOutput)-1
    def run(self):
        processErrors(self.benchmarkname_machinename, self.sdcItemList, self.processTotals, self.errLimitList)
        processesTotals_queue.put(self.processTotals)


def processErrors(benchmarkname_machinename, sdcItemList, processTotals, errLimitList):
    benchmark = benchmarkname_machinename
    machine = benchmarkname_machinename
    m = re.match("(.*)_(.*)", benchmarkname_machinename)
    if m:
        benchmark = m.group(1)
        machine = m.group(2)

        benchmark = benchmark.strip()
        machine = machine.strip()

        if not parseErrorUtils.hasParser(benchmark):
            #print benchmark+" - There is no parser implemented"
            return

    sdci = 1
    total_sdcs = len(sdcItemList)
    csvHeader = list()
    csvHeader.append("logFileName")
    csvHeader.append("machine")
    csvHeader.append("benchmark")
    csvHeader.append("header")
    csvHeader.append("sdcIteration")
    csvHeader.append("numberAccumulatedErrors")
    csvHeader.append("numberIterationErrors")
    csvHeader.append("numberIterationErrorsLogged")
    csvHeader.append("numberIterationErrorsParsed")
    csvHeader.append("maxRelativeError")
    csvHeader.append("minRelativeError")
    csvHeader.append("averageRelativeError")
    for errLimit in errLimitList:
        csvHeader.append("numberErrorsLessThan"+str(errLimit))
        csvHeader.append("localityForErrorsHigherThan"+str(errLimit))
    csvHeader.append("numberZeroOutput")
    csvHeader.append("numberZeroGold")

    for sdcItem in sdcItemList:
        progress = "{0:.2f}".format(sdci/total_sdcs * 100)

        #threadsOutput[threadIdx] = "[ "+benchmark+" "+str(sdci)+"/"+str(total_sdcs)+"] "
        #output = ""
        #for i in range(0, numThreads):
        #    output +=  threadsOutput[i]
        #sys.stdout.write("\r"+output)
        #sys.stdout.flush()

        logFileName = sdcItem[0]
        header = sdcItem[1]
        header = header.strip()
        header = re.sub(r"[^\w]", '-', header) #keep only numbers and digits
        header = header.strip()
        sdcIteration = sdcItem[2]
        iteErrors = sdcItem[3]
        accIteErrors = sdcItem[4]
        errList = sdcItem[5]

#        csvOutDict = dict()
#        csvOutDict["logFileName"] = logFileName
#        csvOutDict["machine"] = machine
#        csvOutDict["benchmark"] = benchmark
#        csvOutDict["header"] = header
#        csvOutDict["sdcIteration"] = sdcIteration
#        csvOutDict["numberAccumulatedErrors"] = accIteErrors
#        csvOutDict["numberIterationErrors"] = iteErrors
        
        key = benchmarkname_machinename+"_"+header

        if (not key in processTotals):
            processTotals[key] = dict()
            processTotals[key]["errors"] = 0.0
            for errLimit in errLimitList:
                processTotals[key][str(errLimit)] = 0.0

        
        logFileNameNoExt = logFileName
        m = re.match("(.*).log", logFileName)
        if m:
            logFileNameNoExt = m.group(1)
#            csvOutDict["numberIterationErrorsLogged"] = len(errList)
            errorsParsed = parseErrorUtils.parseErrors(errList, benchmark, header)
            if errorsParsed is None:
                sdci += 1
                continue
#            csvOutDict["numberIterationErrorsParsed"] = len(errorsParsed)
#            (csvOutDict["numberZeroOutput"], csvOutDict["numberZeroGold"] ) = parseUtils.countZerosReadExpected(errorsParsed)
            
            (maxRelErr, minRelErr, avgRelErr, relErrLowerLimit, errListFiltered) = parseUtils.relativeErrorParser(errorsParsed, 0.0)
            totErrors = len(errListFiltered)
            
            if (totErrors > 0):
                processTotals[key]["errors"] += 1.0
                for errLimit in errLimitList:
                    (maxRelErr, minRelErr, avgRelErr, relErrLowerLimit, errListFiltered) = parseUtils.relativeErrorParser(errorsParsed, errLimit)
#                    csvOutDict["maxRelativeError"] = maxRelErr
#                    csvOutDict["minRelativeError"] = minRelErr
#                    csvOutDict["averageRelativeError"] = avgRelErr
#                    csvOutDict["numberErrorsLessThan"+str(errLimit)] = relErrLowerLimit
#                    csvOutDict["localityForErrorsHigherThan"+str(errLimit)] = parseUtils.localityMultiDimensional(errListFiltered)
                    if (relErrLowerLimit == totErrors):
                        processTotals[key][str(errLimit)] += 1
                        
                    elif (relErrLowerLimit > totErrors):
                        print("wtf:"+str(relErrLowerLimit)+">"+str(totErrors))



        # Write info to csv file
#                csvFileName = "logs_parsed_machine-"+machine+"_benchmark-"+benchmark+"_header-"+header+".csv"
#                csvFullPath = os.path.join(csvDirOut, csvFileName)
#        if not os.path.exists(os.path.dirname(csvFullPath)):
#            try:
#                os.makedirs(os.path.dirname(csvFullPath))
#            except OSError as exc: # Guard against race condition
#                if exc.errno != errno.EEXIST:
#                    raise
#                if not os.path.isfile(csvFullPath):
#                    csvWFP = open(csvFullPath, "a")
#                    writer = csv.writer(csvWFP, delimiter=';')
#                    writer.writerow(csvHeader)
#                else:
#                    csvWFP = open(csvFullPath, "a")
#                    writer = csv.writer(csvWFP, delimiter=';')
#                row = list()
#                for item in csvHeader:
#                    if item in csvOutDict:
#                        row.append(csvOutDict[item])
#                    else:
#                        row.append(" ")
#                writer.writerow(row)
#
#                csvWFP.close()
        sdci += 1

#    sys.stdout.write("\r"+benchmark+" - Processing SDC "+str(sdci-1)+" of "+str(total_sdcs)+" - 100%                     "+"\n")
#    sys.stdout.flush()
################ => processErrors()


###########################################
# MAIN
###########################################
if __name__ == "__main__":
    csvDirOutPrefix = "parsed_"
    print "\n\tCSV files will be stored in "+csvDirOutPrefix+"+db folder\n"

    precision = 10
    limitRange = 10

    numThreads = 0

    processes = []
    processesTotals_queue = Queue()
    processesTotals = []
    #threadsOutput = []

    for inputDB in sys.argv[1:]:
        print("Loading database: "+inputDB+" ...")
        csvDirOut = csvDirOutPrefix + inputDB.replace('/', '')
        db = shelve.open(inputDB) #python2
        #for k, v in db.items(): #python3
        for k, v in db.iteritems(): #python2
            #threads.append(parserThread(k, v))
            processes.append(parserProcess(k, v, precision, limitRange, processesTotals_queue))
            numThreads += 1
            #processErrors(k,v)
        db.close()
        
    print "Number of processes: "+str(numThreads)
        
    for process in processes:
        process.start()
        
    for process in processes:
        process.join()
        
    print "\nGenerating totals..."
    
    errLimitList = [float(i)/precision for i in range(0, precision*limitRange+1)]
    errLimitList.sort()
    
    for totals in range(0, numThreads):
        processesTotals.append(processesTotals_queue.get())
        
    totals = dict()
    for processTotals in processesTotals:
        for key in processTotals.iterkeys():
            if not (key in totals):
                totals[key] = dict()
                totals[key]["errors"] = 0.0
                for errLimit in errLimitList:
                    totals[key][str(errLimit)] = 0.0
            for secondKey in processTotals[key]:
                totals[key][secondKey] += processTotals[key][secondKey]
            
        
    print "\nOutputing to file..."

    csvHeader = list()
    csvHeader.append("Threshold")
    csvHeader.append("Percentage")
    csvHeader.append("Machine")

    #print(totals)

    csvWFP = open("thresholds_summary_"+sys.argv[1].replace('/', '')+".csv", "w")
    writer = csv.writer(csvWFP, delimiter=';')
    writer.writerow(csvHeader)
    for key in totals.iterkeys():
        last = 0
        for errLimit in errLimitList:
            if ((last != totals[key][str(errLimit)]) or (errLimit == errLimitList[-1])):
                last = totals[key][str(errLimit)]
                csvRow = list()
                csvRow.append(str(errLimit))
                csvRow.append(str(100 - (float(totals[key][str(errLimit)]) / float(totals[key]["errors"])) * 100.0))
                csvRow.append(key)
                writer.writerow(csvRow)
    csvWFP.close()
