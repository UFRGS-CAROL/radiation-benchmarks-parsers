from ObjectDetectionParser import ObjectDetectionParser
import re
import os
from SupportClasses import PrecisionAndRecall
from SupportClasses import Rectangle
from SupportClasses import GoldContent
from PIL import Image
from copy import deepcopy


def getImgDim(imgPath):
    im = Image.open(imgPath)
    width, height = im.size
    return width, height


class DarknetV3Parser(ObjectDetectionParser):
    __executionType = None
    __executionModel = None
    __weights = None
    __configFile = None
    _cnnParser = None
    _saveLayer = False
    _tensorCore = 0

    def _placeOutputOnList(self):
        self._outputListError = [self._logFileName,
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
                                 self._precisionClasses,
                                 self._recallClasses,
                                 self._falseNegative,
                                 self._falsePositive,
                                 self._truePositive,
                                 self._abftType,
                                 self._rowDetErrors,
                                 self._colDetErrors,
                                 self._header]

    def setSize(self, header):
        pattern = ".*gold_file\: (\S+).*save_layer\: (\d+).*abft_type\: (\S+).*iterations\: (\d+).*"
        pattern += "tensor_core_mode\: (\d+).*"
        sizeM = re.match(pattern, header)
        if sizeM:
            self._goldFileName = str(sizeM.group(1))
            self._saveLayer = bool(int(sizeM.group(2)))
            self._abftType = str(sizeM.group(3))
            self._iterations = int(sizeM.group(4))
            self._tensorCore = bool(int(sizeM.group(5)))

        self._size = "gold_file_" + os.path.basename(self._goldFileName) + "_save_layer_" + str(
            self._saveLayer) + "_abft_" + str(self._abftType) + "_tensor_core_" + str(self._tensorCore)

    def _relativeErrorParser(self, errList):
        if len(errList) == 0:
            return

        gold = self._loadGold()

        if gold is None:
            return

        # for layers parser
        self._imgListSize = gold.getPlistSize()
        self._imgListPath = gold.getImgListPath()
        self._detectionThreshold = gold.getThresh()

        imgFilename = errList[0]['img']

        goldObjs = gold.getProbArray(imgPath=imgFilename)
        foundObjs = []
        # Copy the contents to found array
        for t in goldObjs:
            probs = t[0][:]
            rect = deepcopy(t[1])
            foundObjs.append([probs, rect])

        for y in errList:
            detection = y['detection']
            if y['type'] == "coord":
                foundObjs[detection][1] = Rectangle.Rectangle(y['x_r'], y['y_r'], y['w_r'], y['h_r'])
            if y['type'] == "prob":
                cls = y['class']
                foundObjs[detection][0][cls] = y['prob_r']

        # before keep going is necessary to filter the results
        w, h = getImgDim(imgPath=imgFilename.replace("/home/carol/radiation-benchmarks", self._localRadiationBench))
        gValidRects, gValidProbs, gValidClasses = self.__filterResults(objs=goldObjs, h=h, w=w)
        fValidRects, gValidProbs, fValidClasses = self.__filterResults(objs=foundObjs, h=h, w=w)

        precisionRecallObj = PrecisionAndRecall.PrecisionAndRecall(self._prThreshold)

        gValidSize = len(gValidRects)
        fValidSize = len(fValidRects)
        if gValidSize > 200 or fValidSize > 200:
            print "\nFuck, it's here", gValidSize, fValidSize
            # for i in xrange(1,10):
            #     print gValidRects[i]
            print h, w
            return

        precisionRecallObj.precisionAndRecallParallel(gValidRects, fValidRects)
        self._precision = precisionRecallObj.getPrecision()
        self._recall = precisionRecallObj.getRecall()

        # Classes precision and recall
        self._precisionAndRecallClasses(fValidClasses, gValidClasses)

        if self._imgOutputDir and (self._precision != 1 or self._recall != 1
                                   or self._precisionClasses != 1 or self._recall != 1):
            drawImgFileName = imgFilename.replace("/home/carol/radiation-benchmarks", self._localRadiationBench)
            gValidRectsDraw = [
                Rectangle.Rectangle(left=int(i.left), bottom=int(i.top), width=int(i.width), height=int(i.height),
                                    right=int(i.right), top=int(i.bottom)) for i in gValidRects]

            fValidRectsDraw = [
                Rectangle.Rectangle(left=int(i.left), bottom=int(i.top), width=int(i.width), height=int(i.height),
                                    right=int(i.right), top=int(i.bottom)) for i in fValidRects]

            self.buildImageMethod(drawImgFileName, gValidRectsDraw, fValidRectsDraw, str(self._sdcIteration)
                                  + '_' + self._logFileName, self._imgOutputDir)

        self._falseNegative = precisionRecallObj.getFalseNegative()
        self._falsePositive = precisionRecallObj.getFalsePositive()
        self._truePositive = precisionRecallObj.getTruePositive()
        # set all
        self._goldLines = gValidSize
        self._detectedLines = fValidSize
        self._wrongElements = abs(gValidSize - fValidSize)

    def _loadGold(self):
        # --------------------------------------------------------------------------------------------------------------
        # open and load gold
        pureMachine = self._machine.split('-ECC')[0]
        goldKey = pureMachine + "_" + self._benchmark + "_" + self._size
        if pureMachine in self._goldBaseDir:
            goldPath = self._goldBaseDir[pureMachine] + "/darknet_v3/" + os.path.basename(self._goldFileName)
        else:
            print 'not indexed machine: ', pureMachine, " set it on Parameters.py"
            return None

        if goldKey not in self._goldDatasetArray:
            g = GoldContent.GoldContent(nn='darknetv3', filepath=goldPath)
            self._goldDatasetArray[goldKey] = g

        return self._goldDatasetArray[goldKey]

    def __filterResults(self, objs, h, w):
        validRectangles = []
        validProbs = []
        validClasses = []

        # probRes, box, objectness, sort_class
        for obj in objs:
            box = obj[1]
            # Keep in mind that it is not the left and botton
            # it is the CENTER of darknet box
            bX = box.left
            bY = box.bottom

            left = (bX - box.width / 2.) * w
            right = (bX + box.width / 2.) * w
            top = (bY + box.height / 2.) * h
            bot = (bY - box.height / 2.) * h

            width = box.width * w
            height = box.height * h

            if width > w - 1:
                width = w - 1

            if height > h - 1:
                height = h - 1

            if left < 0:
                left = 0

            if right > w - 1:
                right = w - 1

            if top < 0:
                top = 0

            if bot > h - 1:
                bot = h - 1

            final_prob = -1000
            final_class = -1
            for i, prob in enumerate(obj[0]):
                if prob > self._detectionThreshold and prob > final_prob:
                    final_prob = prob
                    final_class = i

            rect = Rectangle.Rectangle(left=int(left), bottom=int(bot), width=int(width), height=int(height),
                                       right=int(right), top=int(top))
            validProbs.append(final_prob)
            validClasses.append(final_class)
            validRectangles.append(rect)

        return validRectangles, validProbs, validClasses

    # parse Darknet
    # returns a dictionary
    def parseErrMethod(self, errString):
        # parse errString for darknet
        ret = {}
        if 'ERR' in errString:
            ret = self.__processRect(errString)

        return ret if len(ret) > 0 else None

    # parse Darknet
    # returns a dictionary
    def __processRect(self, errString):
        ret = {}
        # ERR img: /home/carol/radiation-benchmarks/data/CALTECH/set07_V001_881.jpg
        pattern = ".*img\: (\S+)"
        # detection: 0
        pattern += ".*detection\: (\d+)"
        # x_e: 0.5122104 x_r: 0.8423371 y_e: 0.3261115 y_r: 1.008772
        pattern += ".*x_e\: (\S+).*x_r\: (\S+).*y_e\: (\S+).*y_r\: (\S+)"
        # h_e: 0.02655367 h_r: 0.02857633 w_e: 0.011929 w_r: 0.01652152
        pattern += ".*h_e\: (\S+).*h_r\: (\S+).*w_e\: (\S+).*w_r\: (\S+)"
        # objectness_e: 0.5872963 objectness_r: 0.9313526 sort_class_e: 79 sort_class_r: 79
        pattern += ".*objectness_e\: (\S+).*objectness_r\: (\S+).*sort_class_e\: (\d+).*sort_class_r\: (\d+).*"

        darknetM = re.match(pattern, errString)
        if darknetM:
            ret['type'] = "coord"
            i = 1
            ret['img'] = darknetM.group(i)
            i += 1
            ret['detection'] = int(darknetM.group(i))
            i += 1

            # x_e: 0.5122104 x_r: 0.8423371 y_e: 0.3261115 y_r: 1.008772
            try:
                ret["x_e"] = float(darknetM.group(i))
            except:
                ret["x_e"] = 1e10
            i += 1

            try:
                ret["x_r"] = float(darknetM.group(i))
            except:
                ret["x_r"] = 1e10
            i += 1

            try:
                ret["y_e"] = float(darknetM.group(i))
            except:
                ret["y_e"] = 1e10
            i += 1

            try:
                ret["y_r"] = float(darknetM.group(i))
            except:
                ret["y_r"] = 1e10
            i += 1

            # h_e: 0.02655367 h_r: 0.02857633 w_e: 0.011929 w_r: 0.01652152
            try:
                ret["h_e"] = float(darknetM.group(i))
            except:
                ret["h_e"] = 1e10
            i += 1

            try:
                ret["h_r"] = float(darknetM.group(i))
            except:
                ret["h_r"] = 1e10
            i += 1

            try:
                ret["w_e"] = float(darknetM.group(i))
            except:
                ret["w_e"] = 1e10
            i += 1

            try:
                ret["w_r"] = float(darknetM.group(i))
            except:
                ret["w_r"] = 1e10
            i += 1

        # ERR img: /home/carol/radiation-benchmarks/data/CALTECH/set07_V001_881.jpg
        # detection: 3 class: 2 prob_e: 0 prob_r: 0.8630365
        pattern = ".*img\: (\S+)"
        pattern += ".*detection\: (\d+)"
        pattern += ".*class\: (\d+)"
        pattern += ".*prob_e\: (\S+)"
        pattern += ".*prob_r\: (\S+).*"
        darknetM = re.match(pattern, errString)
        if darknetM:
            ret['type'] = "prob"
            ret['img'] = darknetM.group(1)
            ret['detection'] = int(darknetM.group(2))
            ret['class'] = int(darknetM.group(3))
            ret['prob_e'] = float(darknetM.group(4))
            ret['prob_r'] = float(darknetM.group(5))

        return ret
