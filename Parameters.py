############################################################################################
########################OBJECT DETECTION PARSER PARAMETERS##################################
############################################################################################

# IMG_OUTPUT_DIR is the directory to where the images with error comparisons will be saved
# IMG_OUTPUT_DIR = '/tmp/img_darknet_v3_errors'
IMG_OUTPUT_DIR = ''

GOLD_BASE_DIR = {
    # 'carol-ECC-ON': '/home/fernando/Dropbox/UFRGS/Pesquisa/fault_injections/sassifi_darknet_v2/',
    # 'carol-k401-ECC-OFF': '/home/fernando/Dropbox/LANSCE2017/K40_gold',
    # 'carol-k201-ECC-OFF': '/home/fernando/Dropbox/LANSCE2017/K20_gold',
    'carol-k401': '/home/fernando/Dropbox/LANSCE2017/K40_gold',
    'carol-k201': '/home/fernando/Dropbox/LANSCE2017/K20_gold',
    'carol-tx': '/home/fernando/Dropbox/UFRGS/Pesquisa/Teste_12_2016/GOLD_TITAN',
    'carol-k402': '/home/fernando/Dropbox/UFRGS/Pesquisa/Teste_12_2016/GOLD_K40',
    'carolx1b': '/home/fernando/Dropbox/UFRGS/Pesquisa/Teste_12_2016/GOLD_X1/tx1b',
    'carolx1c': '/home/fernando/Dropbox/UFRGS/Pesquisa/Teste_12_2016/GOLD_X1/tx1c',
    'carolx1a': '/home/fernando/Dropbox/UFRGS/Pesquisa/Teste_12_2016/GOLD_X1/tx1c',
    'caroltitanx1': '/home/fernando/Dropbox/Voltas_LANSCE2018/V2_darknet_data'
}

############################################################################################
#################################DARKNET PARSER PARAMETERS##################################
############################################################################################
"""This section MUST BE SET ACCORDING THE GOLD PATHS"""

DARKNET_DATASETS = {'caltech.pedestrians.critical.1K.txt': {'dumb_abft': 'gold.caltech.critical.abft.1K.test',
                                                            'no_abft': 'gold.caltech.critical.1K.test'},
                    'caltech.pedestrians.1K.txt': {'dumb_abft': 'gold.caltech.abft.1K.test',
                                                   'no_abft': 'gold.caltech.1K.test'},
                    'voc.2012.1K.txt': {'dumb_abft': 'gold.voc.2012.abft.1K.test', 'no_abft': 'gold.voc.2012.1K.test'}}

LAYERS_GOLD_PATH_DARKNETV1 = '/media/fernando/ed3cae20-d686-4879-a851-dd813aea60ca/home/carol/data_lansce_2017_darknet/data_v1'
LAYERS_PATH_DARKNETV1 = '/media/fernando/ed3cae20-d686-4879-a851-dd813aea60ca/home/carol/data_lansce_2017_darknet/data_v1'

LAYERS_GOLD_PATH_DARKNETV2 = '/media/fernando/ed3cae20-d686-4879-a851-dd813aea60ca/home/carol/data_lansce_2017_darknet/data_v2'
LAYERS_PATH_DARKNETV2 = '/media/fernando/ed3cae20-d686-4879-a851-dd813aea60ca/home/carol/data_lansce_2017_darknet/data_v2'

############################################################################################
###############################FASTER RCNN PARSER PARAMETERS################################
############################################################################################

FASTER_RCNN_DATASETS = {
    # normal
    'caltech.pedestrians.critical.1K.txt': 'gold.caltech.critical.1K.test',
    'caltech.pedestrians.1K.txt': 'gold.caltech.1K.test',
    'voc.2012.1K.txt': 'gold.voc.2012.1K.test'
}

############################################################################################
################################## HOG PARSER PARAMETERS ###################################
############################################################################################
HOG_GOLD_BASE_DIR = "/home/fernando/Dropbox/UFRGS/Pesquisa/fault_injections/sassifi_results_new/golds/histogram_ori_gradients/"
HOG_DATASETS = 'urbanstreet'

############################################################################################
#####################################LENET PARSER PARAMETERS################################
############################################################################################

LENET_DATASETS = {
    '': '',
    'test': 'foi',
}

LAYERS_GOLD_PATH_LENET = "/home/fernando/Dropbox/UFRGS/Pesquisa/fault_injections/sassifi_lenet/"
LAYERS_PATH_LENET = "/home/fernando/Dropbox/UFRGS/Pesquisa/fault_injections/sassifi_lenet/"

############################################################################################
####################################RESNET PARSER PARAMETERS################################
############################################################################################

RESNET_CLASSES_PATH = "../src/cuda/resnet_torch/fb.resnet.torch/pretrained/imagenet.lua"
# "/home/fernando/git_pesquisa/radiation-benchmarks/src/cuda/resnet_torch/fb.resnet.torch/pretrained/imagenet.lua"

