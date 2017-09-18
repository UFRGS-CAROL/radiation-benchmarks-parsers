from collections import Counter
import os

import numpy as np
from sklearn.metrics import precision_recall_curve
from ObjectDetectionParser import ObjectDetectionParser
from SupportClasses import _GoldContent
import re
import csv



# 0 to 9 digits
MAX_LENET_ELEMENT = 9.0


class ResnetParser(ObjectDetectionParser):
    __weights = None

    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "precision",
                  "recall", "false_negative", "false_positive", "true_positive", "header"]

    _classes = None
    _topOnesSize = 5

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)

        self._sizeOfDNN = 200
        classesPath = kwargs.pop("classes_path")
        self._classes = self.__loadClasses(classesPath)



    def _writeToCSV(self, csvFileName):
        self._writeCSVHeader(csvFileName)

        try:
            csvWFP = open(csvFileName, "a")
            writer = csv.writer(csvWFP, delimiter=';')
            outputList = [self._logFileName,
                          self._machine,
                          self._benchmark,
                          self._sdcIteration,
                          self._accIteErrors,
                          self._iteErrors,
                          self._goldLines,
                          self._detectedLines,
                          self._wrongElements,
                          self._precision,
                          self._recall,
                          self._falseNegative,
                          self._falsePositive,
                          self._truePositive,
                          self._header]


            writer.writerow(outputList)
            csvWFP.close()

        except:
            print "\n Crash on log ", self._logFileName

    def setSize(self, header):
        # gold_file: gold_test weights: ./lenet.weights iterations: 10
        # HEADER model: resnet-200.t7
        #  img_list_txt: /home/carol/radiation-benchmarks/data/networks_img_list//caltech.pedestrians.1K.txt
        #  gold_file: /home/carol/radiation-benchmarks/data/resnet_torch/gold.caltech.1K.csv
        resnetM = re.match(".*model\: (\S+).*img_list_txt\: (\S+).*gold_file\: (\S+).*", header)

        if resnetM:
            self.__weights = str(resnetM.group(1))
            self._imgListPath = str(resnetM.group(2))
            self._goldFileName = str(resnetM.group(3))
        else:
            self.__weights = ""
            self._imgListPath = ""
            self._goldFileName = ""

        self._size = self.__weights + "_" + os.path.basename(self._imgListPath) + "_" + os.path.basename(self._goldFileName)


    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        if len(errString) == 0:
            return
        ret = {}
        #ERR img: [/home/carol/radiation-benchmarks/data/CALTECH/set08_V001_346.jpg]
        #  iteration: [0] found_prob: [0.000001] gold_prob: [0.000001]
        # found_index: [828] gold_index: [363]
        resnetM = re.match(".*img\: \[(\S+)\].*iteration\: \[(\d+)\].*found_prob\: \[(\S+)\].*gold_prob\: \[(\S+)\].*"
                           "found_index\: \[(\d+)\].*gold_index\: \[(\d+)\].*", errString)

        if resnetM:
            i = 1
            ret["img"] = resnetM.group(i)
            i += 1
            ret["iteration"] = int(resnetM.group(i))
            i += 1
            try:
                ret["found_pb"] = float(resnetM.group(i))
            except:
                ret["found_pb"] = 1e10

            i += 1
            try:
                ret["gold_pb"] = float(resnetM.group(i))
            except:
                ret["gold_pb"] = 1e10

            i += 1
            ret["found_index"] = int(resnetM.group(i))
            i += 1
            ret["gold_index"] = int(resnetM.group(i))

            if ret["found_index"] > len(self._classes):
                ret["found_index"] = -1

            if ret["gold_index"] > len(self._classes):
                print self._logFileName


        return ret if len(ret) > 0 else None

    def __loadClasses(self, path):
        fileContent = open(path, "r").read()
        temp = fileContent.replace("return{", "")
        temp = temp.replace("}", "")
        classesList = temp.replace("\'", "").split(",")
        retList = [i.lstrip() for i in classesList]

        return retList

    def __sortTwoLists(self, list1, list2):
        # for list
        sorted1, sorted2 = (list(t) for t in zip(*sorted(zip(list1, list2), reverse=True)))
        # for numpy
        # arr1inds = list1.argsort()
        # sorted1 = list1[arr1inds[::-1]]
        # sorted2 = list2[arr1inds[::-1]]
        return sorted1, sorted2


    def __loadGold(self):
        # ---------------------------------------------------------------------------------------------------------------
        # open and load gold
        goldKey = self._machine + "_" + self._benchmark + "_" + self._size

        if self._machine in self._goldBaseDir:
            goldPath = self._goldBaseDir[self._machine] + "/resnet_torch/" + os.path.basename(self._goldFileName)
        else:
            print 'not indexed machine: ', self._machine, " set it on Parameters.py"
            return

        if goldKey not in self._goldDatasetArray:
            g = _GoldContent._GoldContent(nn='resnet', filepath=goldPath)
            self._goldDatasetArray[goldKey] = g

        # ---------------------------------------------------------------------------------------------------------------
        return self._goldDatasetArray[goldKey]


    def __setFoundListBasedOnTestResult(self, classes, probs, classIndex, probToSet):
        for i, class_ in enumerate(classes):
            if class_ == classIndex:
                probs[i] = probToSet


    def _relativeErrorParser(self, errList):
        errListLen = len(errList)
        if errListLen == 0:
            return

        img = errList[0]["img"]

        # open golds
        gold = self.__loadGold()

        goldClasses = list(gold.getIndexes(imgPath=img))
        goldProbs = list(gold.getProbArray(imgPath=img))


        if len([item for item, count in Counter(goldClasses).items() if count > 1]) > 0:
            raise ValueError("Some error because list have duplicated elements: " + str([item for item, count in Counter(goldClasses).items() if count > 1]))


        foundClasses = list(gold.getIndexes(imgPath=img))
        foundProbs = list(gold.getProbArray(imgPath=img))

        # # first set the errors
        # for i in errList:
        #     fIndex = i["found_index"]
        #     fProb = i["found_pb"]
        #     self.__setFoundListBasedOnTestResult(foundClasses, foundProbs, fIndex, fProb)


        # must reorder the found classes and probs
        foundProbsSorted, foundClassesSorted = self.__sortTwoLists(foundProbs, foundClasses)

        if goldProbs != foundProbsSorted or goldClasses != foundClassesSorted:
            print list(set(foundProbs) - set(foundProbsSorted))
            print list(set(foundClasses) - set(foundClassesSorted))
