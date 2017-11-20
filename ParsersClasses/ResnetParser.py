import warnings
from collections import Counter
import os

import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import confusion_matrix
from ObjectDetectionParser import ObjectDetectionParser
from SupportClasses import GoldContent
import re
import csv

# 0 to 9 digits
MAX_LENET_ELEMENT = 9.0


class ResnetParser(ObjectDetectionParser):
    __weights = None

    # overiding csvheader
    _csvHeader = ["logFileName", "Machine", "Benchmark", "SDC_Iteration", "#Accumulated_Errors", "#Iteration_Errors",
                  "gold_lines", "detected_lines", "wrong_elements", "precision",
                  "recall", 'fscore_0.5',
                  "false_negative", "false_positive", "true_positive",  # "true_negative",
                  "header"]

    _classes = None
    _topOnesSize = 5
    _fscore = None

    # _trueNegative = None

    def __init__(self, **kwargs):
        ObjectDetectionParser.__init__(self, **kwargs)

        self._sizeOfDNN = 200
        classesPath = kwargs.pop("classes_path")
        self._classes = self.__loadClasses(classesPath)

        # set resnet threshold
        self._detectionThreshold = 0.1

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
                          self._fscore,
                          self._falseNegative,
                          self._falsePositive,
                          self._truePositive,
                          # self._trueNegative,
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

        self._size = os.path.basename(self.__weights) + "_" + os.path.basename(
            self._imgListPath) + "_" + os.path.basename(
            self._goldFileName)

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        if len(errString) == 0:
            return
        ret = {}
        # ERR img: [/home/carol/radiation-benchmarks/data/CALTECH/set08_V001_346.jpg]
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
        fileContent = open(path, "r").readlines()
        del fileContent[-1]
        del fileContent[0]

        retList = [i.lstrip().replace("\'", "").replace("\n", "").replace(",", "").replace(" ", "-") for i in
                   fileContent]
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
        pureMachine = self._machine.split('-ECC')[0]
        goldKey = pureMachine + "_" + self._benchmark + "_" + self._size
        if pureMachine in self._goldBaseDir:
            goldPath = self._goldBaseDir[pureMachine] + "/resnet_torch/" + os.path.basename(self._goldFileName)
        else:
            print 'not indexed machine: ', pureMachine, " set it on Parameters.py"
            return None

        if goldKey not in self._goldDatasetArray:
            g = GoldContent.GoldContent(nn='resnet', filepath=goldPath)
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

        goldClasses = gold.getIndexes(imgPath=img)
        goldProbs = list(gold.getProbArray(imgPath=img))

        if len([item for item, count in Counter(goldClasses).items() if count > 1]) > 0:
            raise ValueError("Some error because list have duplicated elements: " + str(
                [item for item, count in Counter(goldClasses).items() if count > 1]))

        foundClasses = list(gold.getIndexes(imgPath=img))
        foundProbs = list(gold.getProbArray(imgPath=img))

        # # first set the errors
        for i in errList:
            fIndex = i["found_index"]
            fProb = i["found_pb"]
            self.__setFoundListBasedOnTestResult(foundClasses, foundProbs, fIndex, fProb)

        goldStrClasses = []
        foundStrClasses = []
        for i in goldClasses:
            if goldProbs[i - 1] > self._detectionThreshold:
                goldStrClasses.append(self._classes[i - 1])

        for i in foundClasses:
            if foundProbs[i - 1] > self._detectionThreshold:
                foundStrClasses.append(self._classes[i - 1])

        diffElements = list(set(goldStrClasses) - set(foundStrClasses))
        self._goldLines = len(goldStrClasses)
        self._detectedLines = len(foundStrClasses)
        self._wrongElements = len(diffElements)

        self._falsePositive, self._truePositive, self._falseNegative =  self.__perfMeasure(foundStrClasses, goldStrClasses)

        if self._truePositive + self._falseNegative == 0:
            self._recall = 0
        else:
            self._recall = float(self._truePositive) / float(self._truePositive + self._falseNegative)

        if self._truePositive + self._falsePositive == 0:
            self._precision = 0
        else:
            self._precision = float(self._truePositive) / float(self._truePositive + self._falsePositive)

    def __perfMeasure(self, found, gold):
        # precision
        outPositive = 0
        for i in found:
            for g in gold:
                if g == i: #(g.jaccard_similarity(i)) >= self.__threshold:
                    outPositive += 1
                    break

        falsePositive = len(found) - outPositive

        # recall
        truePositive = 0
        for i in gold:
            for z in found:
                if i == z: #(i.jaccard_similarity(z)) >= self.__threshold:
                    truePositive += 1
                    break

        falseNegative = len(gold) - truePositive
        return falsePositive, truePositive, falseNegative
