#!/usr/bin/env python
import re
import shelve
import sys

import matplotlib.pyplot as plt
import numpy as np

from scipy.interpolate import make_interp_spline, BSpline


def plot_graph_xy(x_data, y_data, x_axis_label, y_axis_label):
    plt.plot(x_data, y_data)
    plt.xlabel(x_axis_label)

    plt.ylabel(y_axis_label)
    plt.yscale('log')

    plt.show()


def pre_process_errors(k, v):
    error_per_log = {}
    for sdc_inf in v:
        log_name = sdc_inf[0]
        header = sdc_inf[1]
        m = re.match(".*checkblock:(\d+).*", header)

        error_per_log[log_name] = {
            "check_block": int(m.group(1)),
            "err_list": sdc_inf[-1]
        }

    return error_per_log


def process_micro_error(err):
    err_data = []

    for e in err:
        err_list = err[e]['err_list']
        skip_next = False
        for i, lst in enumerate(err_list):
            if skip_next:
                skip_next = False
                continue
            pattern_error = '.*r: (\S+),.*e: (\S+) smaller_precision: (\S+).*'
            pattern_detected = '.*detected_dmr_errors: (\d+).*'

            m = re.match(pattern_error, lst)
            err_parsed = [np.float64(m.group(1)), np.float64(m.group(2)), np.float64(m.group(3))]

            try:
                lst = err_list[i + 1]
                m = re.match(pattern_detected, lst)

                err_parsed.append(int(m.group(1)))
                skip_next = True
            except:
                pass

            err_data.append(err_parsed)

    error_metrics = []
    # Analysis on relative error
    for error in err_data:
        r = error[0]
        e = error[1]
        smaller = error[2]
        number_diff = abs(r - e)
        hardening_diff = abs(e - smaller)
        relative_error_sdc = abs(number_diff / e)
        relative_error_hardening = abs(hardening_diff / e)

        detected = False
        if len(error) == 4:
            detected = True

        # print("Number diff {:.15E}, DMR diff {:.15E}, relative error SDC {:.15E} relative error DMR {:.15E}".format(
        #     number_diff,
        #     hardening_diff,
        #     relative_error_sdc,
        #     relative_error_hardening
        #     , detected))
        error_metrics.append([number_diff,
                              hardening_diff,
                              relative_error_sdc,
                              relative_error_hardening])
    return error_metrics


def generate_axis_data(error_metrics):
    # how_many_detected_faults = [i[3] for i in error_metrics].count(True)
    how_many_errors = len(error_metrics)

    digit_displacement = 16gar   # max number of digits after . in double

    threshold_variation = [10**-i for i in range(0, digit_displacement)]
    threshold_variation.append(0.0)
    threshold_variation.sort()
    # percentage_variation = [i/10 for i in range(0, 10)]

    percentage_detected_errors = []

    for threshold_i in threshold_variation:
        errors_detected = 0
        for e in error_metrics:
            if e[1] < threshold_i:
                errors_detected += 1

        percentage_detected_errors.append(float(errors_detected) / float(how_many_errors))

    return percentage_detected_errors, threshold_variation


def parse_errors(error_benchmarks):
    err_dict = {}
    for err in error_benchmarks:
        if "MICRO-" in err.upper():
            err_data = process_micro_error(error_benchmarks[err])
            err_dict[err] = generate_axis_data(err_data)
        elif "HOTSPOT" in err.upper():
            raise NotImplementedError
        elif "YOLO" in err.upper():
            raise NotImplementedError

    return err_dict


def parse_database(error_database):
    # open the shelve error database
    db = shelve.open(error_database)

    error_list_per_machine = {}

    # process each benchmark class
    for k, v in db.iteritems():
        print("Processing ", k)
        error_list_per_machine[k] = pre_process_errors(k, v)

    db.close()

    # Parse the errors
    return parse_errors(error_list_per_machine)


def main():
    error_database = sys.argv[1]
    err_dict = parse_database(error_database)
    for e in err_dict:
        x_axis = np.array(err_dict[e][0])
        y_axis = np.array(err_dict[e][1])

        # try:
        plot_graph_xy(x_axis, y_axis, "% detected faults", "Error threshold")
    # except:
    #     print("NO VALID RESULTS, SORRY NO HPCA PAPER FOR TODAY")


if __name__ == '__main__':
    main()
