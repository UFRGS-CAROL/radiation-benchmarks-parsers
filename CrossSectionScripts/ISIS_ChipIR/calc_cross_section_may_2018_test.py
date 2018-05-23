#!/usr/bin/python -u
import os
import sys
import re
import csv
from datetime import timedelta
from datetime import datetime


def get_dt(year_date, day_time, sec_frac):
    yv = year_date.split('/')
    day = int(yv[0])
    month = int(yv[1])
    year = int(yv[2])

    dv = day_time.split(':')
    hour = int(dv[0])
    minute = int(dv[1])
    second = int(dv[2])

    # we get secFrac in seconds, so we must convert to microseconds
    # e.g: 0.100 seconds = 100 milliseconds = 100000 microseconds
    microsecond = int(float(sec_frac) * 1e6)

    return datetime(year, month, day, hour, minute, second, microsecond)


def read_count_file(in_file_name):
    """
    Read neutron log file
    :param in_file_name: neutron log filename
    :return: list with all neutron lines
    """
    file_lines = []
    with open(in_file_name, 'r') as in_file:
        for l in in_file:
            # Sanity check, we require a date at the beginning of the line
            line = l.rstrip()
            if not re.match("\d{1,2}/\d{1,2}/\d{2,4}", line):
                sys.stderr.write("Ignoring line (malformed):\n%s\n" % (line))
                continue

            if "N/A" in line:
                break

            file_lines.append(line)
    return file_lines


def get_fluence_flux(start_dt, end_dt, file_lines, factor, distance_factor=1.0):
    # inFile = open(inFileName, 'r')
    # endDT = startDT + timedelta(minutes=60)

    # last_counter_20 = 0
    last_fission_counter = None
    # last_counter_30mv = 0
    # last_counter_40 = 0
    # last_cur_integral = 0
    last_dt = None
    # flux1h = 0
    beam_off_time = 0
    first_curr_integral = None
    first_counter_30mv = None
    first_fission_counter = None

    # for l in inFile:
    for line in file_lines:
        # Parse the line
        # line = l.split(';')
        # the date is organized in this order:
        # Date;time;decimal of second; Dimond counter threshold = 40mV(counts);
        # Dimond counter th = 20mV(counts); Dimond counter th = 30mV(counts);
        # Fission Counter(counts); Integral Current uAh; Current uA

        year_date = line[0]
        day_time = line[1]
        sec_frac = line[2]
        # counter_30mv = float(line[5])
        fission_counter = float(line[6])
        # curr_integral = float(line[5])

        # Generate datetime for line
        cur_dt = get_dt(year_date, day_time, sec_frac)
        if start_dt <= cur_dt and first_fission_counter is None:
            first_fission_counter = fission_counter
            # first_counter_30mv = counter_30mv
            # last_counter_30mv = counter_30mv
            last_dt = cur_dt
            continue

        # if first_curr_integral is not None:
        if first_fission_counter is not None:
            if fission_counter == last_fission_counter:
                beam_off_time += (cur_dt - last_dt).total_seconds()

            last_fission_counter = fission_counter
            last_dt = cur_dt

        if cur_dt > end_dt:
            interval_total_seconds = float((end_dt - start_dt).total_seconds())
            flux1h = ((last_fission_counter - first_fission_counter) * factor) / interval_total_seconds
            flux1h *= distance_factor
            return flux1h, beam_off_time
        elif first_curr_integral is not None:
            last_fission_counter = fission_counter

    return 0, beam_off_time


def create_run_classes(possible_benchmarks, possible_headers, csv_data):
    bench_combination = {}
    for benchmark in possible_benchmarks:
        for header in possible_headers:
            key = benchmark + "_" + header
            bench_combination[key] = []

    for csv_line in csv_data:
        key_csv_line = csv_line[2] + '_' + csv_line[3]
        bench_combination[key_csv_line].append(csv_line)

    ret_bench_combination = {}
    for key in bench_combination:
        if len(bench_combination[key]) != 0:
            ret_bench_combination[key] = bench_combination[key]

    return ret_bench_combination


