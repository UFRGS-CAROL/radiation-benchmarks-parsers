#!/usr/bin/env python3.6
import csv
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.ticker as mtick

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

IGID_STR = ["GPR", "CC", "PR", "STORE_OP",
            "IADD_IMUL_OP", "FADD_FMUL_OP", "DADD_DMUL_OP",
            "MAD_OP", "FFMA_OP", "DFMA_OP", "SETP_OP",
            "LDS_OP", "LD_OP", "MISC_OP"]

FLIP_SINGLE_BIT = 0
FLIP_TWO_BITS = 1
RANDOM_VALUE = 2
ZERO_VALUE = 3

WARP_FLIP_SINGLE_BIT = 4
WARP_FLIP_TWO_BITS = 5
WARP_RANDOM_VALUE = 6
WARP_ZERO_VALUE = 7

EM_STR = ["FLIP_SINGLE_BIT", "FLIP_TWO_BITS", "RANDOM_VALUE", "ZERO_VALUE",
          "WARP_FLIP_SINGLE_BIT", "WARP_FLIP_TWO_BITS", "WARP_RANDOM_VALUE", "WARP_ZERO_VALUE"]

# Used for instruction output-level value injection runs

rf_bfm_list = "RF"

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

DEFAULT_CSV_OUTPUT = "logs_sdcs_{}_inst_value.csv"


def check_sdc_due_nvdue(log_file, log_path):
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


def main():
    types_injected = {
        "mxm_inst_injection_mxm_256x256_1kfaults": "256",
        "mxm_inst_injection_mxm_512x512_1kfaults": "512",
        "mxm_inst_injection_mxm_1kx1k_1kfaults": "1024"
    }

    benchmarks_injected = ["gemm_tensorcores"]
    colors = {"256": "red", "512": "blue", "1024": "green"}

    sdc_avf_list = {}
    due_avf_list = {}

    final_df = {"size": [], "inst_type": [], "sdc_avf": [], "due_avf": []}

    for benchmark in benchmarks_injected:
        ax = plt.gca()

        for types_inj in types_injected:

            sdc_avf_per_inst = {inst_value_igid_bfm_map[i]: 0.0 for i in inst_value_igid_bfm_map}
            due_avf_per_inst = {inst_value_igid_bfm_map[i]: 0.0 for i in inst_value_igid_bfm_map}

            csv_log = types_inj + "/" + DEFAULT_CSV_OUTPUT.format(benchmark)
            sdc_saturation = []

            with open(csv_log) as csv_log_fp:
                reader = csv.reader(csv_log_fp)

                n_faults = 0.0
                sdc_it = 0.0
                for [logfilename, has_sdc, kname, kcount, igid, bfm, iid, opid, bid, has_end, sdc_caught] in reader:
                    n_faults += 1.0
                    sdc_it += float(has_sdc)
                    sdc_saturation.append(sdc_it / n_faults)
                    sdc_avf_per_inst[inst_value_igid_bfm_map[int(igid)]] += float(has_sdc)
                    due_avf_per_inst[inst_value_igid_bfm_map[int(igid)]] += 1.0 if int(has_end) == 0 else 0.0

                for i in inst_value_igid_bfm_map:
                    sdc_avf_per_inst[inst_value_igid_bfm_map[i]] /= n_faults
                    due_avf_per_inst[inst_value_igid_bfm_map[i]] /= n_faults

            sdc_avf_list[types_inj] = sdc_avf_per_inst
            due_avf_list[types_inj] = due_avf_per_inst

            this_df = pd.DataFrame(
                {"injection_num": [i for i in range(int(n_faults))], "sdc_variation": sdc_saturation})
            this_df.plot(kind='scatter', x='injection_num', y='sdc_variation',
                         color=colors[types_injected[types_inj]], ax=ax)

        ax.set_xlabel("num injections")
        ax.set_ylabel("AVF")
        ax.legend(["{}x{}".format(i, i) for i in colors])
        ax.set_title("Fault saturation MxM")
        plt.show()

    print("inst", ",", str([types_injected[i] for i in types_injected]).replace("[", "").replace("]", ""))
    for i in inst_value_igid_bfm_map:
        print(inst_value_igid_bfm_map[i], ",",
              str([sdc_avf_list[types_inj][inst_value_igid_bfm_map[i]] for types_inj in types_injected]).replace("[",
                                                                                                                 "").replace(
                  "]", ""))


if __name__ == "__main__":
    main()
