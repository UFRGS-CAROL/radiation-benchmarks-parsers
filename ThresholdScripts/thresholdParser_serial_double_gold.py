#!/usr/bin/env python

import sys
import os
import csv
import re
import collections

import errno

import struct

import parseUtils_gold_tre
import parseErrorUtils_gold_tre
import shelve


def processErrors(benchmarkname_machinename, sdcItemList, gold_tre_array):
    benchmark = benchmarkname_machinename
    machine = benchmarkname_machinename
    m = re.match("(.*)_(.*)", benchmarkname_machinename)
    if m:
        benchmark = m.group(1)
        machine = m.group(2)

        benchmark = benchmark.strip()
        machine = machine.strip()

        if not parseErrorUtils_gold_tre.hasParser(benchmark):
            print benchmark + " - There is no parser implemented"
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
        csvHeader.append("numberErrorsLessThan" + str(errLimit))
        csvHeader.append("localityForErrorsHigherThan" + str(errLimit))
    csvHeader.append("numberZeroOutput")
    csvHeader.append("numberZeroGold")

    for sdcItem in sdcItemList:
        progress = "{0:.2f}".format(sdci / total_sdcs * 100)
        sys.stdout.write(
            "\r" + benchmark + " - Processing SDC " + str(sdci) + " of " + str(total_sdcs) + " - " + progress + "%")
        sys.stdout.flush()

        logFileName = sdcItem[0]
        header = sdcItem[1]
        header = header.strip()
        header = re.sub(r"[^\w]", '-', header)  # keep only numbers and digits
        header = header.strip()
        sdcIteration = sdcItem[2]
        iteErrors = sdcItem[3]
        accIteErrors = sdcItem[4]
        errList = sdcItem[5]

        #        if not "gemm" in benchmark:
        #            break

        csvOutDict = dict()
        csvOutDict["logFileName"] = logFileName
        csvOutDict["machine"] = machine
        csvOutDict["benchmark"] = benchmark
        csvOutDict["header"] = header
        csvOutDict["sdcIteration"] = sdcIteration
        csvOutDict["numberAccumulatedErrors"] = accIteErrors
        csvOutDict["numberIterationErrors"] = iteErrors

        key = benchmarkname_machinename + "_" + header
        if (not key in totals):
            totals[key] = dict()
            totals[key]["errors"] = 0.0
            for errLimit in errLimitList:
                totals[key][str(errLimit)] = 0.0

        logFileNameNoExt = logFileName
        m = re.match("(.*).log", logFileName)
        if m:
            logFileNameNoExt = m.group(1)

            csvOutDict["numberIterationErrorsLogged"] = len(errList)
            errorsParsed = parseErrorUtils_gold_tre.parseErrors(errList, benchmark, header)
            if errorsParsed is None:
                sdci += 1
                continue
            csvOutDict["numberIterationErrorsParsed"] = len(errorsParsed)
            (csvOutDict["numberZeroOutput"], csvOutDict["numberZeroGold"]) = parseUtils_gold_tre.countZerosReadExpected(
                errorsParsed)

            (maxRelErr, minRelErr, avgRelErr, relErrLowerLimit, errListFiltered) = parseUtils_gold_tre.relativeErrorParser(
                errorsParsed, 0.0, gold_tre_array)
            totErrors = len(errListFiltered)

            if (totErrors > 0):
                totals[key]["errors"] += 1.0
                for errLimit in errLimitList:
                    (maxRelErr, minRelErr, avgRelErr, relErrLowerLimit,
                     errListFiltered) = parseUtils_gold_tre.relativeErrorParser(errorsParsed, errLimit, gold_tre_array)
                    csvOutDict["maxRelativeError"] = maxRelErr
                    csvOutDict["minRelativeError"] = minRelErr
                    csvOutDict["averageRelativeError"] = avgRelErr
                    csvOutDict["numberErrorsLessThan" + str(errLimit)] = relErrLowerLimit
                    csvOutDict["localityForErrorsHigherThan" + str(errLimit)] = parseUtils_gold_tre.localityMultiDimensional(
                        errListFiltered)
                    if (relErrLowerLimit == totErrors):
                        totals[key][str(errLimit)] += 1
                    elif (relErrLowerLimit > totErrors):
                        print("wtf:" + str(relErrLowerLimit) + ">" + str(totErrors))



                    # Write info to csv file
        csvFileName = "logs_parsed_machine-" + machine + "_benchmark-" + benchmark + "_header-" + header + ".csv"
        csvFullPath = os.path.join(csvDirOut, csvFileName)
        if not os.path.exists(os.path.dirname(csvFullPath)):
            try:
                os.makedirs(os.path.dirname(csvFullPath))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
                if not os.path.isfile(csvFullPath):
                    csvWFP = open(csvFullPath, "a")
                    writer = csv.writer(csvWFP, delimiter=';')
                    writer.writerow(csvHeader)
                else:
                    csvWFP = open(csvFullPath, "a")
                    writer = csv.writer(csvWFP, delimiter=';')
                row = list()
                for item in csvHeader:
                    if item in csvOutDict:
                        row.append(csvOutDict[item])
                    else:
                        row.append(" ")
                writer.writerow(row)

                csvWFP.close()
        sdci += 1

    sys.stdout.write("\r" + benchmark + " - Processing SDC " + str(sdci - 1) + " of " + str(total_sdcs) + " - 100%\n")
    sys.stdout.flush()