def generate_benchmark_runs(benchmark_exec_list, neutron_file_lines, factor, distance_factor=1.0):
    abort_zero_s = 0
    obtained_runs = {}
    start_dt = datetime.strptime(benchmark_exec_list[0][0][0:-1], "%c")
    end_dt = start_dt
    obtained_runs[start_dt] = {'executions': []}

    for benchmark_exec in benchmark_exec_list:
        obtained_runs[start_dt]['executions'].append(benchmark_exec)

        # acc_time
        acc_time_s = float(benchmark_exec[6])
        # #SDC
        sdc_s = int(benchmark_exec[4])
        # abort
        if int(benchmark_exec[7]) == 1:
            abort_zero_s += 1
        elif int(benchmark_exec[8]) == 0:
            abort_zero_s += 1

        if end_dt - start_dt >= timedelta(minutes=60):
            # compute 1h flux; sum SDC, ACC_TIME, Abort with 0; compute fluence (flux*(sum ACC_TIME))
            flux, time_beam_off = get_fluence_flux(start_dt=start_dt, end_dt=(start_dt + timedelta(minutes=60)),
                                                   file_lines=neutron_file_lines, factor=factor,
                                                   distance_factor=distance_factor)
            flux_acc_time, time_beam_off_acc_time = get_fluence_flux(start_dt=start_dt,
                                                                     end_dt=(start_dt + timedelta(seconds=acc_time_s)),
                                                                     file_lines=neutron_file_lines, factor=factor,
                                                                     distance_factor=distance_factor)

            fluence = flux * acc_time_s
            fluence_acc_time = flux_acc_time * acc_time_s
            if fluence > 0:
                cross_section = sdc_s / fluence
                cross_section_crash = abort_zero_s / fluence
            else:
                cross_section = 0
                cross_section_crash = 0
            if fluence_acc_time > 0:
                cross_section_acc_time = sdc_s / fluence_acc_time
                cross_section_crash_acc_time = abort_zero_s / fluence_acc_time
            else:
                cross_section_acc_time = 0
                cross_section_crash_acc_time = 0

            obtained_runs[start_dt]['metrics'] = [cross_section, cross_section_crash,
                                                  cross_section_acc_time, cross_section_crash_acc_time]

            start_dt = datetime.strptime(benchmark_exec[0][0:-1], "%c")
            obtained_runs[start_dt] = {'executions': []}
            abort_zero_s = 0

        end_dt = datetime.strptime(benchmark_exec[0][0:-1], "%c")

    return obtained_runs


def main():
    if len(sys.argv) < 4:
        print "Usage: {} <neutron counts input file> <csv file> <factor> <distance factor>".format(sys.argv[0])
        sys.exit(1)

    neutron_count_file_name = sys.argv[1]
    csv_file_name = sys.argv[2]
    factor = float(sys.argv[3])
    distance_factor = float(sys.argv[4])

    csv_output_summary_name = csv_file_name.replace(".csv", "_cross_section.csv")

    # Read all info from csv file
    csv_input_header = ""
    with open(csv_file_name, "r") as csv_input:
        reader = csv.reader(csv_input, delimiter=';')
        csv_input_file_lines = list(reader)[1:]

    # Read neutron count file
    with open(neutron_count_file_name, 'r') as neutron_count_input:
        reader = csv.reader(neutron_count_input, delimiter=';')
        neutron_file_lines = list(reader)

    # Filter all possible benchmarks
    all_possible_benchmarks = set([i[2] for i in csv_input_file_lines])
    all_possible_benchmarks_headers = set([i[3] for i in csv_input_file_lines])

    bench_combination = create_run_classes(possible_benchmarks=all_possible_benchmarks,
                                           possible_headers=all_possible_benchmarks_headers,
                                           csv_data=csv_input_file_lines)

    with open(csv_output_summary_name, 'w') as csv_writer_summary_output:
        writer_summary_out = csv.writer(csv_writer_summary_output, delimiter=';')

        for key_bench in bench_combination:
            obtained_runs = generate_benchmark_runs(benchmark_exec_list=bench_combination[key_bench],
                                                    neutron_file_lines=neutron_file_lines,
                                                    factor=factor, distance_factor=distance_factor)
            for run in obtained_runs:
                for executions in obtained_runs[run]['executions']:
                    writer_summary_out.writerow(executions)
                if 'metrics' in obtained_runs[run]:
                    writer_summary_out.writerow(obtained_runs[run]['metrics'])


