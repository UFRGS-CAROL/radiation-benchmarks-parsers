#!/usr/bin/env python
import sys
from SupportClasses import MatchBenchmark
from SupportClasses import WriteSDCDatabase
import shelve
import argparse
import Parameters as par

# benchmarks dict => (bechmarkname_machinename : list of SDC item)
# SDC item => [logfile name, header, sdc iteration, iteration total amount error, iteration accumulated error, list of errors ]
# list of errors => list of strings with all the error detail print in lines using #ERR
def parseErrors(benchmarkname_machinename, sdcItemList):
    sdci = 1
    totalSdcs = len(sdcItemList)
    matchBench = MatchBenchmark.MatchBenchmark()
    for sdcItem in sdcItemList:
        match = matchBench.processHeader(sdcItem, benchmarkname_machinename)
        if not match:
            continue

        progress = "{0:.2f}".format(float(sdci) / float(totalSdcs) * 100)
        sys.stdout.write("\rProcessing SDC " + str(sdci) + " of " + str(
            totalSdcs) + " - " + progress + "%")

        sys.stdout.flush()

        matchBench.parseErrCall()
        matchBench.relativeErrorParserCall()
        matchBench.localityParserCall()
        matchBench.jaccardCoefficientCall()

        matchBench.writeToCSVCall()
        sdci += 1
    sys.stdout.write(
        "\rProcessing SDC " + str(sdci - 1) + " of " + str(totalSdcs) + " - 100%                     " + "\n")
    sys.stdout.flush()


def parse_args():
    """Parse input arguments."""

    parser = argparse.ArgumentParser(description='Parse logs for Neural Networks')

    parser.add_argument('--gen_database', dest='gen_data',
                        help="if this flag is passed the other flags will have no effects. --gen_data <path where the parser must search for ALL LOGs FILES",
                        default='')

    parser.add_argument('--out_database', dest='out_data', help = "The output database name", default='./error_log_database')

   # args = parser.parse_args()


    parser.add_argument('--database', dest='error_database',
                        help='Where database is located', default="errors_log_database")

    parser.add_argument('--benchmarks', dest='benchmarks',
                        help='A list separated by \',\' (commas with no sapace) where each item will be the benchmarks that parser will process.'
                             '\nAvailiable parsers: Darknet, Hotspot, GEMM, HOG, lavamd'
                             '\nnw, quicksort, accl, PyFasterRCNN, Lulesh, LUD, mergesort.'
                             ' Darknet benchmark needs --parse_layers parameter, which is False if no layer will be parsed, and True otherwise.'
                             ' Darknet, HOG, and PyFasterRCNN need a Precision and Recall threshold value.'
                             'If you want a more correct radiation test result pass --check_csv flag')

    parser.add_argument('--parse_layers', dest='parse_layers',
                        help='If you want parse Darknet layers, set it True, default values is False',
                        default=False, action='store_true')

    parser.add_argument('--pr_threshold', dest='pr_threshold',
                        help='Precision and Recall threshold value,0 - 1, defautl value is 0.5',
                        default=0.5)

    parser.add_argument('--check_csv', dest='check_csv',
                        help='This parameter will open a csv file which contains all radiation test runs, then it will check '
                             'if every SDC is on a valid run, default is false',
                        default=False, action='store_true')

    parser.add_argument('--ecc', dest='ecc',
                        help='If the boards have ecc this is passed, otherwise nothing must be passed', default=False,
                        action='store_true')

    parser.add_argument('--is_fi', dest='is_fi', help='if it is a fault injection log processing', action='store_true',
                        default=False)


    args = parser.parse_args()
    return args


###########################################
# MAIN
###########################################'

if __name__ == '__main__':
    args = parse_args()

    # generating error_log_database
    if args.gen_data != '':
        writeSDCData = WriteSDCDatabase.WriteSDCDatabase(path=str(args.gen_data),out=str(args.out_data))
        writeSDCData.execute()
    else:

        benchlist = (str(args.benchmarks).lower()).split(',')
        print args.parse_layers
        par.setBenchmarks(
            benchmarks=benchlist,
            pr_threshold=args.pr_threshold,
            parse_layers=args.parse_layers,
            check_csv=args.check_csv,
            ecc=args.ecc,
            is_fi=args.is_fi
        )

        db = shelve.open(args.error_database)
        for k, v in db.iteritems():
            print("Processing ", k)
            parseErrors(k, v)

        db.close()
