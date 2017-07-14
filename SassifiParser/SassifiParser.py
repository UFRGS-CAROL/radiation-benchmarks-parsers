#!/usr/bin/env python

import argparse
import os
import csv
import re
from collections import Counter

IGID_STR = ["GPR", "CC", "PR", "STORE_OP",
            "IADD_IMUL_OP", "FADD_FMUL_OP", "DADD_DMUL_OP",
            "MAD_OP", "FFMA_OP", "DFMA_OP", "SETP_OP",
            "LDS_OP", "LD_OP", "MISC_OP"]

EM_STR = ["FLIP_SINGLE_BIT", "FLIP_TWO_BITS", "RANDOM_VALUE", "ZERO_VALUE",
          "WARP_FLIP_SINGLE_BIT", "WARP_FLIP_TWO_BITS", "WARP_RANDOM_VALUE",
          "WARP_ZERO_VALUE"]

ERROR_MODEL_SIZE = len(EM_STR)
INSTRUCTION_SIZE = len(IGID_STR)


class SassifiParser:
    inst_type = "rf"

    _contErrorTypePerInstruction = None
    _contCrashPerInstruction = None
    _contAbortPerInstruction = None

    def __init__(self, instType):
        self.inst_type = instType
        self._contCrashPerInstruction = {i: {j: 0 for j in EM_STR} for i in IGID_STR}
        self._contErrorTypePerInstruction = {i: {j: 0 for j in EM_STR} for i in IGID_STR}
        self._contAbortPerInstruction = {i: {j: 0 for j in EM_STR} for i in IGID_STR}

    def check_crash(self, log_filename):
        log_file = open(log_filename)
        regexp = re.compile(r'.*KerTime.*?([0-9.-]+)')
        there_is_end = 0
        there_is_abort = 0
        kernel_time = 0
        for line in log_file:
            match = regexp.match(line)
            if match:
                kernel_time = float(match.group(1))
            if 'END' in line:
                there_is_end = 1
            if 'ABORT' in line:
                there_is_abort = 1
        log_file.close()
        crash = 0
        if there_is_end == 0:
            crash = 1
        return (crash, there_is_abort, kernel_time)

    def count_frequency(self, row_to_count):
        # row_to_count = [row[string_to_count] for row in reader]
        array_size = []
        for (k, v) in Counter(row_to_count).iteritems():
            array_size.append([k, v])

        return array_size

    def parse_csv(self, csv_input, logs_dir, cp):
        global INSTRUCTION_SIZE, ERROR_MODEL_SIZE

        csvfile = open(csv_input)
        reader = csv.DictReader(csvfile)
        # count sdcs for each instruction
        sdc_inst_count = []
        # count sdcs for each error model
        sdc_em_count = []
        sdcs = 0
        # count total faults
        total_faults = 0
        # total faults per instruction
        total_inst_count = []
        # per error model
        total_em_count = []

        # count crashes and abort per instruction
        crashes_inst_count = []
        abort_inst_count = []
        # count crashes and abort per error model
        crashes_em_count = []
        abort_em_count = []

        # count for each injection type the kernel occurrence
        sdc_em_count_per_kernel = {}
        sdc_inst_count_per_kernel = {}
        inj_em_count_per_kernel = {}
        inj_inst_count_per_kernel = {}
        # kernel_array = count_frequency(reader,"inj_kname")

        # kernel time
        kern_time = []

        total_crashes = 0
        total_aborts = 0
        print "Parsing " + csv_input
        # separate the good data
        if cp != "":
            copyLogsFolder = str(cp)
            os.system("mkdir -p " + copyLogsFolder)
        for i in range(0, INSTRUCTION_SIZE):
            sdc_inst_count.append(0)
            total_inst_count.append(0)
            crashes_inst_count.append(0)
            abort_inst_count.append(0)

        for i in range(0, ERROR_MODEL_SIZE):
            sdc_em_count.append(0)
            total_em_count.append(0)
            crashes_em_count.append(0)
            abort_em_count.append(0)

        # log_file,has_sdc,inj_kname,inj_kcount, inj_igid, inj_fault_model,
        # inj_inst_id, inj_destination_id, inj_bit_location, finished
        for row in reader:
            # cp all good data to new folder
            if cp != "":
                os.system("cp " + logs_dir + "/" + row['log_file'] + " " + copyLogsFolder)
            it_inst_count = 8

            if 'inst' in self.inst_type:
                it_inst_count = int(row['inj_igid'])

            it_em_count = int(row['inj_fault_model'])
            # increase each instrction/error model count to have the final results
            if '1' in row['has_sdc']:
                sdc_inst_count[it_inst_count] += 1
                sdc_em_count[it_em_count] += 1
                sdcs += 1

                # to get each EM avf for each instruction type
                self._contErrorTypePerInstruction[IGID_STR[it_inst_count]][EM_STR[it_em_count]] += 1
                # count em per kernel
                if row["inj_kname"] not in sdc_em_count_per_kernel:
                    sdc_em_count_per_kernel[row["inj_kname"]] = []
                    for x in range(0, ERROR_MODEL_SIZE):
                        sdc_em_count_per_kernel[row["inj_kname"]].append(0)

                if row["inj_kname"] not in sdc_inst_count_per_kernel:
                    sdc_inst_count_per_kernel[row["inj_kname"]] = []
                    for x in range(0, INSTRUCTION_SIZE):
                        sdc_inst_count_per_kernel[row["inj_kname"]].append(0)

                sdc_em_count_per_kernel[row["inj_kname"]][it_em_count] += 1
                sdc_inst_count_per_kernel[row["inj_kname"]][it_inst_count] += 1

            if row["inj_kname"] not in inj_em_count_per_kernel:
                inj_em_count_per_kernel[row["inj_kname"]] = 0

            if row["inj_kname"] not in inj_inst_count_per_kernel:
                inj_inst_count_per_kernel[row["inj_kname"]] = 0

            inj_em_count_per_kernel[row["inj_kname"]] += 1
            inj_inst_count_per_kernel[row["inj_kname"]] += 1
            # check crash info for each file
            (crash, abort, kertime) = self.check_crash(logs_dir + "/" + row['log_file'])
            if crash > 1 or abort > 1:
                print 'Some error in the log files'
                exit(1)
            crashes_inst_count[it_inst_count] += crash
            abort_inst_count[it_inst_count] += abort
            crashes_em_count[it_em_count] += crash
            abort_em_count[it_em_count] += abort
            total_crashes += crash
            kern_time.append(kertime)
            total_faults += 1

            # to get avf of each EM for each instruction type
            self._contCrashPerInstruction[IGID_STR[it_inst_count]][EM_STR[it_em_count]] += crash + abort
            # self._contAbortPerInstruction[ASID_STR[it_inst_count]][EM_STR[it_em_count]] += abort
            # print row['inj_asid'] + " " + row['inj_fault_model']

            total_inst_count[it_inst_count] += 1
            total_em_count[it_em_count] += 1

        csvfile.close()
        # ---------------------------------------------------------------
        # print instruction histogram
        csvfile = self.__generate_parse_filename(csv_input)
        fieldnames = ['instruction', 'sdc_num', 'total_inst_count', 'crashes',
                      'abort', 'nothing']
        fieldnames.extend(['sdc_' + str(i) for i in EM_STR])
        fieldnames.extend(['crash_abort_' + str(i) for i in EM_STR])

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(0, INSTRUCTION_SIZE):
            tempDict = {
                'instruction': IGID_STR[i],
                'sdc_num': str(sdc_inst_count[i]),
                'total_inst_count': str(total_inst_count[i]),
                'crashes': str(crashes_inst_count[i]),
                'abort': str(abort_inst_count[i]),
                'nothing': '',
            }
            for t in EM_STR:
                tempDict['sdc_' + t] = self._contErrorTypePerInstruction[IGID_STR[i]][t]

            for t in EM_STR:
                tempDict['crash_abort_' + t] = self._contCrashPerInstruction[IGID_STR[i]][t]

            writer.writerow(tempDict)

        writer.writerow({'instruction': '', 'sdc_num': '', 'total_inst_count': ''})
        writer.writerow({
            'instruction': 'error_model', 'sdc_num': 'sdc_num',
            'total_inst_count': 'total_em_count'})
        for i in range(0, ERROR_MODEL_SIZE):
            writer.writerow({
                'instruction': EM_STR[i],
                'sdc_num': str(sdc_em_count[i]),
                'total_inst_count': str(total_em_count[i]),
                'crashes': str(crashes_em_count[i]),
                'abort': str(abort_em_count[i])})

        writer.writerow({'instruction': '', 'sdc_num': ''})

        writer.writerow({'instruction': 'Total sdcs', 'sdc_num': str(sdcs)})
        writer.writerow(
            {'instruction': 'Injected faults', 'sdc_num': str(total_faults)})
        # print kern_time
        runtime_average = sum(kern_time) / len(kern_time)

        writer.writerow({
            'instruction': 'Average kernel runtime',
            'sdc_num': str(runtime_average)})

        writer.writerow({
            'instruction': 'error model', 'sdc_num': 'SDCs',
            'total_inst_count': '', 'crashes': 'crashes per EM', 'abort': 'abort per EM'})

        for kernel in inj_em_count_per_kernel:
            # kernel = str(i[0])
            writer.writerow({'instruction': kernel})
            if kernel in sdc_em_count_per_kernel:
                err_list = sdc_em_count_per_kernel[kernel]
                for j in range(ERROR_MODEL_SIZE):
                    writer.writerow(
                        {'instruction': EM_STR[j], 'sdc_num': str(err_list[j])})

        writer.writerow({'instruction': '', 'sdc_num': '', 'total_inst_count': ''})
        writer.writerow({
            'instruction': 'Instructions', 'sdc_num': 'SDCs',
            'total_inst_count': ''})

        for kernel in inj_inst_count_per_kernel:
            writer.writerow({'instruction': kernel})
            if kernel in sdc_inst_count_per_kernel:
                err_list = sdc_inst_count_per_kernel[kernel]
                for j in range(INSTRUCTION_SIZE):
                    writer.writerow(
                        {'instruction': IGID_STR[j], 'sdc_num': str(err_list[j])})

        writer.writerow({'instruction': '', 'total_inst_count': ''})
        writer.writerow({
            'instruction': 'kernel', 'sdc_num': 'injected faults',
            'total_inst_count': ''})
        for kernel in inj_inst_count_per_kernel:
            writer.writerow(
                {'instruction': kernel, 'sdc_num': inj_em_count_per_kernel[kernel]})

        writer.writerow(
            {'instruction': '', 'sdc_num': ''})
        writer.writerow(
            {'instruction': 'SDCs per instruction based on each error type', 'sdc_num': ''})

        csvfile.close()
        print csv_input + " parsed"

    def __generate_parse_filename(self, csv_input):
        dir_generate = csv_input.split('/')[-1]
        first_part = csv_input.split(dir_generate)[0]
        csvfile = open(first_part + 'parse_' + dir_generate, 'w')
        return csvfile

    def process_daniels_and_caios_log(self, csv_input, to_join, key, joined, del1, del2):
        # sassifi output
        csvfile = open(csv_input)
        reader = csv.DictReader(csvfile, delimiter=del1)

        # file which will be joined
        daniel_input = open(to_join)
        reader_daniel = csv.DictReader(daniel_input, delimiter=del2)

        # the final header will be input and to_join csv headers
        fieldnames = []
        for i in reader.fieldnames:
            fieldnames.append(i)

        for i in reader_daniel.fieldnames:
            fieldnames.append(i)

        output_csv = open(joined, 'w')
        writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
        writer.writeheader()

        # put the content into two list
        daniel_rows = []
        logs_rows = []
        for row in reader_daniel:
            daniel_rows.append(row)
        for row in reader:
            logs_rows.append(row)

        # join two csvs
        count_logs = 0
        d = {}
        has_sdc = 'has_sdc'

        if key != 'none':
            for i in logs_rows:
                log_file = i[key]
                if '1' in i[has_sdc]:
                    for j in daniel_rows:
                        logname = j[key]
                        if logname in log_file and log_file not in d.values():
                            z = j.copy()
                            z.update(i)
                            d = z.copy()
                            writer.writerow(z)
                            count_logs += 1

                            break

        print "Parsed " + str(count_logs)
        csvfile.close()
        daniel_input.close()
        output_csv.close()


