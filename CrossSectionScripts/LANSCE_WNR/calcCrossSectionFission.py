#!/usr/bin/python -u

import os
import sys
import re
import csv

from datetime import timedelta
from datetime import datetime


def getDt(yearDate, dayTime, secFrac):
    yv = yearDate.split('-')
    year = int(yv[0])
    month = int(yv[1])
    day = int(yv[2])

    dv = dayTime.split(':')
    hour = int(dv[0])
    minute = int(dv[1])
    second = int(dv[2])

    # we get secFrac in seconds, so we must convert to microseconds
    # e.g: 0.100 seconds = 100 milliseconds = 100000 microseconds
    microsecond = int(float("0." + secFrac) * 1e6)

    return datetime(year, month, day, hour, minute, second, microsecond)


def getWenderFactor(startDT):
    if startDT < datetime(2017, 9, 11, 8, 32, 0, 0):
        return 22228
    elif startDT < datetime(2017, 9, 11, 14, 01, 0, 0):
        return 22020
    elif startDT < datetime(2017, 9, 12, 05, 33, 0, 0):
        return 22051
    elif startDT < datetime(2017, 9, 12, 17, 24, 0, 0):
        return 22010
    elif startDT < datetime(2017, 9, 13, 07, 47, 0, 0):
        return 22096
    elif startDT < datetime(2017, 9, 13, 15, 49, 0, 0):
        return 22069
    elif startDT < datetime(2017, 9, 14, 8, 19, 0, 0):
        return 22450
    elif startDT < datetime(2017, 9, 14, 17, 18, 0, 0):
        return 21924
    else:
        return 21976


fileLines = list()


def readFissionFile():
    inFile = open(inFileName, 'r')
    global fileLines
    for l in inFile:
        line = l.rstrip()
        m = re.match("(.* 2017)(.*)", line)
        if m:
            fileLines.append(line)


def getFluenceFlux(startDT, endDT):
    pulseCount = 0
    lastDt = startDT
    timeNoPulse = 0  # in seconds

    for l in fileLines:

        line = l.rstrip()
        m = re.match("(.* 2017)(.*)", line)
        if m:
            curDt = datetime.strptime(m.group(1), "%b %d %H:%M:%S %Y")
            if startDT <= curDt and curDt <= endDT:
                try:
                    curCount = int(m.group(2))
                except ValueError:
                    continue  # Ignore line in case it contain "Start of test"

                if curCount <= 0:  # diffCount <= 0 or lastCount <= 0:
                    timeNoPulse += (curDt - lastDt).total_seconds()
                else:
                    pulseCount += curCount
                lastDt = curDt
            elif curDt > endDT:
                try:
                    # return [(pulseCount*getWenderFactor(startDT)/((endDT - startDT).total_seconds() -timeNoPulse))*factor, timeNoPulse]
                    return [(pulseCount * getWenderFactor(startDT) / ((endDT - startDT).total_seconds())) * factor,
                            timeNoPulse]
                except ZeroDivisionError:
                    return [0, 0]

    # It should not get out of the loop, but in case there is no pulse data, timeNoPulse is updated
    timeNoPulse += (endDT - curDt).total_seconds()
    try:
        return [(pulseCount * getWenderFactor(startDT) / ((endDT - startDT).total_seconds())) * factor, timeNoPulse]
    except ZeroDivisionError:
        return [0, 0]


