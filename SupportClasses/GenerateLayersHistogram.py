#!/usr/bin/env python
import csv

import numpy as np
import struct
import os

class GenerateLayersHistogram():

    csvFilePath = ""
    csvFile = None
    writer = None
    finalInfo = []

    def __init__(self, **kwargs):
        self.csvFilePath = kwargs.pop("csvFile")
        fieldnames = kwargs.pop("fieldnames")
        fileExists = os.path.isfile(self.csvFilePath)

        self.csvFile = open(self.csvFilePath, "a")
        self.writer = csv.DictWriter(self.csvFile, fieldnames=fieldnames, delimiter=';')

        if not fileExists:
            self.writer.writeheader()

    def closeCsv(self):
        self.csvFile.close()

    __layerDimentions = {
        0: [608, 608, 32],
        1: [304, 304, 32],
        2: [304, 304, 64],
        3: [152, 152, 64],
        4: [152, 152, 128],
        5: [152, 152, 64],
        6: [152, 152, 128],
        7: [76, 76, 128],
        8: [76, 76, 256],
        9: [76, 76, 128],
        10: [76, 76, 256],
        11: [38, 38, 256],
        12: [38, 38, 512],
        13: [38, 38, 256],
        14: [38, 38, 512],
        15: [38, 38, 256],
        16: [38, 38, 512],
        17: [19, 19, 512],
        18: [19, 19, 1024],
        19: [19, 19, 512],
        20: [19, 19, 1024],
        21: [19, 19, 512],
        22: [19, 19, 1024],
        23: [19, 19, 1024],
        24: [19, 19, 1024],
        25: [0, 0, 0],
        26: [38, 38, 64],
        27: [19, 19, 256],
        28: [0, 0, 0],
        29: [19, 19, 1024],
        30: [19, 19, 425],
        31: [0, 0, 0]
    }

    def tupleToArray(self, layerContents, layerSize):
        layer = np.ndarray(shape=(layerSize), dtype=float)
        for i in range(0, layerSize):
            layer[i] = layerContents[i]
        return layer

    # returns the opened layers if files were found
    # an empty dict otherwise
    def openLayersImg(self, imgNumber, layersFilePath, imgName):
        lineDict = {}
        for i in self.__layerDimentions:
            goldName = layersFilePath + "gold_layer_" + str(i) + "_img_" + str(imgNumber) + "_test_it_0.layer"
            width, height, depth = self.__layerDimentions[i]
            layerSize = width * height * depth

            fi = open(goldName, "rb")
            logLayerContents = struct.unpack('f' * layerSize, fi.read(4 * layerSize))
            logLayerArray = self.tupleToArray(layerContents=logLayerContents, layerSize=layerSize)
            fi.close()

            # calculate the min an max values
            sortedArray = np.sort(logLayerArray, kind='mergesort')

            if layerSize > 0:
                lineDict[i] = {'min': sortedArray[0], 'max': sortedArray[len(sortedArray) - 1], 'imgNumber': imgNumber, 'imgName':imgName.rstrip(), 'layer':i}
            else:
                lineDict[i] = {'min': 0, 'max': 0, 'imgNumber': imgNumber, 'imgName':imgName.rstrip(), 'layer':i}

        return lineDict

    def writeToCSV(self):
        # for i in self.lineDict:
        #     # print self.lineDict[i]
        #     self.writer.writerow(self.lineDict[i])
        localMin = {}
        localMax = {}

        for i in self.finalInfo:
            for j in xrange(0,32):
                min_l = i[j]['min']
                max_l = i[j]['max']
                if localMin[j] > min_l:
                    localMin[j] = i[j]

                if localMax[j] < max_l:
                    localMax[j] = i[j]

        for i in localMax:
            self.writer.writerow(localMax[i])

        self.writer.writerow({'min': "Min values", 'max': "", 'imgNumber': "", 'imgName': "", 'layer':""})

        for i in localMin:
            self.writer.writerow(localMin[i])


    def generateInfo(self, lines, layers):
        for i, line in enumerate(lines):
            print "Processing layers from img:", line.rstrip() , "i:", i
            # hist.writeToCSV(i, layersPath, line)
            self.finalInfo.append(hist.openLayersImg(i, layers, line))


###########################################
# MAIN
###########################################'

if __name__ == '__main__':
    # to set vars
    csvFilePath = "temp.csv"
    layersPath = "temp_layers/"
    texts = ["temp.txt"]
            # "/home/carol/radiation-benchmarks/data/networks_img_list/caltech.pedestrians.1K.txt",]
             # "/home/carol/radiation-benchmarks/data/networks_img_list/voc.2012.1K.txt",
             # "/home/carol/radiation-benchmarks/data/networks_img_list/caltech.pedestrians.critical.1K.txt"]

    ##################
    fieldnames = ['min', 'max', 'imgNumber', 'imgName', 'layer']
    hist = GenerateLayersHistogram(csvFile=csvFilePath, fieldnames=fieldnames)

    for txtList in texts:
        # read lines
        lines = open(txtList, "r").readlines()
        hist.generateInfo(lines, layersPath)

    hist.writeToCSV()

    hist.closeCsv()
