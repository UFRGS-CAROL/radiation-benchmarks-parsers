#!/usr/bin/env python

import csv
import re
from datetime import timedelta, datetime
import os
from glob import glob

tmpDir = "/tmp/parserSDC/"
if not os.path.isdir(tmpDir):
    os.mkdir(tmpDir)
else:
    os.system("rm -r -f " + tmpDir + "*")

all_tar = [y for x in os.walk(".") for y in glob(os.path.join(x[0], '*.tar.gz'))]
for tar in all_tar:
    try:
        os.system("tar -xzf " + tar + " -C " + tmpDir)
    except:
        os.system("gzip -d " + tar + " -C " + tmpDir + "/temp_file.tar")
        os.system("tar -xf " + tmpDir + "/temp_file.tar" + " -C " + tmpDir)

all_logs_org = [y for x in os.walk(".") for y in glob(os.path.join(x[0], '*.log'))]
for logs in all_logs_org:
    os.system("cp " + logs + " " + tmpDir)

all_logs_tmp = [y for x in os.walk(tmpDir) for y in glob(os.path.join(x[0], '*.log'))]
for logs in all_logs_tmp:
    os.system("mv " + logs + " " + tmpDir)

machine_dict = dict()

header_csv = "Time;Machine;Benchmark;Header Info;#SDC;acc_err;acc_time;abort;end;framework_error;filename and dir"

total_sdc = 0

all_logs = [y for x in os.walk(tmpDir) for y in glob(os.path.join(x[0], '*.log'))]

all_logs.sort()

folder_p = "logs_parsed"

good_csv_files = list()

if not os.path.isdir(folder_p):
    os.mkdir(folder_p)

for fi in all_logs:

    m = re.match(".*/(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)_(.*).log", fi)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        sec = int(m.group(6))
        benchmark = m.group(7)
        machine_name = m.group(8)

        startDT = datetime(year, month, day, hour, minute, sec)

        lines = open(fi, "r")
        sdc = 0
        end = 0
        abort = 0
        acc_time = 0
        acc_err = 0
        cuda_framework_abort = 0
        header = "unknown"
        for line in lines:
            m = re.match(".*HEADER(.*)", line)
            if m:
                header = m.group(1)
                header.replace(";", "-")

            m = re.match(".*SDC.*", line)
            if m:
                sdc += 1
                total_sdc += 1

            m = re.match(".*AccTime:(\d+.\d+)", line)
            if m:
                acc_time = float(m.group(1))

            m = re.match(".*AccErr:(\d+)", line)
            if m:
                acc_err = int(m.group(1))

            m = re.match(".*ABORT.*", line)
            if m:
                abort = 1

            m = re.match(".*CUDA Framework error.*", line)
            if m:
                cuda_framework_abort = 1

            m = re.match(".*END.*", line)
            if m:
                end = 1

        good_file = './' + folder_p + '/logs_parsed_' + machine_name + '.csv'
        if good_file not in good_csv_files:
            good_csv_files.append(good_file)

        with open('./' + folder_p + '/logs_parsed_' + machine_name + '.csv', 'a') as fp, open(
                './' + folder_p + '/logs_parsed_problematics_' + machine_name + '.csv', 'a') as fp_problem:
            good_fp = csv.writer(fp, delimiter=';')  # , quotechar='|', quoting=csv.QUOTE_MINIMAL)
            problem_fp = csv.writer(fp_problem, delimiter=';')  # , quotechar='|', quoting=csv.QUOTE_MINIMAL)

            if machine_name not in machine_dict:
                machine_dict[machine_name] = 1
                good_fp.writerow(header_csv.split(";"))
                problem_fp.writerow(header_csv.split(";"))

                print("Machine first time: " + machine_name)

            if not re.match(".*sm.*", benchmark):
                row = [startDT.ctime(), machine_name, benchmark, header, sdc,
                       acc_err, acc_time, abort, end, cuda_framework_abort, fi]
                if header == "unknown" or acc_time == 0:
                    problem_fp.writerow(row)
                else:
                    good_fp.writerow(row)

