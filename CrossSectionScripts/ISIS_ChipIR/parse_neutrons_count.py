#!/usr/bin/env python
import re
import sys


def merge_files(paths, output_file):
    with open(output_file, "w") as outf:
        for path in paths:
            with open(path, 'r') as fi:
                lines = fi.readlines()
                for line in lines:
                    if 'Data From ChipIR' in line:
                        continue
                    try:
                        out_line = re.sub(r"\s+", ';', line)
                        out_line = out_line[:-1]
                        outf.write(out_line + "\n")
                    except Exception as err:
                        print line, err

if __name__ == '__main__':
    output_file = sys.argv[len(sys.argv) - 1]
    paths = sys.argv[1:(len(sys.argv) - 1)]
    merge_files(paths=paths, output_file=output_file)