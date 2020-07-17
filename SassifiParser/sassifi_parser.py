#!/usr/bin/env python3.6

import pandas as pd
from sys import argv

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
    RF_MODE: "RF"
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


def check_sdc(log_file):
    global logs_dir
    with open(logs_dir + "/" + log_file) as fp:
        return 1 if any("SDC" in s for s in fp.readlines()) else 0


def check_due(log_file):
    global logs_dir
    with open(logs_dir + "/" + log_file) as fp:
        return 0 if any("END" in s for s in fp.readlines()) else 1


def check_nvdue(log_file):
    global logs_dir
    with open(logs_dir + "/" + log_file) as fp:
        return 1 if any("CUDA Framework error" in s for s in fp.readlines()) else 0


def main():
    global logs_dir
    input_csv = argv[1]
    logs_dir = argv[2]

    avf_df = pd.read_csv(input_csv, header=None)
    avf_df.columns = ["logfile", "has_sdc", "kname", "kcount", "igid",
                      "bfm", "iid", "opid", "bid", "has_end", "sdc_caught"]
    avf_df["#sdc"] = avf_df["logfile"].apply(check_sdc)
    avf_df["#due"] = avf_df["logfile"].apply(check_due)
    avf_df["#nvdue"] = avf_df["logfile"].apply(check_nvdue)
    avf_df["igid"] = avf_df["igid"].apply(lambda r: inst_value_igid_bfm_map[r.strip() if type(r) == str else r])
    avf_per_igid = avf_df.groupby(["igid"]).sum()[["#sdc", "#due", "#nvdue"]]
    avf_per_igid["#faults"], _ = avf_df.shape
    avf_per_igid["AVF SDC"] = avf_per_igid["#sdc"] / avf_per_igid["#faults"]
    avf_per_igid["AVF DUE"] = avf_per_igid["#due"] / avf_per_igid["#faults"]
    avf_per_igid["AVF NVDUE"] = avf_per_igid["#nvdue"] / avf_per_igid["#faults"]
    avf_per_igid.to_csv(input_csv.replace(".csv", "_avf.csv"))


if __name__ == '__main__':
    main()
