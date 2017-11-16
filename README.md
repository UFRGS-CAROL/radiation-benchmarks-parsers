# UFRGS Radiation Benchmarks Parsers

TODO: Write a project description

## Installation

### 1
    Get the repository with git clone 
    https://github.com/fernandoFernandeSantos/radiation-benchmarks-parsers.git

### 2
    Set parameters for each particular benchmark available in
    https://github.com/dagoliveira/radiation-benchmarks.git
    Note: for some benchmarks such as Py-Faster-Rcnn and Darknet,
    you must have the Golden output for each platform,
    for error criticality evaluation

## Usage

Before use ParseBenchmarkCriticality.py keep in mind that all benchmarks parameters must be set in Parameters.py,
on the contrary, this parser will crash.

usage:

\<path\>/ParseBenchmarksCriticality.py
                                     [-h]
                                     &nbsp;--gen_database  [GEN_DATA]
                                     &nbsp;--out_database [OUT_DATA]
                                     &nbsp;--database [ERROR_DATABASE]
                                     &nbsp;--benchmarks [BENCHMARKS]
                                     &nbsp;--parse_layers
                                     &nbsp;--pr_threshold [PR_THRESHOLD]
                                     &nbsp;--check_csv &nbsp;--ecc &nbsp;--is_fi

Parse logs for Neural Networks

arguments:

  -h, --help            show this help message and exit

### Flags for database generation

  --gen_database <GEN_DATA>

                        If this flag is passed, the other flags will have no
                        effects, despite out_database.
                        --gen_data <path where the parser must search
                        for ALL LOGs FILES

  --out_database <OUT_DATA>

                        The output database name. If gen_database is used,
                        this flag will set the filename for the generated database.
                        The default filename is ./error_log_database.

### Flags for error parser

  --database <ERROR_DATABASE>

                        Where database is located


  --benchmarks <BENCHMARKS>

                        A list separated by ',' (commas with no space) where
                        each item will be the benchmarks that parser will
                        process. Available parsers:

                        * Darknet --> needs --parse_layers and a Precision and Recall threshold value, only for DarknetV1 logs from 2016.
                        * DarknetV1 -->  needs --parse_layers and a Precision and Recall threshold value. For DarknetV1 logs after 2017
                        * DarknetV2 --> needs --parse_layers and a Precision and Recall threshold value.
                        * Lenet --> needs --parse_layers and a Precision and Recall threshold value.
                        * Hotspot
                        * GEMM,
                        * HOG --> needs a Precision and Recall threshold value.
                        * lavamd
                        * nw
                        * quicksort
                        * accl
                        * PyFasterRCNN --> needs a Precision and Recall threshold value.
                        * Lulesh
                        * LUD
                        * mergesort


  --parse_layers

                        If you want to parse Darknet layers, set it True, default
                        values is False

  --pr_threshold <PR_THRESHOLD>

                        Precision and Recall threshold value,0 - 1, default
                        value is 0.5

  --check_csv

                        This parameter will open a csv file which contains all
                        radiation test runs, then it will check if every SDC
                        is on a valid run, the default is false


  --ecc

                        If the boards have ecc this is passed, otherwise
                        nothing must be passed

  --is_fi

                        if it is a fault injection log processing

  --err_hist

                        This parameter will generate an histogram for a serie of error thresholds,
                        these error thresholds are calculated using ERROR_RELATIVE_HISTOGRAM dict values
                        (set on Parameters.py)




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
