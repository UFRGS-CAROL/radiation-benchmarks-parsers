#!/usr/bin/python -u

import os
import sys
import re
import csv

from datetime import timedelta
from datetime import datetime

fileLines = list()


def get_dt(yearDate, dayTime, secFrac):
    yv = yearDate.split('/')
    day = int(yv[0])
    month = int(yv[1])
    year = int(yv[2])

    dv = dayTime.split(':')
    hour = int(dv[0])
    minute = int(dv[1])
    second = int(dv[2])

    # we get secFrac in seconds, so we must convert to microseconds
    # e.g: 0.100 seconds = 100 milliseconds = 100000 microseconds
    microsecond = int(float(secFrac) * 1e6)

    return datetime(year, month, day, hour, minute, second, microsecond)


def read_count_file():
    inFile = open(inFileName, 'r')
    global fileLines
    for l in inFile:

        # Sanity check, we require a date at the beginning of the line
        line = l.rstrip()
        if not re.match("\d{1,2}/\d{1,2}/\d{2,4}", line):
            # sys.stderr.write("Ignoring line (malformed):\n%s\n" % (line))
            continue

        if "N/A" in line:
            break

        fileLines.append(line)


def get_fluence_flux(startDT, endDT):
    # inFile = open(inFileName, 'r')
    # endDT = startDT + timedelta(minutes=60)

    last_counter_20 = 0
    last_counter_30 = 0
    last_counter_40 = 0
    last_curIntegral = 0
    lastDT = None
    flux1h = 0
    beamOffTime = 0
    first_curIntegral = None

    # for l in inFile:
    for l in fileLines:

        ## Sanity check, we require a date at the beginning of the line
        line = l.rstrip()
        # if not re.match("\d{1,2}/\d{1,2}/\d{2,4}", line):
        #	#sys.stderr.write("Ignoring line (malformed):\n%s\n" % (line))
        #	continue
        #
        # if "N/A" in line:
        #    break
        #
        ## Parse the line
        lv = line.split(';')

        yearDate = lv[0]
        dayTime = lv[1]
        secFrac = lv[2]
        counter_40 = lv[3]
        counter_20 = lv[4]
        counter_30 = lv[5]
        fission_counter = lv[6]
        curIntegral = lv[7]
        current = lv[8]

        # Generate datetime for line
        curDt = get_dt(yearDate, dayTime, secFrac)

        if startDT <= curDt and first_curIntegral is None:
            first_curIntegral = float(curIntegral)
            last_counter_20 = counter_20
            last_counter_30 = counter_30
            last_counter_40 = counter_40
            lastDT = curDt
            continue

        if first_curIntegral is not None:
            if counter_30 == last_counter_30:
                shutter = "Closed"
                beamOffTime += (curDt - lastDT).total_seconds()
            else:
                shutter = "Open"
            last_counter_20 = counter_20
            last_counter_30 = counter_30
            last_counter_40 = counter_40
            lastDT = curDt

        if curDt > endDT:
            flux1h = (float(last_curIntegral) - first_curIntegral) / (endDT - startDT).total_seconds()
            return [flux1h, beamOffTime]
        elif first_curIntegral is not None:
            last_curIntegral = curIntegral


