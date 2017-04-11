# UFRGS Radiation Benchmarks Parsers

TODO: Write a project description

## Installation

TODO: Describe the installation process

## Usage

TODO: Write usage instructions

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
# to set which benchmarks you need to parse set the parameters on

Parameters.py 

# to run the parser 
#first - create a database
run WriteSdcsErrDatabase.py where all .log files are located

#second
run ./ProcessDatabase.py --database < error database generated file path> --benchmarks <benchmarks list>
#for example if you want run this parser for darknet, gemm and accl
run ./ProcessDatabase.py --database /home/ic_fodao/errors_log_database --benchmarks darknet,gemm,accl

#for HOG, Darknet and PyFasterRCNN some parameters could be set
--pr_threshold Precision and Recall jaccard similarity threshold value, default is 0.5
--parse_layers Parse Darknet corrupted layers


# it must generate some folders with all parsed CSVs