############################################################################################
#################################OVERALL PARAMETERS ########################################
############################################################################################
LOCAL_RADIATION_BENCH = '/mnt/4E0AEF320AEF15AD/radiation-benchmarks'

# if var check_csvs is true this values must have the csvs datapath
# _ecc_on is mandatory only for boards that have ecc memory
SUMMARIES_FILES = {
    'carol-k401-ECC-OFF': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},
    'carol-k201-ECC-OFF': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},
    'carol-k401-ECC-ON': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},
    'carol-k201-ECC-ON': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},

    'caroltx2a-ECC-OFF': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},

    'caroltx2a': {
        'csv': '/home/fernando/Dropbox/LANSCE2017/LANSCE2017_results/logs_parsed'
               '/summaries-fission.csv', 'data': None},

    'carol-tx': '', 'data': None,
    'carol-k402': '', 'data': None
}

# --- new ERROR Threshold method
ERROR_RELATIVE_HISTOGRAM = {
    # SET THESE FOR THE FINAL HISTOGRAM CSV
    # precision and limitrange will be multiplied to generate all possible limits
    "PRECISION": 10,
    "LIMIT_RANGE": 10,

}

###############################################################################################


# set all benchmarks to be parsed here
radiationBenchmarks = {}


def setBenchmarks(**kwargs):
    benchmarks = kwargs.pop("benchmarks")
    pr_threshold = float(kwargs.pop("pr_threshold"))
    parse_layers = bool(kwargs.pop("parse_layers"))
    checkCsv = SUMMARIES_FILES if bool(kwargs.pop("check_csv")) else None
    ecc = bool(kwargs.pop("ecc"))
    isFi = bool(kwargs.pop("is_fi"))
    err_hist = bool(kwargs.pop('parse_err_histogram'))
    if err_hist:
        parse_err_histogram = ERROR_RELATIVE_HISTOGRAM
    else:
        parse_err_histogram = None

    # I wish that importing only the selected benchmarks
    # will make things faster
    print "Parsing for: ",
    for i in benchmarks:
        benchObj = None
        print i,
        # darknet is the first version of tested darknet, until master degree dissertation
        if i == 'darknet':
            from ParsersClasses import DarknetParser
            benchObj = DarknetParser.DarknetParser(parseLayers=parse_layers,
                                                   prThreshold=pr_threshold,
                                                   layersGoldPath=LAYERS_GOLD_PATH_DARKNETV1,
                                                   layersPath=LAYERS_PATH_DARKNETV1,
                                                   imgOutputDir=IMG_OUTPUT_DIR,
                                                   localRadiationBench=LOCAL_RADIATION_BENCH,
                                                   check_csv=checkCsv,
                                                   ecc=ecc,
                                                   is_fi=isFi,
                                                   goldBaseDir=GOLD_BASE_DIR,
                                                   datasets=DARKNET_DATASETS
                                                   )

        if i == 'darknetv1':
            from ParsersClasses import DarknetV1Parser
            benchObj = DarknetV1Parser.DarknetV1Parser(parseLayers=parse_layers,
                                                       prThreshold=pr_threshold,
                                                       layersGoldPath=LAYERS_GOLD_PATH_DARKNETV1,
                                                       layersPath=LAYERS_PATH_DARKNETV1,
                                                       imgOutputDir=IMG_OUTPUT_DIR,
                                                       localRadiationBench=LOCAL_RADIATION_BENCH,
                                                       check_csv=checkCsv,
                                                       goldBaseDir=GOLD_BASE_DIR,
                                                       datasets=DARKNET_DATASETS
                                                       )
        if i == 'darknetv2':
            from ParsersClasses import DarknetV2Parser
            benchObj = DarknetV2Parser.DarknetV2Parser(parseLayers=parse_layers,
                                                       prThreshold=pr_threshold,
                                                       layersGoldPath=LAYERS_GOLD_PATH_DARKNETV2,
                                                       layersPath=LAYERS_PATH_DARKNETV2,
                                                       imgOutputDir=IMG_OUTPUT_DIR,
                                                       localRadiationBench=LOCAL_RADIATION_BENCH,
                                                       check_csv=checkCsv,
                                                       goldBaseDir=GOLD_BASE_DIR,
                                                       datasets=DARKNET_DATASETS
                                                       )
        if i in ['darknet_v3_single', 'darknet_v3_half', 'darknet_v3_double']:
            from ParsersClasses import DarknetV3Parser
            benchObj = DarknetV3Parser.DarknetV3Parser(prThreshold=pr_threshold,
                                                       imgOutputDir=IMG_OUTPUT_DIR,
                                                       localRadiationBench=LOCAL_RADIATION_BENCH,
                                                       check_csv=checkCsv,
                                                       goldBaseDir=GOLD_BASE_DIR,
                                                       datasets=DARKNET_DATASETS
                                                       )

        if i == 'resnet':
            from ParsersClasses import ResnetParser
            benchObj = ResnetParser.ResnetParser(imgOutputDir=IMG_OUTPUT_DIR,
                                                 prThreshold=pr_threshold,
                                                 localRadiationBench=LOCAL_RADIATION_BENCH,
                                                 check_csv=checkCsv,
                                                 goldBaseDir=GOLD_BASE_DIR,
                                                 datasets=DARKNET_DATASETS,
                                                 classes_path=RESNET_CLASSES_PATH)

        elif i == 'hotspot':
            from ParsersClasses import HotspotParser
            benchObj = HotspotParser.HotspotParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                   check_csv=checkCsv,
                                                   ecc=ecc,
                                                   parse_err_histogram=parse_err_histogram)
        elif i == 'hog':
            from ParsersClasses import HogParser
            benchObj = HogParser.HogParser(
                prThreshold=pr_threshold,
                imgOutputDir=IMG_OUTPUT_DIR,
                localRadiationBench=LOCAL_RADIATION_BENCH,
                check_csv=checkCsv,
                ecc=ecc,
                goldBaseDir=HOG_GOLD_BASE_DIR,
                datasets=HOG_DATASETS
            )
        elif i == 'lavamd':
            from ParsersClasses import LavaMDParser
            benchObj = LavaMDParser.LavaMDParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                 check_csv=checkCsv,
                                                 ecc=ecc,
                                                 parse_err_histogram=parse_err_histogram)
        elif i == 'mergesort':
            from ParsersClasses import MergesortParser
            benchObj = MergesortParser.MergesortParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                       check_csv=checkCsv,
                                                       ecc=ecc)
        elif i == 'nw':
            from ParsersClasses import NWParser
            benchObj = NWParser.NWParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                         check_csv=checkCsv,
                                         ecc=ecc,
                                         parse_err_histogram=parse_err_histogram)
        elif i == 'quicksort':
            from ParsersClasses import QuicksortParser
            benchObj = QuicksortParser.QuicksortParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                       check_csv=checkCsv,
                                                       ecc=ecc)
        elif i == 'accl':
            from ParsersClasses import ACCLParser
            benchObj = ACCLParser.ACCLParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                             check_csv=checkCsv,
                                             ecc=ecc,
                                             parse_err_histogram=parse_err_histogram)
        elif i == 'pyfasterrcnn':
            from ParsersClasses import FasterRcnnParser
            benchObj = FasterRcnnParser.FasterRcnnParser(
                prThreshold=pr_threshold,
                imgOutputDir=IMG_OUTPUT_DIR,
                localRadiationBench=LOCAL_RADIATION_BENCH,
                check_csv=checkCsv,
                ecc=ecc,
                is_fi=isFi,
                goldBaseDir=GOLD_BASE_DIR,
                datasets=FASTER_RCNN_DATASETS
            )
        elif i == 'lulesh':
            from ParsersClasses import LuleshParser
            benchObj = LuleshParser.LuleshParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                 check_csv=checkCsv,
                                                 ecc=ecc,
                                                 parse_err_histogram=parse_err_histogram)
        elif i == 'lud':
            from ParsersClasses import LudParser
            benchObj = LudParser.LudParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                           check_csv=checkCsv,
                                           ecc=ecc,
                                           parse_err_histogram=parse_err_histogram)
        elif i == 'gemm':
            from ParsersClasses import GemmParser
            benchObj = GemmParser.GemmParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                             check_csv=checkCsv,
                                             ecc=ecc,
                                             parse_err_histogram=parse_err_histogram)
        elif i == 'lenet':
            from ParsersClasses import LenetParser
            benchObj = LenetParser.LenetParser(parseLayers=parse_layers,
                                               prThreshold=pr_threshold,
                                               layersGoldPath=LAYERS_GOLD_PATH_LENET,
                                               layersPath=LAYERS_PATH_LENET,
                                               imgOutputDir=IMG_OUTPUT_DIR,
                                               localRadiationBench=LOCAL_RADIATION_BENCH,
                                               check_csv=checkCsv,
                                               ecc=ecc,
                                               is_fi=isFi,
                                               goldBaseDir=GOLD_BASE_DIR,
                                               datasets=LENET_DATASETS)
        elif i == 'beziersurface':
            from ParsersClasses import BezierSurfaceParser
            benchObj = BezierSurfaceParser.BezierSurfaceParser(localRadiationBench=LOCAL_RADIATION_BENCH,
                                                               check_csv=checkCsv,
                                                               ecc=ecc,
                                                               parse_err_histogram=parse_err_histogram)

        elif i == 'gaussian':
            from ParsersClasses import GaussianParser
            benchObj = GaussianParser.GaussianParser()

        elif benchObj == None:
            print "\nERROR: ", i, " is not in the benchmark list, this will probaly crash the system"

        radiationBenchmarks[i] = benchObj

    print ""