#########################################################
#                    Main Thread                        #
#########################################################
if __name__ == '__main__':
    main()


    # def main():

    #     in_file_name = sys.argv[1]
    #     csv_file_name = sys.argv[2]
    #     factor = float(sys.argv[3])
    #     distance_factor = float(sys.argv[4])
    #
    #     csv_out_file_full = csv_file_name.replace(".csv", "_cross_section.csv")
    #     csv_out_file_summary = csv_file_name.replace(".csv", "_cross_section_summary.csv")
    #     print "in: " + csv_file_name
    #     print "out: " + csv_out_file_full
    #     with open(csv_file_name, "r") as csv_input, open(csv_out_file_full, "w") as csv_full, open(csv_out_file_summary,
    #                                                                                                "w") as csv_summary:
    #
    #         reader = csv.DictReader(csv_input, delimiter=';')
    #         # csv_header = next(reader, None)
    #         lines = list(reader)
    #         field_names = lines[0].keys()
    #         # writer_csv_full.writerow()
    #         # writer_csv_summary.writerow(lines[0].keys())
    #
    #         header_c = ["start timestamp", "end timestamp", "#lines computed", "#SDC", "#AccTime", "#(Abort==0)",
    #                     "Flux 1h (factor " + str(distance_factor) + ")",
    #                     "Flux AccTime (factor " + str(distance_factor) + ")",
    #                     "Fluence(Flux * $AccTime)", "Fluence AccTime(FluxAccTime * $AccTime)", "Cross Section SDC",
    #                     "Cross Section Crash", "Time Beam Off (sec)", "Cross Section SDC AccTime",
    #                     "Cross Section Crash AccTime", "Time Beam Off AccTime (sec)"]
    #
    #         writer_csv_full = csv.DictWriter(csv_full, delimiter=';',
    #                                          fieldnames=header_c + field_names, extrasaction='ignore')
    #         writer_csv_summary = csv.DictWriter(csv_summary, delimiter=';',
    #                                             fieldnames=header_c + field_names, extrasaction='ignore')
    #         writer_csv_full.writeheader()
    #         writer_csv_summary.writeheader()
    #
    #         # We need to read the neutron count files before calling get_fluence_flux
    #         file_lines = read_count_file(in_file_name)
    #         # Time;Machine;Benchmark;Header Info;#SDC;acc_err;acc_time;abort;end;filename and dir
    #         for i, line in enumerate(lines):
    #             start_dt = datetime.strptime(line['Time'][0:-1], "%c")
    #             j = i
    #             # acc_time
    #             acc_time_s = float(line['acc_time'])
    #             # #SDC
    #             sdc_s = int(line['#SDC'])
    #             # abort
    #             abort_zero_s = 0
    #             if int(line['abort']) == 0:
    #                 abort_zero_s += 1
    #
    #             writer_csv_full.writerow(line)
    #             writer_csv_summary.writerow(line)
    #             end_dt = datetime.strptime(lines[i + 1]['Time'][0:-1], "%c")
    #             print "parsing file {} date in line {}:{}".format(csv_file_name.replace(".csv", ""), str(i), start_dt,
    #                                                               end_dt)
    #
    #             last_line = ""
    #             while (end_dt - start_dt) < timedelta(minutes=60):
    #                 if lines[i + 1]['Benchmark'] != line['Benchmark']:  # not the same benchmark
    #                     break
    #                 if lines[i + 1]['Header Info'] != line['Header Info']:  # not the same input
    #                     break
    #                 # print "line "+str(i)+" inside 1h interval"
    #                 i += 1
    #                 acc_time_s += float(line['acc_time'])
    #                 sdc_s += int(line['#SDC'])
    #                 if int(line['abort']) == 0:
    #                     abort_zero_s += 1
    #                 writer_csv_full.writerow(line)
    #                 last_line = line
    #
    #                 if i == (len(lines) - 1):  # end of lines
    #                     break
    #                 end_dt = datetime.strptime(lines[i + 1]['Time'][0:-1], "%c")
    #
    #             # compute 1h flux; sum SDC, ACC_TIME, Abort with 0; compute fluence (flux*(sum ACC_TIME))
    #             flux, time_beam_off = get_fluence_flux(start_dt=start_dt, end_dt=(start_dt + timedelta(minutes=60)),
    #                                                    file_lines=file_lines, factor=factor,
    #                                                    distance_factor=distance_factor)
    #             flux_acc_time, time_beam_off_acc_time = get_fluence_flux(start_dt=start_dt,
    #                                                                      end_dt=(start_dt + timedelta(seconds=acc_time_s)),
    #                                                                      file_lines=file_lines, factor=factor,
    #                                                                      distance_factor=distance_factor)
    #
    #             fluence = flux * acc_time_s
    #             fluence_acc_time = flux_acc_time * acc_time_s
    #             if fluence > 0:
    #                 cross_section = sdc_s / fluence
    #                 cross_section_crash = abort_zero_s / fluence
    #             else:
    #                 cross_section = 0
    #                 cross_section_crash = 0
    #             if fluence_acc_time > 0:
    #                 cross_section_acc_time = sdc_s / fluence_acc_time
    #                 cross_section_crash_acc_time = abort_zero_s / fluence_acc_time
    #             else:
    #                 cross_section_acc_time = 0
    #                 cross_section_crash_acc_time = 0
    #
    #             # writer_csv_full.writerow(header_c)
    #             if len(last_line) > 2:
    #                 writer_csv_summary.writerow(last_line)
    #
    #             # writer_csv_summary.writerow(header_c)
    #             row = {"start timestamp": start_dt.ctime(),
    #                    "end timestamp": end_dt.ctime(), "#lines computed": (i - j + 1),
    #                    "#SDC": sdc_s, "#AccTime": acc_time_s, "#(Abort==0)": abort_zero_s,
    #                    "Flux 1h (factor " + str(distance_factor) + ")": flux,
    #                    "Flux AccTime (factor " + str(distance_factor) + ")": flux_acc_time,
    #                    "Fluence(Flux * $AccTime)": fluence,
    #                    "Fluence AccTime(FluxAccTime * $AccTime)": fluence_acc_time,
    #                    "Cross Section SDC": cross_section,
    #                    "Cross Section Crash": cross_section_crash, "Time Beam Off (sec)": time_beam_off,
    #                    "Cross Section SDC AccTime": cross_section_acc_time,
    #                    "Cross Section Crash AccTime": cross_section_crash_acc_time,
    #                    "Time Beam Off AccTime (sec)": time_beam_off_acc_time}
    #             writer_csv_full.writerow(row)
    #             writer_csv_summary.writerow(row)
    #             # writer_csv_full.writerow([])
    #             # writer_csv_full.writerow([])
    #             # writer_csv_summary.writerow([])
    #             # writer_csv_summary.writerow([])
