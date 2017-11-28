#!/usr/bin/env python

import sys
import os
import csv
import re
import collections
import shelve

benchmarkWarnings = []

def processErrors(benchmarkname_machinename, sdcItemList):
    m = re.match("(.*)_(.*)", benchmarkname_machinename)

    if not m:
        return

    benchmark = m.group(1).strip()
    machine = m.group(2).strip()

    total_sdcs = len(sdcItemList)
    sdci = 1

    for sdcItem in sdcItemList:
        progress = "{0:.2f}".format(sdci/total_sdcs * 100)
        sys.stdout.write("\r"+benchmark+" - Processing SDC "+str(sdci)+" of "+str(total_sdcs)+" - "+progress+"%")
        sys.stdout.flush()

        sizeRE = re.match(".*?(\d+).*", sdcItem[1])
        if not sizeRE:
            continue

        logFileName = sdcItem[0]
        # header = sdcItem[1]
        # header = header.strip()
        # header = re.sub(r"[^\w]", '-', header) #keep only numbers and digits
        # header = header.strip()
        header = int(sizeRE.group(1))
        sdcIteration = int(sdcItem[2])
        iteErrors = int(sdcItem[3])
        accIteErrors = int(sdcItem[4])
        errList = sdcItem[5]

        if not re.match("(.*).log", logFileName):
            continue
        
        if "SORT" in benchmark.upper():
            goldCount = int(header)
        elif "GEMM" in benchmark.upper() or "hotspot" in benchmark.upper():
            goldCount = int(header) * int(header)
        else:
            if not benchmark in benchmarkWarnings:
                benchmarkWarnings.append(benchmark)
                sys.stdout.write("\nBenchmark " + benchmark + " not implemented.\n")
            continue

        sdcInfo = dict()
        sdcInfo["machine"] = machine
        sdcInfo["benchmark"] = benchmark
        sdcInfo["header"] = header
        sdcInfo["sdcIteration"] = sdcIteration
        sdcInfo["goldCount"] = goldCount
        sdcInfo["errorLogged"] = len(errList)
        sdcInfo["errorCount"] = iteErrors
        sdcInfo["difference"] = (float(iteErrors) / float(goldCount)) * 100.0
        sdcInfo["logfile"] = logFileName
        
        sdcsInfo.append(sdcInfo)

    sys.stdout.write("\r"+benchmark+" - Processing SDC "+str(sdci)+" of "+str(total_sdcs)+" - 100%                     "+"\n")
    sys.stdout.flush()
################ => processErrors()
    



###########################################
# MAIN
###########################################
csvDirOutPrefix = "parsed_"
print "\n\tCSV summary will be saved to difference_summary.csv in overwrite mode.\n"

sdcsInfo = list()

for inputDB in sys.argv[1:]:
    print(inputDB)
    csvDirOut = csvDirOutPrefix + inputDB.replace('/', '')
    db = shelve.open(inputDB)
    for k, v in db.iteritems():
        processErrors(k, v)
    db.close()

csvHeader = list()
csvHeader.append("machine")
csvHeader.append("benchmark")
csvHeader.append("header")
csvHeader.append("SDC iteration")
csvHeader.append("gold count")
csvHeader.append("error logged")
csvHeader.append("error count")
csvHeader.append("\%difference")
csvHeader.append("logfile")

csvWFP = open("difference_summary.csv", "w")
writer = csv.writer(csvWFP, delimiter=';')
writer.writerow(csvHeader)

for sdcInfo in sdcsInfo:
    row = list()
    row.append(sdcInfo["machine"])
    row.append(sdcInfo["benchmark"])
    row.append(sdcInfo["header"])
    row.append(sdcInfo["sdcIteration"])
    row.append(sdcInfo["goldCount"])
    row.append(sdcInfo["errorLogged"])
    row.append(sdcInfo["errorCount"])
    row.append(sdcInfo["difference"])
    row.append(sdcInfo["logfile"])
    writer.writerow(row)
            
csvWFP.close()