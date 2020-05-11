from LavaMDParser import LavaMDParser
from JTX2InstParser import JTX2InstParser


class LavaMDPersistentThreadsParser(LavaMDParser):
    _teperatureMetrics = ["A0_TEMP", "PLL_TEMP", "GPU_TEMP", "CPU_TEMP",
                          "PMIC_TEMP", "TDIODE_TEMP", "TBOARD_TEMP"]

    _powerMetrics = ["IN_POWER", "SYS_SOC_POWER", "SYS_GPU_POWER", "SYS_CPU_POWER",
                     "SYS_DDR_POWER", "MUX_POWER",
                     "5V0_IO_SYS_POWER", "3V3_SYS_POWER"]

    _powerAndTemperatureAverage = None
    _csvFilesPath = ""

    def __init__(self, **kwargs):
        super(LavaMDParser, self).__init__(**kwargs)
        self._csvHeader.extend(self._teperatureMetrics)

        self._csvHeader.extend(self._powerMetrics)
        self._csvFilesPath = kwargs.get("power_temp_file")

    def _relativeErrorParser(self, errList):
        super(LavaMDParser, self)._relativeErrorParser(errList)

        latest_csv = self._csvFilesPath + self._logFileName.replace(".log", "JTX2INST.csv")

        temperature, power, timestamp_start, timestamp_end = JTX2InstParser.parseFile(latest_csv)
        self._powerAndTemperatureAverage = [temperature[t] for t in self._teperatureMetrics] + [power[p] for p in
                                                                                                self._powerMetrics]

    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
                                 self._machine,
                                 self._benchmark,
                                 self._header,
                                 self._sdcIteration,
                                 self._accIteErrors,
                                 self._iteErrors,
                                 self._maxRelErr,
                                 self._minRelErr,
                                 self._avgRelErr,
                                 self._zeroOut,
                                 self._zeroGold,
                                 self._countErrors]

        self._outputListError.extend(self._powerAndTemperatureAverage)