print("\n\t\tTOTAL_SDC: ", total_sdc, "\n")

summariesFile = "./" + folder_p + "/summaries.csv"
os.system("rm -f " + summariesFile)

for csvFileName in good_csv_files:

    csvOutFileName = csvFileName.replace(".csv", "_summary.csv")

    print("in: " + csvFileName)
    print("out: " + csvOutFileName)

    # csvFP = open(csvFileName, "r")
    # csvWFP = open(csvOutFileName, "w")
    # csvWFP2 = open(summariesFile, "a") # summary
    with open(csvFileName, "r") as csvFP, open(csvOutFileName, "w") as csvWFP, open(summariesFile, "a") as csvWFP2:

        reader = csv.reader(csvFP, delimiter=';')
        writer = csv.writer(csvWFP, delimiter=';')
        writer2 = csv.writer(csvWFP2, delimiter=';')

        writer2.writerow([])
        writer2.writerow([csvFileName])
        headerW2 = ["start timestamp", "end timestamp", "benchmark", "header detail",
                    "#lines computed", "#SDC", "#AccTime",
                    "#(Abort==0 and END==0)", "framework_error"]
        writer2.writerow(headerW2)
        ##################

        csvHeader = next(reader, None)

        writer.writerow(csvHeader)

        lines = list(reader)

        i = 0
        size = len(lines)

        while i < size:
            if re.match("Time", lines[i][0]):
                i += 1

            startDT = datetime.strptime(lines[i][0].strip(), "%c")
            ##################summary
            benchmark = lines[i][2]
            inputDetail = lines[i][3]
            ##################
            # print "date in line "+str(i)+": ",startDT
            j = i
            accTimeS = float(lines[i][6])
            sdcS = int(lines[i][4])
            abortZeroS = 0
            frameworkErrors = 0

            if int(lines[i][7]) == 0:
                abortZeroS += 1
            writer.writerow(lines[i])
            if i + 1 < size:
                try:
                    if re.match("Time", lines[i + 1][0]):
                        i += 1
                    if i + 1 < size:

                        while startDT - datetime.strptime(lines[i + 1][0], "%c") < timedelta(minutes=60):
                            if i + 1 == size:
                                break
                            if lines[i + 1][2] != lines[i][2]:  # not the same benchmark
                                break
                            if lines[i + 1][3] != lines[i][3]:  # not the same input
                                break
                            i += 1
                            ##################summary
                            endDT1h = datetime.strptime(lines[i][0], "%c")
                            ##################
                            accTimeS += float(lines[i][6])
                            sdcS += int(lines[i][4])
                            if int(lines[i][7]) == 0 and int(lines[i][8]) == 0:
                                abortZeroS += 1

                            # CUDA framework errors
                            if int(lines[i][9]) == 1:
                                frameworkErrors += 1

                            writer.writerow(lines[i])
                            if i == (len(lines) - 1):  # end of lines
                                break
                            if re.match("Time", lines[i + 1][0]):
                                i += 1
                            if i == (len(lines) - 1):  # end of lines
                                break
                except ValueError as e:
                    print("date conversion error, detail: " + str(e))
                    print("date: " + lines[i + 1][0] + "\n")
            headerC = ["start timestamp", "#lines computed", "#SDC", "#AccTime",
                       "#(Abort==0 and END==0), CUDA Framework "
                       "errors"]
            writer.writerow(headerC)
            row = [startDT.ctime(), (i - j + 1), sdcS, accTimeS, abortZeroS, frameworkErrors]
            writer.writerow(row)
            writer.writerow([])
            writer.writerow([])
            ##################summary
            try:
                row2 = [startDT.ctime(), endDT1h.ctime(), benchmark, inputDetail, (i - j + 1), sdcS, accTimeS,
                        abortZeroS, frameworkErrors]
                writer2.writerow(row2)
            except Exception:
                pass
            ##################
            i += 1

    # csvFP.close()
    # csvWFP.close()

# os.system("rm -r -f "+tmpDir)
# sys.exit(0)