################ => processErrors()
# For MxM
def load_gold_to_array_mxm(gold_path):
    DEFAULT_SIZE = 8192 * 8192
    print("Loading gold from mxm")
    with open(gold_path, "rb") as fp:
        arr_ct = struct.unpack("d" * DEFAULT_SIZE, fp.read(8 * DEFAULT_SIZE))
    return arr_ct, DEFAULT_SIZE

# For Lava
def load_gold_to_array_lava(gold_path, nboxes):
    array = []
    NUMBER_PAR_PER_BOX = 192

    print("Loading gold from lava")
    space_elem = nboxes * nboxes * nboxes * NUMBER_PAR_PER_BOX
    with open(gold_path, "rb") as fp:

        while True:
            # return_value[0] = fread( & (fv_cpu_GOLD[i].v), 1, sizeof(tested_type), fp);
            element = fp.read(8)
            if not element:
                break
            v, = struct.unpack("d", element)
            # return_value[1] = fread( & (fv_cpu_GOLD[i].x), 1, sizeof(tested_type), fp);
            element = fp.read(8)
            x, = struct.unpack("d", element)
            # return_value[2] = fread( & (fv_cpu_GOLD[i].y), 1, sizeof(tested_type), fp);
            element = fp.read(8)
            y, = struct.unpack("d", element)
            # return_value[3] = fread( & (fv_cpu_GOLD[i].z), 1, sizeof(tested_type), fp);
            element = fp.read(8)
            z, = struct.unpack("d", element)
            array.append({"v": float(v), "x": float(x), "y": float(y), "z": float(z)})

    return array, NUMBER_PAR_PER_BOX


###########################################
# MAIN
###########################################
csvDirOutPrefix = "parsed_"
print "\n\tCSV files will be stored in " + csvDirOutPrefix + "+db folder\n"

totals = dict()
errLimitList = [0.0, 2 ** -300, 10 ** -64]
errLimitList += [float(10 ** i) for i in range(-8, -1)]
errLimitList += [float(i) / 10 for i in range(1, 101)]
# errLimitList += [float(i) for i in range(10, 101)]
errLimitList.sort()


gold_path_lava = "/home/fernando/Dropbox/temp/golds_tre/lava_gold_double_15"
gold_path_mxm = "/home/fernando/Dropbox/temp/golds_tre/GOLD_8192_use_tensor_0.matrix"
gold_tre_array_lava, max_size_lava = load_gold_to_array_lava(gold_path=gold_path_lava, nboxes=15)
gold_tre_array_mxm, max_size_mxm = load_gold_to_array_mxm(gold_path=gold_path_mxm)

gold_tre_array_micro = 4.444444444444444
max_size_micro = 1

for inputDB in sys.argv[1:]:
    print(inputDB)
    csvDirOut = csvDirOutPrefix + inputDB.replace('/', '')
    db = shelve.open(inputDB)  # python2
    # for k, v in db.items(): #python3
    for k, v in db.iteritems():  # python2
        print("Processing {}".format(k))
        # if "LAVA" in k.upper():
        #     processErrors(k, v, {"data": gold_tre_array_lava, "type": "lava", "max_size": max_size_lava})
        # if "MXM" in k.upper():
        #     processErrors(k, v, {"data": gold_tre_array_mxm, "type": "mxm", "max_size": max_size_mxm})
        if "MICRO" in k.upper():
            processErrors(k, v, {"data": gold_tre_array_micro, "type": "micro", "max_size": max_size_micro})

    db.close()

csvHeader = list()
csvHeader.append("Threshold")
csvHeader.append("Percentage")
csvHeader.append("Configuration")

# print(totals)

csvWFP = open("thresholds_summary.csv", "w")
writer = csv.writer(csvWFP, delimiter=';')
writer.writerow(csvHeader)
# csvWFPgemm = open("thresholds_gemm.csv", "w")
# writerGemm = csv.writer(csvWFPgemm, delimiter=';')
# writerGemm.writerow(csvHeader)
# csvWFPhotspot = open("thresholds_hotspot.csv", "w")
# writerHotspot = csv.writer(csvWFPhotspot, delimiter=';')
# writerHotspot.writerow(csvHeader)
# csvWFPlava = open("thresholds_lava.csv", "w")
# writerLava = csv.writer(csvWFPlava, delimiter=';')
# writerLava.writerow(csvHeader)
for key in totals.iterkeys():
    last = -1
    for errLimit in errLimitList:
        if ((last != totals[key][str(errLimit)]) or (errLimit == errLimitList[-1]) or (errLimit == errLimitList[0])):
            last = totals[key][str(errLimit)]
            csvRow = list()
            csvRow.append(str(errLimit))
            csvRow.append(str(100 - (float(totals[key][str(errLimit)]) / float(totals[key]["errors"])) * 100.0))
            csvRow.append(key)
            writer.writerow(csvRow)


# csvWFP.close()
# csvWFPgemm.close()
# csvWFPhotspot.close()
# csvWFPlava.close()
