#!/usr/bin/python -u

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


def get_fluence_flux(start_dt, end_dt, file_lines, factor):
    # inFile = open(inFileName, 'r')
    # endDT = startDT + timedelta(minutes=60)

    # last_counter_20 = 0
    last_counter_30 = 0
    # last_counter_40 = 0
    last_cur_integral = 0
    last_dt = None
    # flux1h = 0
    beam_off_time = 0
    first_cur_integral = None

    # for l in inFile:
    for line in file_lines:
        # Parse the line
        line = line.split(';')

        # 0 - 03/05/2018;
        # 1 - 00:00:02;
        # 2 - .723;
        # 3 - 00000000061;
        # 4 - 00000000035;
        # 5 - 00000000017;
        # 6 - 00001158191;
        # 7 - 4461.49;
        # 8 - 21.66
        year_date = line[0]
        day_time = line[1]
        sec_frac = line[2]
        cur_integral = float(line[6])

        # Generate datetime for line
        cur_dt = get_dt(year_date, day_time, sec_frac)
        if first_cur_integral is None:
            first_cur_integral = cur_integral

        if cur_dt > end_dt:
            interval_total_seconds = float((end_dt - start_dt).total_seconds())
            flux1h = ((first_cur_integral -  cur_integral) * factor) / interval_total_seconds
            if flux1h < 0:
                raise ValueError
            # print cur_integral, first_cur_integral, interval_total_seconds, flux1h
            return [flux1h, beam_off_time]

        # if start_dt <= cur_dt and first_cur_integral is None:
        #     first_cur_integral = float(cur_integral)
        #     last_counter_20 = counter_20
        #     last_counter_30 = counter_30
        #     last_counter_40 = counter_40
        #     last_dt = cur_dt
        #     continue
        #
        # if first_cur_integral is not None:
        #     if counter_30 == last_counter_30:
        #         beam_off_time += (cur_dt - last_dt).total_seconds()
        #
        #     last_counter_20 = counter_20
        #     last_counter_30 = counter_30
        #     last_counter_40 = counter_40
        #     last_dt = cur_dt
        # if cur_dt > end_dt:
        #     flux1h = (float(last_cur_integral) - first_cur_integral) / (end_dt - start_dt).total_seconds()
        #     return [flux1h, beam_off_time]
        # elif first_cur_integral is not None:
        #     last_cur_integral = cur_integral


def calc_distance_factor(x):
    return 400.0 / ((x + 20.0) * (x + 20.0))


def main():
    if len(sys.argv) < 4:
        print "Usage: %s <neutron counts input file> <csv file> <factor>" % (sys.argv[0])
        sys.exit(1)
    in_file_name = sys.argv[1]
    csv_file_name = sys.argv[2]
    factor = float(sys.argv[3])  # calc_distance_factor(float(sys.argv[3]) / 100.0)
    distance_factor = float(sys.argv[4])

    csv_out_file_full = csv_file_name.replace(".csv", "_cross_section.csv")
    csv_out_file_summary = csv_file_name.replace(".csv", "_cross_section_summary.csv")
    print "in: " + csv_file_name
    print "out: " + csv_out_file_full
    with open(csv_file_name, "r") as csv_input, open(csv_out_file_full, "w") as csv_full, open(csv_out_file_summary,
                                                                                               "w") as csv_summary:
        reader = csv.reader(csv_input, delimiter=';')
        writer_csv_full = csv.writer(csv_full, delimiter=';')
        writer_csv_summary = csv.writer(csv_summary, delimiter=';')

        csv_header = next(reader, None)

        writer_csv_full.writerow(csv_header)
        writer_csv_summary.writerow(csv_header)

        lines = list(reader)

        # We need to read the neutron count files before calling get_fluence_flux
        file_lines = read_count_file(in_file_name)
        for i in range(0, len(lines) - 1):
            start_dt = datetime.strptime(lines[i][0][0:-1], "%c")
            j = i
            # acc_time
            acc_time_s = float(lines[i][6])
            # #SDC
            sdc_s = int(lines[i][4])
            # abort
            abort_zero_s = 0
            if int(lines[i][7]) == 0:
                abort_zero_s += 1

            writer_csv_full.writerow(lines[i])
            writer_csv_summary.writerow(lines[i])
            end_dt = datetime.strptime(lines[i + 1][0][0:-1], "%c")
            print "date in line", str(i), ":", start_dt, end_dt

            last_line = ""
            while (end_dt - start_dt) < timedelta(minutes=60):
                if lines[i + 1][2] != lines[i][2]:  # not the same benchmark
                    break
                if lines[i + 1][3] != lines[i][3]:  # not the same input
                    break
                # print "line "+str(i)+" inside 1h interval"
                i += 1
                acc_time_s += float(lines[i][6])
                sdc_s += int(lines[i][4])
                if int(lines[i][7]) == 0:
                    abort_zero_s += 1
                writer_csv_full.writerow(lines[i])
                last_line = lines[i]
                if i == (len(lines) - 1):  # end of lines
                    break
                end_dt = datetime.strptime(lines[i + 1][0][0:-1], "%c")
            # compute 1h flux; sum SDC, ACC_TIME, Abort with 0; compute fluence (flux*(sum ACC_TIME))
            flux, time_beam_off = get_fluence_flux(start_dt=start_dt, end_dt=(start_dt + timedelta(minutes=60)),
                                                   file_lines=file_lines, factor=factor)
            # get_fluence_flux(start_dt, (start_dt + timedelta(minutes=60)), file_lines)
            flux_acc_time, time_beam_off_acc_time = get_fluence_flux(start_dt=start_dt,
                                                                     end_dt=(start_dt + timedelta(seconds=acc_time_s)),
                                                                     file_lines=file_lines, factor=factor)
            # get_fluence_flux(start_dt,         (start_dt + timedelta(seconds=acc_time_s)),
            #                                                      file_lines)
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
            header_c = ["start timestamp", "end timestamp", "#lines computed", "#SDC", "#AccTime", "#(Abort==0)",
                        "Flux 1h (factor " + str(distance_factor) + ")", "Flux AccTime (factor " + str(distance_factor) + ")",
                        "Fluence(Flux * $AccTime)", "Fluence AccTime(FluxAccTime * $AccTime)", "Cross Section SDC",
                        "Cross Section Crash", "Time Beam Off (sec)", "Cross Section SDC AccTime",
                        "Cross Section Crash AccTime", "Time Beam Off AccTime (sec)"]
            writer_csv_full.writerow(header_c)
            writer_csv_summary.writerow(last_line)
            writer_csv_summary.writerow(header_c)
            row = [start_dt.ctime(), end_dt.ctime(), (i - j + 1), sdc_s, acc_time_s, abort_zero_s, flux, flux_acc_time,
                   fluence,
                   fluence_acc_time, cross_section, cross_section_crash, time_beam_off, cross_section_acc_time,
                   cross_section_crash_acc_time,
                   time_beam_off_acc_time]
            writer_csv_full.writerow(row)
            writer_csv_summary.writerow(row)
            writer_csv_full.writerow([])
            writer_csv_full.writerow([])
            writer_csv_summary.writerow([])
            writer_csv_summary.writerow([])


#########################################################
#                    Main Thread                        #
#########################################################
if __name__ == '__main__':
    main()
