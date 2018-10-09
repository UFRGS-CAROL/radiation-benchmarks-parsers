import multiprocessing

"""Calculates precision and recall between two sets of rectangles"""


class PrecisionAndRecall(object):
    precision = 0
    recall = 0
    specifity = 0
    falsePositive = 0
    falseNegative = 0
    truePositive = 0
    __threshold = 1

    def __init__(self, threshold):
        manager = multiprocessing.Manager()
        self.__threshold = threshold
        self.precision = manager.Value('f', 0.0)
        self.recall = manager.Value('f', 0.0)
        self.falseNegative = manager.Value('i', 0)
        self.truePositive = manager.Value('i', 0)
        self.falsePositive = manager.Value('i', 0)

    def __repr__(self):
        ret_str = "precision " + str(self.precision) + " recall:" + str(self.recall)
        ret_str += " false positive:" + str(self.falsePositive)
        ret_str += " false negative:" + str(self.falseNegative)
        ret_str += " true positive:" + str(self.truePositive) + " threshold:" + str(self.__threshold)
        return ret_str

    def getPrecision(self):
        return self.precision.value

    def getRecall(self):
        return self.recall.value

    def getFalsePositive(self):
        return self.falsePositive.value

    def getFalseNegative(self):
        return self.falseNegative.value

    def getTruePositive(self):
        return self.truePositive.value

    def cleanValues(self):
        self.precision.value = 0
        self.recall.value = 0
        self.falseNegative.value = 0
        self.truePositive.value = 0
        self.falsePositive.value = 0

    """
    Calculates the precision an recall value, based on Lucas C++ function for HOG
    gold = List of Rectangles
    found = List o Rectangles
    """

    def precisionAndRecallParallel(self, gold, found):
        # print "running in parallel"
        rp = multiprocessing.Process(target=self.recallMethod, args=(gold, found))
        pp = multiprocessing.Process(target=self.precisionMethod, args=(gold, found))
        rp.start()
        pp.start()
        rp.join()
        pp.join()

        if self.truePositive.value + self.falsePositive.value > 0:
            pr_div = float(self.truePositive.value + self.falsePositive.value)
            self.precision.value = float(self.truePositive.value) / pr_div
        else:
            self.precision.value = 0

    """
        split precision for parallelism
    """

    def precisionMethod(self, gold, found):
        # print "passou precision"
        out_positive = 0
        for i in found:
            for g in gold:
                if (g.jaccard_similarity(i)) >= self.__threshold:
                    out_positive += 1
                    break
        self.falsePositive.value = len(found) - out_positive

    """
        split recall for parallelism
    """

    def recallMethod(self, gold, found):
        # print "passou recall"
        for i in gold:
            for z in found:
                if (i.jaccard_similarity(z)) >= self.__threshold:
                    self.truePositive.value += 1
                    break

        self.falseNegative.value = len(gold) - self.truePositive.value
        if self.truePositive.value + self.falseNegative.value > 0:
            self.recall.value = float(self.truePositive.value) / float(
                self.truePositive.value + self.falseNegative.value)
        else:
            self.recall.value = 0

    def precisionAndRecallSerial(self, gold, found):
        # precision
        outPositive = 0
        for i in found:
            for g in gold:
                if (g.jaccard_similarity(i)) >= self.__threshold:
                    outPositive += 1
                    break

        falsePositive = len(found) - outPositive

        # recall
        truePositive = 0
        for i in gold:
            for z in found:
                if (i.jaccard_similarity(z)) >= self.__threshold:
                    truePositive += 1
                    break

        falseNegative = len(gold) - truePositive
        # print "\n", "falsePositive", falsePositive, "falseNegative", falseNegative, "truePositive", truePositive
        recall = float(truePositive) / float(truePositive + falseNegative)

        precision = float(truePositive) / float(truePositive + falsePositive)
        self.falseNegative.value = falseNegative
        self.falsePositive.value = falsePositive
        self.truePositive.value = truePositive
        # print "precision" , precision, "recall" ,recall
        self.precision.value = precision
        self.recall.value = recall

    """
    return x and y pixel cordinates
    """

    def _centerOfMass(self, rectangles):
        xTotal = 0
        yTotal = 0
        pixels = 0
        for r in rectangles:
            # for x in xrange(r.left, r.right + 1):
            #  for y in xrange(r.bottom, r.top + 1):
            xTotal += ((r.bottom - r.top - 1) * (r.left - r.right - 1) * (r.left + r.right)) / 2
            yTotal += ((r.bottom - r.top - 1) * (r.bottom + r.top) * (r.left - r.right - 1)) / 2
            pixels += (r.top - r.bottom + 1) * (r.right - r.left + 1)

        if pixels > 0:
            return ((xTotal) / pixels, (yTotal) / pixels)
        else:
            return 0, 0

    def centerOfMassGoldVsFound(self, gold, found, xSize, ySize):
        xGold, yGold = self._centerOfMass(gold)
        xFound, yFound = self._centerOfMass(found)

        return float(xFound - xGold) / xSize, float(yFound - yGold) / ySize
