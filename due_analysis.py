#!/usr/bin/env python3.6
import csv
import os
import re
from glob import glob
import threading


def check_arch(hostname):
    hostname_upper_case = hostname.upper()
    volta_boards = ["V100", "TITANV", "TITANX"]
    kepler_boards = ["K20", "K40"]
    for v in volta_boards:
        if v in hostname_upper_case:
            return "VOLTA"
    for k in kepler_boards:
        if k in hostname_upper_case:
            return "KEPLER"


def get_crash_motivation(log_file):
    motivation = "no crash"
    has_end = False
    pattern = ".*CUDA Framework error:(.*)Bailing.*"
    with open(log_file) as fp:
        lines = fp.readlines()
        for line in lines:
            if "CUDA" in line:
                m = re.match(pattern=pattern, string=line)
                if m:
                    motivation = m.group(1)
                    motivation = motivation.strip().replace(".", "")
            if "END" in line:
                has_end = True

            # if "ABORT" in line:
            #     pattern = ".*ABORT (.*)"
            #     m = re.match(pattern=pattern, string=line)
            #     if m:
            #         motivation = m.group(1)

    if motivation == "no crash" and has_end is False:
        motivation = "system crash"
    return motivation


def parse_test_due(base_path, base_dir, analysis_path):
    directory = base_dir + "/" + base_path
    print("Parsing {}".format(base_path))
    all_logs = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*.log'))]
    dir_test_dict = {}
    for log in all_logs:

        # 2019_10_07_22_03_12_cuda_single_lava_ECC_OFF_carolk201.log
        m = re.match(".*/(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)_(.*).log", log)
        if m:
            benchmark = m.group(7)
            machine_name = m.group(8)

            arch = check_arch(machine_name)
            if arch:
                key = "{}_{}".format(arch, benchmark)
                if key not in dir_test_dict:
                    dir_test_dict[key] = {}

                due_motivation = get_crash_motivation(log_file=log)
                if due_motivation not in dir_test_dict[key]:
                    dir_test_dict[key][due_motivation] = 0
                dir_test_dict[key][due_motivation] += 1
    csv_path = analysis_path + base_path + ".csv"
    with open(csv_path, "w") as csv_file:
        writer = csv.writer(csv_file)

        # Get all due motivation to generate the reader
        due_motivation_list = list(set(d for k in dir_test_dict for d in dir_test_dict[k]))
        header = ["arch", "benchmark", "all_due"] + due_motivation_list
        writer.writerow(header)

        for key in dir_test_dict:
            arch, benchmark = key.split("_", maxsplit=1)
            all_due = sum([dir_test_dict[key][x] for x in dir_test_dict[key]])
            line = [arch, benchmark, all_due]
            for d in due_motivation_list:
                try:
                    line.append(dir_test_dict[key][d])
                except KeyError:
                    line.append(0)

            writer.writerow(line)


def main():
    # database
    base_dir = "/home/fernando/temp/all_tests"
    database = [
        "ChipIR062018",
        "LANSCE102018",
        "ChipIR022019",
        "LANSCE092019",
        "ChipIR102019",
        "ChipIR032020"
    ]

    analysis_path = "./due_analysis_files/"
    os.system("mkdir -p " + analysis_path)
    threads = []
    for base_path in database:
        th = threading.Thread(target=parse_test_due, args=(base_path, base_dir, analysis_path))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()


if __name__ == '__main__':
    main()
