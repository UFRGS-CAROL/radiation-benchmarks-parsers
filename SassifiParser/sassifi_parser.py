#!/usr/bin/env python3.6


import csv
import sys

#######################################################################
# Three injection modes
#######################################################################
RF_MODE = "rf"
INST_VALUE_MODE = "inst_value"
INST_ADDRESS_MODE = "inst_address"

#######################################################################
# Categories of instruction types (IGIDs): This should match the values set in
# err_injector/error_injector.h.
#######################################################################

GPR = 0
CC = 1
PR = 2
STORE_OP = 3
IADD_IMUL_OP = 4
FADD_FMUL_OP = 5
DADD_DMUL_OP = 6
MAD_OP = 7
FFMA_OP = 8
DFMA_OP = 9
SETP_OP = 10
LDS_OP = 11
LD_OP = 12
MISC_OP = 13
NUM_INST_TYPES = 14

FLIP_SINGLE_BIT = 0
FLIP_TWO_BITS = 1
RANDOM_VALUE = 2
ZERO_VALUE = 3
WARP_FLIP_SINGLE_BIT = 4
WARP_FLIP_TWO_BITS = 5
WARP_RANDOM_VALUE = 6
WARP_ZERO_VALUE = 7

error_mode_map = {
    FLIP_SINGLE_BIT: "FLIP_SINGLE_BIT",
    FLIP_TWO_BITS: "FLIP_TWO_BITS",
    RANDOM_VALUE: "RANDOM_VALUE",
    ZERO_VALUE: "ZERO_VALUE",
    WARP_FLIP_SINGLE_BIT: "WARP_FLIP_SINGLE_BIT",
    WARP_FLIP_TWO_BITS: "WARP_FLIP_TWO_BITS",
    WARP_RANDOM_VALUE: "WARP_RANDOM_VALUE",
    WARP_ZERO_VALUE: "WARP_ZERO_VALUE"
}

rf_igid_bfm_map = {0: "RF"}

inst_value_igid_bfm_map = {
    GPR: "GPR",
    CC: "CC",
    PR: "PR",
    STORE_OP: "STORE_OP",
    IADD_IMUL_OP: "IADD_IMUL_OP",
    FADD_FMUL_OP: "FADD_FMUL_OP",
    DADD_DMUL_OP: "DADD_DMUL_OP",
    MAD_OP: "MAD_OP",
    FFMA_OP: "FFMA_OP",
    DFMA_OP: "DFMA_OP",
    SETP_OP: "SET_OP",
    LDS_OP: "LDS_OP",
    LD_OP: "LD_OP",
}

# Used for instruction output-level address injection runs
inst_address_igid_bfm_map = {
    #  Supported models
    GPR: "GPR",
    STORE_OP: "STORE_OP",
}


def check_sdc_due_nvdue(log_file):
    sdc = 0
    due = 1
    nvdue = 0
    with open(log_file) as fp:
        lines = fp.readlines()
        for line in lines:
            if "SDC" in line:
                sdc = 1

            if "CUDA Framework error" in line:
                nvdue = 1

            if "END" in line:
                due = 0

    return sdc, due, nvdue


def main(arg_list):
    csv_input, log_path, inst_type = arg_list
    map_to_use = {"rf": rf_bfm_map, "inst_value": inst_value_igid_bfm_map, "inst_address": inst_address_igid_bfm_map}

    igid_map = map_to_use[inst_type]
    sdc_num_per_inst = {i: 0.0 for i in igid_map}
    due_num_per_inst = {i: 0.0 for i in igid_map}
    nvdue_num_per_inst = {i: 0.0 for i in igid_map}

    sdc_saturation = []

    with open(csv_input) as csv_log_fp:
        reader = csv.reader(csv_log_fp)

        n_faults = 0.0
        sdc_it = 0.0
        for [log_file, has_sdc, kname, kcount, igid, bfm, iid, opid, bid, has_end, sdc_caught] in reader:
            log_file_path = log_path + "/" + log_file
            sdc, due, nvdue = check_sdc_due_nvdue(log_file=log_file_path)
            n_faults += 1.0
            sdc_it += float(sdc)
            sdc_saturation.append(sdc_it / n_faults)
            key = int(igid)
            sdc_num_per_inst[key] += float(sdc)
            due_num_per_inst[key] += float(due)
            nvdue_num_per_inst[key] += float(nvdue)

        output_csv_name = csv_input.replace(".csv", "_avf.csv")
        with open(output_csv_name, "w") as out_f:
            writer = csv.writer(out_f)
            writer.writerow(["instruction", "#sdc", "#due", "#nvdue", "#faults", "AVF SDC", "AVF DUE", "AVF NVDUE"])
            for key, value in igid_map.items():
                sdc_num = sdc_num_per_inst[key]
                due_num = due_num_per_inst[key]
                nvdue_num = nvdue_num_per_inst[key]

                sdc_avf = sdc_num / n_faults
                due_avf = due_num / n_faults
                nvdue_avf = nvdue_num / n_faults
                line = [value, sdc_num, due_num, nvdue_num, n_faults, sdc_avf, due_avf, nvdue_avf]
                writer.writerow(line)


if __name__ == '__main__':
    main(sys.argv[1:])
