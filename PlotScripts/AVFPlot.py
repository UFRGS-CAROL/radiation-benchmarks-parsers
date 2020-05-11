#!/usr/bin/env python
import csv
import os
import re
import sys

import matplotlib.pyplot as plt
import numpy as np

full_path = "/home/fernando/temp/hpca_fi"


def check_crash_sdc(log_file, check_detected=None):
    sdc, crash = False, True
    detected = False
    false_positive = False

    with open(log_file) as lf:
        lines = lf.readlines()

        for line in lines:
            if "SDC" in line:
                sdc = True
            if "END" in line:
                crash = False

        for line in lines:
            if check_detected in line:
                detected = True

    if sdc is False and detected is True:
        false_positive = True
        detected = False

    return sdc, crash, detected, false_positive


def avf(carol_fi_path, check_detected=None):
    log_path = carol_fi_path + "/var/radiation-benchmarks/log/"
    dir_list = os.listdir(log_path)
    sdc_avf = 0.0
    due_avf = 0.0

    faults = float(len(dir_list))
    detected_avf = 0.0
    for log_file in dir_list:
        sdc, crash, detected, false_positive = check_crash_sdc(log_path + log_file, check_detected)

        if sdc and (detected is False):
            sdc_avf += 1.0 / faults
        if crash:
            due_avf += 1.0 / faults

        if detected:
            detected_avf += 1.0 / faults

    return sdc_avf, due_avf, detected_avf


def avf_csv(carol_fi_path, check_detected, benchmark):
    csv_file = carol_fi_path + "/fi_micro_{}_dmrmixed_double_single_bit.csv".format(benchmark.lower())
    log_path = carol_fi_path + "/var/radiation-benchmarks/log/"

    sdc_avf = 0.0
    due_avf = 0.0
    detected_avf = 0.0
    faults = 0.0
    falses_positives = 0.0
    with open(csv_file) as fp:
        csv_reader = csv.DictReader(fp)

        for row in csv_reader:
            faults += 1.0
            sdc, crash, detected, false_positive = check_crash_sdc(log_path + row['log_file'], check_detected)

            if sdc and (detected is False):
                sdc_avf += 1.0
            if crash:
                due_avf += 1.0

            if detected:
                detected_avf += 1.0

            if false_positive:
                falses_positives += 1.0

    return sdc_avf, due_avf, detected_avf, faults, falses_positives


def avf_microbenchmarks():
    csv_files = [
        # "fi_micro_add_dmrmixed_double_single_bit_1000/",
        # "fi_micro_add_dmrmixed_double_single_bit_10/",
        # "fi_micro_add_dmrmixed_double_single_bit_1/",
        # "fi_micro_add_dmrmixed_double_single_bit_100/",
        #
        "fi_micro_mul_dmrmixed_double_single_bit_100/",
        "fi_micro_mul_dmrmixed_double_single_bit_10/",
        "fi_micro_mul_dmrmixed_double_single_bit_1000/",
        "fi_micro_mul_dmrmixed_double_single_bit_1/",
        #
        # "fi_micro_fma_dmrmixed_double_single_bit_100/",
        # "fi_micro_fma_dmrmixed_double_single_bit_1/",
        # "fi_micro_fma_dmrmixed_double_single_bit_10/",
        # "fi_micro_fma_dmrmixed_double_single_bit_1000/",
        #
        # "fi_micro_addnotbiased_dmrmixed_double_single_bit_0/", "fi_micro_addnotbiased_dmrmixed_double_single_bit_100/",
        # "fi_micro_addnotbiased_dmrmixed_double_single_bit_1/", "fi_micro_addnotbiased_dmrmixed_double_single_bit_1000/",
        # "fi_micro_mulnotbiased_dmrmixed_double_single_bit_0/", "fi_micro_mulnotbiased_dmrmixed_double_single_bit_100/",
        # "fi_micro_mulnotbiased_dmrmixed_double_single_bit_1/", "fi_micro_mulnotbiased_dmrmixed_double_single_bit_1000/",
        # "fi_micro_fmanotbiased_dmrmixed_double_single_bit_0/", "fi_micro_fmanotbiased_dmrmixed_double_single_bit_100/",
        # "fi_micro_fmanotbiased_dmrmixed_double_single_bit_1/", "fi_micro_fmanotbiased_dmrmixed_double_single_bit_1000/"
    ]
    avf_dict = {"ADD": {}, "MUL": {}, "FMA": {}}
    for csv_path in csv_files:
        print(csv_path)
        m = re.match(".*fi_micro_(\S+)_dmrmixed_double_single_bit_(\d+)/.*",
                     csv_path)

        micro_name = str(m.group(1)).upper()
        check_block = m.group(2)
        if "0" == m.group(2):
            check_block = "1MB"
        # key = micro_name + " " + check_block

        full_csv_path = full_path + "/" + csv_path
        sdc_avf, due_avf, detected_avf, fault_num, false_positive = avf_csv(carol_fi_path=os.path.dirname(full_csv_path),
                                                 benchmark=micro_name, check_detected="detected")
        masked_avf = fault_num - (sdc_avf + due_avf + detected_avf)

        print(sdc_avf, due_avf, detected_avf, masked_avf, sdc_avf + due_avf + detected_avf + masked_avf)

        # sdc_avf_list.append(sdc_avf)
        # due_avf_list.append(due_avf)
        # masked_avf_list.append(masked_avf)
        # detected_avf_list.append(detected_avf)
        avf_dict[micro_name][check_block] = {"sdc": sdc_avf, "due": due_avf, "detected": detected_avf,
                                             "masked": masked_avf, "fault_num": fault_num, "false_positive": false_positive}
    return avf_dict


