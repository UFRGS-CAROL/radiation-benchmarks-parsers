# UFRGS Radiation Benchmarks Parsers

TODO: Write a project description

## Installation

TODO: Describe the installation process

## Usage

usage: ParseBenchmarksCriticality.py [-h] [--gen_database GEN_DATA]
                                     [--out_database OUT_DATA]
                                     [--database ERROR_DATABASE]
                                     [--benchmarks BENCHMARKS]
                                     [--parse_layers]
                                     [--pr_threshold PR_THRESHOLD]
                                     [--check_csv] [--ecc] [--is_fi]

Parse logs for Neural Networks

optional arguments:
  -h, --help            show this help message and exit
  --gen_database GEN_DATA
                        if this flag is passed the other flags will have no
                        effects. --gen_data <path where the parser must search
                        for ALL LOGs FILES
  --out_database OUT_DATA
                        The output database name
  --database ERROR_DATABASE
                        Where database is located
  --benchmarks BENCHMARKS
                        A list separated by ',' (commas with no sapace) where
                        each item will be the benchmarks that parser will
                        process. Availiable parsers: Darknet, Hotspot, GEMM,
                        HOG, lavamd nw, quicksort, accl, PyFasterRCNN, Lulesh,
                        LUD, mergesort. Darknet benchmark needs --parse_layers
                        parameter, which is False if no layer will be parsed,
                        and True otherwise. Darknet, HOG, and PyFasterRCNN
                        need a Precision and Recall threshold value.If you
                        want a more correct radiation test result pass
                        --check_csv flag
  --parse_layers        If you want parse Darknet layers, set it True, default
                        values is False
  --pr_threshold PR_THRESHOLD
                        Precision and Recall threshold value,0 - 1, defautl
                        value is 0.5
  --check_csv           This parameter will open a csv file which contains all
                        radiation test runs, then it will check if every SDC
                        is on a valid run, default is false
  --ecc                 If the boards have ecc this is passed, otherwise
                        nothing must be passed
  --is_fi               if it is a fault injection log processing


## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D

## History

TODO: Write history

## Credits

TODO: Write credits

## License

   Copyright 2017 UFRGS HPC Reliability Group

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
