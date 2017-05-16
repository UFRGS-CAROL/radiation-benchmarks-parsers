#!/usr/bin/env python
import csv

import numpy as np
import struct


class GenerateLayersHistogram():
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
        retDict = {}
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
                retDict[i] = {'min': sortedArray[0], 'max': sortedArray[len(sortedArray) - 1], 'imgNumber': imgNumber, 'imgName':imgName}
            else:
                retDict[i] = {'min': 0, 'max': 0, 'imgNumber': imgNumber, 'imgName':imgName}



        return retDict


###########################################
# MAIN
###########################################'

if __name__ == '__main__':
    hist = GenerateLayersHistogram()
    texts = ["/home/carol/radiation-benchmarks/data/networks_img_list/caltech.pedestrians.1K.txt",
             "/home/carol/radiation-benchmarks/data/networks_img_list/voc.2012.1K.txt",
             "/home/carol/radiation-benchmarks/data/networks_img_list/caltech.pedestrians.critical.1K.txt"]
    layersPath = ""
    csvFilePath = "temp.csv"
    csvFile = open(csvFilePath, "a")
    fieldnames = ['min', 'max', 'imgNumber', 'imgName']
    writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
    writer.writeheader()
    for txtList in texts:
        # read lines
        lines = open(txtList, "r").readlines()

        for i, line in enumerate(lines):
            dict = hist.openLayersImg(i, layersPath, line)
            writer.writerow(dict)