def avf_hotspot():
    csv_files = [
        # "fi_hotspot_mp_dmrmixed_double_single_bit_0/",
        #  "fi_hotspot_mp_dmrmixed_double_single_bit_1/",
        # "fi_hotspot_mp_dmrmixed_double_single_bit_2/",
        # "fi_hotspot_mp_dmrmixed_double_single_bit_4/"
        # "fi_hotspot_mp_dmrmixed_double_single_bit_6/",

    ]

    avf_dict = {}
    for csv_path in csv_files:
        print(csv_path)
        m = re.match(".*fi_hotspot_mp_dmrmixed_double_single_bit_(\d+)/.*",
                     csv_path)

        check_block = m.group(1)
        if "0" == m.group(1):
            check_block = "10"
        # key = micro_name + " " + check_block

        full_csv_path = full_path + "/" + csv_path
        sdc_avf, due_avf, detected_avf = avf(carol_fi_path=os.path.dirname(full_csv_path), check_detected="detected")
        masked_avf = 1.0 - (sdc_avf + due_avf + detected_avf)

        print(sdc_avf, due_avf, detected_avf, masked_avf, sdc_avf + due_avf + detected_avf + masked_avf)

        # sdc_avf_list.append(sdc_avf)
        # due_avf_list.append(due_avf)
        # masked_avf_list.append(masked_avf)
        # detected_avf_list.append(detected_avf)
        avf_dict[check_block] = {"sdc": sdc_avf, "due": due_avf, "detected": detected_avf,
                                 "masked": masked_avf}
    return avf_dict


def write_to_csv(avf_dict, output_csv):
    with open(output_csv, "w") as fp:
        header = "micro;check;sdc;detected;due;masked;fault_num;false_positive".split(";")

        csv_writer = csv.DictWriter(fp, fieldnames=header, delimiter=";")
        csv_writer.writeheader()
        for micro_name in avf_dict:
            for check in avf_dict[micro_name]:
                out_dict = {"micro": micro_name, "check": check}
                out_dict.update(avf_dict[micro_name][check])
                csv_writer.writerow(out_dict)

def avf_gemm():
    csv_files = [
        "fi_gemm_tensorcores_dmrmixed_double_single_bit_0/"
    ]
    avf_dict = {"GEMM_TENSORCORES": {}}
    for csv_path in csv_files:
        print(csv_path)
        m = re.match(".*fi_(\S+)_dmrmixed_double_single_bit_(\d+)/.*",
                     csv_path)

        micro_name = str(m.group(1)).upper()
        check_block = m.group(2)
        if "0" == m.group(2):
            check_block = "32it"
        # key = micro_name + " " + check_block

        full_csv_path = full_path + "/" + csv_path
        sdc_avf, due_avf, detected_avf = avf(carol_fi_path=os.path.dirname(full_csv_path), check_detected="detected")
        masked_avf = 1.0 - (sdc_avf + due_avf + detected_avf)

        print(sdc_avf, due_avf, detected_avf, masked_avf, sdc_avf + due_avf + detected_avf + masked_avf)

        # sdc_avf_list.append(sdc_avf)
        # due_avf_list.append(due_avf)
        # masked_avf_list.append(masked_avf)
        # detected_avf_list.append(detected_avf)
        avf_dict[micro_name][check_block] = {"sdc": sdc_avf, "due": due_avf, "detected": detected_avf,
                                             "masked": masked_avf}
    return avf_dict


def main():
    try:
        output_dir = sys.argv[1]
    except:
        output_dir = "."

    # AVF MICROBENCHMARKS
    avf_dict = avf_microbenchmarks()
    write_to_csv(avf_dict, "./{}".format("output_micro.csv"))

    # AVF HOTSPOT
    # avf_dict = avf_hotspot()
    # write_to_csv({"hotspot": avf_dict}, "./{}".format("output_hotspot.csv"))

    # AVF GEMM
    # avf_dict = avf_gemm()
    # write_to_csv(avf_dict, "./{}".format("output_gemm.csv"))


if __name__ == '__main__':
    main()