def getFlux(startDT):
    endDT = startDT + timedelta(minutes=60)

    pulseCount = 0
    lastDt = startDT
    timeNoPulse = 0  # in seconds

    for l in fileLines:

        line = l.rstrip()
        m = re.match("(.* 2017)(.*)", line)
        if m:
            curDt = datetime.strptime(m.group(1), "%b %d %H:%M:%S %Y")
            if startDT <= curDt and curDt <= endDT:
                try:
                    curCount = int(m.group(2))
                except ValueError:
                    continue  # Ignore line in case it contain "Start of test"

                if curCount <= 0:  # diffCount <= 0 or lastCount <= 0:
                    timeNoPulse += (curDt - lastDt).total_seconds()
                else:
                    pulseCount += curCount
                lastDt = curDt
            elif curDt > endDT:
                try:
                    # return [(pulseCount*getWenderFactor(startDT)/(60*60 -timeNoPulse))*factor, timeNoPulse]
                    return [(pulseCount * getWenderFactor(startDT) / (60 * 60)) * factor, timeNoPulse]
                except ZeroDivisionError:
                    return [0, 0]


#########################################################
#                    Main Thread                        #
#########################################################
if len(sys.argv) < 4:
    print "Usage: %s <lansce pulse log file> <csv file> <factor>" % (sys.argv[0])
    sys.exit(1)

inFileName = sys.argv[1]
csvFileName = sys.argv[2]
factor = float(sys.argv[3])

csvOutFileName = csvFileName.replace(".csv", "_cross_section_fission.csv")

print "in: " + csvFileName
print "out: " + csvOutFileName

csvFP = open(csvFileName, "r")
reader = csv.reader(csvFP, delimiter=';')
csvWFP = open(csvOutFileName, "w")
writer = csv.writer(csvWFP, delimiter=';')

##################summary
csvWFP2 = open("summaries-fission.csv", "a")
writer2 = csv.writer(csvWFP2, delimiter=';')
writer2.writerow([])
writer2.writerow([csvFileName])
headerW2 = ["start timestamp", "end timestamp", "benchmark", "header detail", "#lines computed", "#SDC", "#AccTime",
            "#(Abort==0)"]
headerW2.append("Flux 1h (factor " + str(factor) + ")")
headerW2.append("Flux AccTime (factor " + str(factor) + ")")
headerW2.append("Fluence(Flux * $AccTime)")
headerW2.append("Fluence AccTime(FluxAccTime * $AccTime)")
headerW2.append("Cross Section SDC")
headerW2.append("Cross Section Crash")
headerW2.append("Time No Neutron Count (sec)")
headerW2.append("Cross Section SDC AccTime")
headerW2.append("Cross Section Crash AccTime")
headerW2.append("Time No Neutron Count AccTime (sec)")
writer2.writerow(headerW2)
##################

csvHeader = next(reader, None)

writer.writerow(csvHeader)

lines = list(reader)

# We need to read the neutron count files before calling getFluenceFlux
readFissionFile()