# except:
#     e = sys.exc_info()[0]
#     #write_to_page( "<p>Error: %s</p>" % e )
#     print e
def usage():
    print "For parse raw data <csv_input> <logs_dir> <cp | none> <caio | none>"
    print "For merge and parse Daniel's log <csv_input> <daniel_csv> <is_daniel> <c or d or l | none>"


def parse_args():
    """Parse input arguments."""

    parser = argparse.ArgumentParser(description='Parser for sassifi fault injection')
    # parser.add_argument('--gold', dest='gold_dir', help='Directory where gold is located',
    #                     default=GOLD_DIR, type=str)
    parser.add_argument('--inj_type', dest='inst_type', help='INST/RF', default="rf")
    parser.add_argument('--csv_input', dest='csv_input', help='Where is the csv log generated by modified sassifi')

    parser.add_argument('--logs_dir', dest='logs_dir',
                        help='Logs directory, which must have all logs described on csv_input',
                        default='logs_dir')
    parser.add_argument('--copy', dest='copy',
                        help='Is necessary to copy logs to another folder, if yes, pass the output directory',
                        default="")
    parser.add_argument('--join_key', dest='join_key',
                        help='If you want to join two files that have a collum with header = \'log_filename\' for example, --join_key log_filename must be passed',
                        default='log_filename')

    parser.add_argument('--to_join_csv', dest='to_join_csv', help='Other csv to join', default='none')

    parser.add_argument('--joined_output', dest='joined', help='Output file which will have two csvs joined',
                        default='joined_logs.csv')

    parser.add_argument('--del1', dest='del1', help='Delimiter csv <--csv_input>', default=',')

    parser.add_argument('--del2', dest='del2', help='Delimiter csv <--to_join_csv>', default=';')

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    # parameter = sys.argv[1:]
    # # ()
    # if len(parameter) < 3:
    #     usage()
    # else:
    #     if parameter[3] != 'caio':
    args = parse_args()
    sassiParse = SassifiParser(args.inst_type)
    if args.to_join_csv == 'none':
        sassiParse.parse_csv(args.csv_input, args.logs_dir, args.copy)
    else:
        sassiParse.process_daniels_and_caios_log(args.csv_input, args.to_join_csv, args.join_key, args.joined,
                                                 args.del1, args.del2)
        # ():
        # else:
        #     process_daniels_and_caios_log(parameter[0], parameter[1],
        #                                   parameter[2])