#########################################################
#                    Main Thread                        #
#########################################################
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print "Usage: %s <neutron counts input file> <csv file> <factor>" % (sys.argv[0])
        sys.exit(1)

    inFileName = sys.argv[1]
    csv_file_name = sys.argv[2]
    factor = float(sys.argv[3])

    csv_out_fileName = csv_file_name.replace(".csv", "_cross_section.csv")
    csvOutFileName2 = csv_file_name.replace(".csv", "_cross_section_summary.csv")

    print "in: " + csv_file_name
    print "out: " + csv_out_fileName

    with open(csv_file_name, "r") as csv_FP, open(csv_out_fileName, "w") as csv_WFP, open(csvOutFileName2,
                                                                                          "w") as csv_WFP2:
        reader = csv.reader(csv_FP, delimiter=';')
        writer = csv.writer(csv_WFP, delimiter=';')
        writer2 = csv.writer(csv_WFP2, delimiter=';')

        csv_header = next(reader, None)

        writer.writerow(csv_header)
        writer2.writerow(csv_header)

        lines = [i for i in reader]

        # We need to read the neutron count files before calling get_fluence_flux
        read_count_file()
        for i in range(0, len(lines)):
            print lines[i][0]
            print lines[i][0][0:-1]
            start_dt = datetime.strptime(lines[i][0][0:-1], "%c")
            print "date in line " + str(i) + ": ", start_dt
            j = i
            acc_time_s = float(lines[i][6])
            sdcS = int(lines[i][4])
            abort_zero_s = 0
            if int(lines[i][7]) == 0:
                abort_zero_s += 1
            writer.writerow(lines[i])
            writer2.writerow(lines[i])
            end_dt = datetime.strptime(lines[i + 1][0][0:-1], "%c")
            lastLine = ""
            while (end_dt - start_dt) < timedelta(minutes=60):
                if lines[i + 1][2] != lines[i][2]:  # not the same benchmark
                    break
                if lines[i + 1][3] != lines[i][3]:  # not the same input
                    break
                # print "line "+str(i)+" inside 1h interval"
                i += 1
                acc_time_s += float(lines[i][6])
                sdcS += int(lines[i][4])
                if int(lines[i][7]) == 0:
                    abort_zero_s += 1
                writer.writerow(lines[i])
                lastLine = lines[i]
                if i == (len(lines) - 1):  # end of lines
                    break
                end_dt = datetime.strptime(lines[i + 1][0][0:-1], "%c")
            # compute 1h flux; sum SDC, ACC_TIME, Abort with 0; compute fluence (flux*(sum ACC_TIME))
            flux, time_beam_off = get_fluence_flux(start_dt, (start_dt + timedelta(minutes=60)))
            flux_acc_time, time_beam_off_acc_time = get_fluence_flux(start_dt,
                                                                     (start_dt + timedelta(seconds=acc_time_s)))
            fluence = flux * acc_time_s
            fluence_acc_time = flux_acc_time * acc_time_s
            if fluence > 0:
                cross_section = sdcS / fluence
                cross_section_crash = abort_zero_s / fluence
            else:
                cross_section = 0
                cross_section_crash = 0
            if fluence_acc_time > 0:
                cross_section_acc_time = sdcS / fluence_acc_time
                cross_section_crash_acc_time = abort_zero_s / fluence_acc_time
            else:
                cross_section_acc_time = 0
                cross_section_crash_acc_time = 0
            header_c = ["start timestamp", "end timestamp", "#lines computed", "#SDC", "#AccTime", "#(Abort==0)",
                        "Flux 1h (factor " + str(factor) + ")", "Flux AccTime (factor " + str(factor) + ")",
                        "Fluence(Flux * $AccTime)", "Fluence AccTime(FluxAccTime * $AccTime)", "Cross Section SDC",
                        "Cross Section Crash", "Time Beam Off (sec)", "Cross Section SDC AccTime",
                        "Cross Section Crash AccTime", "Time Beam Off AccTime (sec)"]
            writer.writerow(header_c)
            writer2.writerow(lastLine)
            writer2.writerow(header_c)
            row = [start_dt.ctime(), end_dt.ctime(), (i - j + 1), sdcS, acc_time_s, abort_zero_s, flux, flux_acc_time,
                   fluence,
                   fluence_acc_time, cross_section, cross_section_crash, time_beam_off, cross_section_acc_time,
                   cross_section_crash_acc_time,
                   time_beam_off_acc_time]
            writer.writerow(row)
            writer2.writerow(row)
            writer.writerow([])
            writer.writerow([])
            writer2.writerow([])
            writer2.writerow([])
