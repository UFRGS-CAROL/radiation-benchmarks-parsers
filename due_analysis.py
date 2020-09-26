#!/usr/bin/env python3.6
import pandas as pd
import os
import re
from glob import glob
import threading


def check_arch(hostname):
    hostname_upper_case = hostname.upper()
    volta_boards = ["V100", "TITANV", "TITANX"]
    kepler_boards = ["K20", "K40"]
    if any([v for v in volta_boards if v in hostname_upper_case]):
        return "VOLTA"
    elif any([k for k in kepler_boards if k in hostname_upper_case]):
        return "KEPLER"
    else:
        return None


def get_crash_motivation(log_file):
    with open(log_file) as fp:
        lines = fp.readlines()
        if len(lines) == 0:
            return "system crash"
        motivation = "no crash" if "END" in lines[-1] else "system crash"
        pattern_framework = ".*CUDA Framework error:(.*)Bailing.*"
        pattern_abort = ".*ABORT (.*)"

        for line in lines:
            m = re.match(pattern=pattern_framework, string=line)
            if m:
                motivation = m.group(1).strip().replace(".", "")
                break

            m = re.match(pattern=pattern_abort, string=line)
            if m:
                motivation = m.group(1)
                break
    return motivation


def parse_test_due(base_path, base_dir, analysis_path, thread_id):
    directory = base_dir + "/" + base_path
    print(f"Parsing {base_path} at thread {thread_id}")
    all_logs = [y for x in os.walk(directory) for y in glob(os.path.join(x[0], '*.log'))]
    dir_test_dict = {}
    for log in all_logs:
        # 2019_10_07_22_03_12_cuda_single_lava_ECC_OFF_carolk201.log
        m = re.match(r".*/(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(\d+)_(.*)_(.*).log", log)
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
    # Get all due motivation to generate the reader
    df = pd.DataFrame(dir_test_dict).fillna(0)
    df.to_csv(csv_path)


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

    analysis_path = "/home/fernando/Dropbox/temp/profile_files/csvs_files/due_analysis_files/"
    os.system("mkdir -p " + analysis_path)
    threads = []
    for thread_id, base_path in enumerate(database):
        th = threading.Thread(target=parse_test_due, args=(base_path, base_dir, analysis_path, thread_id))
        threads.append(th)
        th.start()

    for th in threads:
        th.join()


if __name__ == '__main__':
    main()