i = 0
size = len(lines)
while i < size:
    if re.match("Time", lines[i][0]):
        i += 1

    progress = "{0:.2f}".format(((float(i) / float(size)) * 100.0))
    sys.stdout.write("\rProcessing Line " + str(i) + " of " + str(size) + " - " + progress + "%")
    sys.stdout.flush()

    startDT = datetime.strptime(lines[i][0][0:-1], "%c")
    endDT1h = startDT
    ##################summary
    benchmark = lines[i][2]
    inputDetail = lines[i][3]
    ##################
    # print "date in line "+str(i)+": ",startDT
    j = i
    accTimeS = float(lines[i][6])
    sdcS = int(lines[i][4])
    abortZeroS = 0
    if (int(lines[i][7]) == 0):
        abortZeroS += 1
    writer.writerow(lines[i])
    if i + 1 < size:
        try:
            if re.match("Time", lines[i + 1][0]):
                i += 1
            if i + 1 < size:
                while ((datetime.strptime(lines[i + 1][0][0:-1], "%c") - startDT) < timedelta(minutes=60)):
                    progress = "{0:.2f}".format(((float(i) / float(size)) * 100.0))
                    sys.stdout.write("\rProcessing Line " + str(i) + " of " + str(size) + " - " + progress + "%")
                    sys.stdout.flush()

                    if (lines[i + 1][2] != lines[i][2]):  # not the same benchmark
                        break
                    if (lines[i + 1][3] != lines[i][3]):  # not the same input
                        break
                    # print "line "+str(i)+" inside 1h interval"
                    i += 1
                    ##################summary
                    endDT1h = datetime.strptime(lines[i][0][0:-1], "%c")
                    ##################
                    accTimeS += float(lines[i][6])
                    sdcS += int(lines[i][4])
                    if (int(lines[i][7]) == 0):
                        abortZeroS += 1
                    writer.writerow(lines[i])
                    if i == (len(lines) - 1):  # end of lines
                        break
                    if re.match("Time", lines[i + 1][0]):
                        i += 1
                    if i == (len(lines) - 1):  # end of lines
                        break
        except ValueError as e:
            print "date conversion error, detail: " + str(e)
            print "date: " + lines[i + 1][0][0:-1] + "\n"
    # compute 1h flux; sum SDC, ACC_TIME, Abort with 0; compute fluence (flux*(sum ACC_TIME))
    flux, timeBeamOff = getFlux(startDT)
    fluence = flux * accTimeS
    fluxAccTime, timeBeamOffAccTime = getFluenceFlux(startDT, (startDT + timedelta(seconds=accTimeS)))
    fluenceAccTime = fluxAccTime * accTimeS
    if fluence > 0:
        crossSection = sdcS / fluence
        crossSectionCrash = abortZeroS / fluence
    else:
        crossSection = 0
        crossSectionCrash = 0
    if fluenceAccTime > 0:
        crossSectionAccTime = sdcS / fluenceAccTime
        crossSectionCrashAccTime = abortZeroS / fluenceAccTime
    else:
        crossSectionAccTime = 0
        crossSectionCrashAccTime = 0
    headerC = ["start timestamp", "end timestamp", "#lines computed", "#SDC", "#AccTime", "#(Abort==0)"]
    headerC.append("Flux 1h (factor " + str(factor) + ")")
    headerC.append("Flux AccTime (factor " + str(factor) + ")")
    headerC.append("Fluence(Flux * $AccTime)")
    headerC.append("Fluence AccTime(FluxAccTime * $AccTime)")
    headerC.append("Cross Section SDC")
    headerC.append("Cross Section Crash")
    headerC.append("Time No Neutron Count (sec)")
    headerC.append("Cross Section SDC AccTime")
    headerC.append("Cross Section Crash AccTime")
    headerC.append("Time No Neutron Count AccTime (sec)")
    writer.writerow(headerC)
    row = [startDT.ctime(), endDT1h.ctime(), (i - j + 1), sdcS, accTimeS, abortZeroS, flux, fluxAccTime, fluence,
           fluenceAccTime, crossSection, crossSectionCrash, timeBeamOff, crossSectionAccTime, crossSectionCrashAccTime,
           timeBeamOffAccTime]
    # row = [startDT.ctime(), (i-j+1), sdcS, accTimeS, abortZeroS]
    writer.writerow(row)
    writer.writerow([])
    writer.writerow([])
    ##################summary
    row2 = [startDT.ctime(), endDT1h.ctime(), benchmark, inputDetail, (i - j + 1), sdcS, accTimeS, abortZeroS, flux,
            fluxAccTime, fluence, fluenceAccTime, crossSection, crossSectionCrash, timeBeamOff, crossSectionAccTime,
            crossSectionCrashAccTime, timeBeamOffAccTime]
    # row2 = [startDT.ctime(),endDT1h.ctime(),benchmark,inputDetail, (i-j+1), sdcS, accTimeS, abortZeroS]
    writer2.writerow(row2)
    ##################
    i += 1

progress = "{0:.2f}".format(((float(i) / float(size)) * 100.0))
sys.stdout.write("\rProcessing Line " + str(i) + " of " + str(size) + " - " + progress + "%")
sys.stdout.flush()
sys.stdout.write("\nDone\n")

csvFP.close()
csvWFP.close()

sys.exit(0)
