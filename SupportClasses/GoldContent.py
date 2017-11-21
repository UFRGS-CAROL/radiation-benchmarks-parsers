import copy
import csv
import math
import pickle
from ctypes import *
import numpy as np

# from SupportClasses
import Rectangle

"""Read a darknet/pyfaster/resnet Gold content to memory"""


class Float(Structure):
    _fields_ = [('f', c_float)]

    def __repr__(self):
        return str(self.f)


class Box(Structure):
    _fields_ = [('x', c_float), ('y', c_float), ('w', c_float), ('h', c_float)]

    def __repr__(self):
        return str(self.x) + " " + str(self.y) + " " + str(self.w) + " " + str(self.h)


class Long(Structure):
    _fields_ = [('l', c_long)]

    def __repr__(self):
        return str(self.l)


class Point(object):
    x = 0
    y = 0

    def __init__(self, x, y):
        self.x = x
        self.y = y


class GoldContent():
    __plistSize = 0
    __classes = 0
    __totalSize = 0
    __prob_array = {}
    __pyFasterGold = []

    # args->thresh,
    #  args->hier_thresh, img_list_size, args->img_list_path,
    #  args->config_file, args->cfg_data, args->model, args->weights,
    #                   total, classes

    # for darknetv2
    __thesh = 0
    __hierThresh = 0
    __configFile = ''
    __cfgData = ''
    __model = ''
    __weights = ''
    __imgListPath = ''
    __nn = None
    __csvGoldFilePath = ''
    __pyFasterImgList = ''


    # imgs, doing it there is no need to open img list file
    __imgsLocationList = []

    # return a dict that look like this
    # //to store all gold filenames
    # typedef struct gold_pointers {
    # //	box *boxes_gold;
    # //	ProbArray pb;
    # 	ProbArray *pb_gold;
    # 	long plist_size;
    # 	FILE* gold;
    # 	int has_file;
    # } GoldPointers;
    #
    def __init__(self, **kwargs):
        # use keyargs
        try:
            self.__nn = kwargs.pop("nn")
            self.__csvGoldFilePath = kwargs.pop("filepath")

            if "darknet" == self.__nn:
                self.darknetConstructor(filePath=self.__csvGoldFilePath)
            elif "pyfaster" == self.__nn:
                self.pyFasterConstructor(filePath=self.__csvGoldFilePath)

            elif "darknetv2" == self.__nn:
                self.darknetV2Constructor(filePath=self.__csvGoldFilePath)

            elif "resnet" == self.__nn:
                self.resnetConstructor(filePath=self.__csvGoldFilePath)

            elif "darknetv1" == self.__nn:
                self.darknetV2Constructor(filePath=self.__csvGoldFilePath)

        except:
            raise

    def getTotalSize(self):
        return self.__totalSize

    def getThresh(self):
        return self.__thesh

    def getPlistSize(self):
        return self.__plistSize

    def getClasses(self):
        return self.__classes

    def getPyFasterGold(self):
        return self.__pyFasterGold

    def getImgListPath(self):
        return self.__imgListPath

    def getImgsLocationList(self):
        return self.__imgsLocationList

    def getGoldCsvName(self):
        return self.__csvGoldFilePath

    def getRectArray(self, **kwargs):
        if self.__nn == 'darknetv2' or self.__nn == 'darknetv1':
            imgPath = kwargs.pop('imgPath')
            return self.__prob_array[imgPath]['boxes']
        elif self.__nn == 'darknet':
            imgPos = int(kwargs.pop('imgPos'))
            return self.__prob_array['boxes'][imgPos]


        return self.__prob_array['boxes']

    def getIndexes(self, **kwargs):
        if self.__nn == 'resnet':
            imgPath = kwargs.pop('imgPath')
            return self.__prob_array[imgPath]['indexes']

    def getProbArray(self, **kwargs):
        if self.__nn == 'darknetv2':
            imgPath = kwargs.pop('imgPath')
            return self.readProbsAndBoxesV2(None, imgPath)
        elif self.__nn == 'darknetv1':
            imgPath = kwargs.pop('imgPath')
            return self.__prob_array[imgPath]['probs']
        elif self.__nn == 'resnet':
            imgPath = kwargs.pop('imgPath')
            return self.__prob_array[imgPath]['probs']
        elif self.__nn == 'darknet':
            imgPos = int(kwargs.pop('imgPos'))
            return self.__prob_array['probs'][imgPos]


    def getImgDim(self, **kwargs):
        h = 0
        w = 0
        c = 0
        if self.__nn == 'darknetv2' or self.__nn == 'darknetv1':
            imgPath = kwargs.pop('imgPath')
            h, w, c = self.__prob_array[imgPath]['h'], \
                      self.__prob_array[imgPath]['w'], self.__prob_array[imgPath]['c']

        return h, w, c

    def darknetConstructor(self, filePath):
        cc_file = open(filePath, 'rb')
        result = []
        # darknet write file in this order, so we need recover data in this order
        # long plist_size;
        # long classes;
        # long total_size;
        # for ( < plist_size times >){
        # -----pb_gold.boxes
        # -----pb_gold.probs
        # }
        plist_size = Long()
        classes = Long()
        total_size = Long()
        cc_file.readinto(plist_size)
        cc_file.readinto(classes)
        cc_file.readinto(total_size)
        plist_size = long(plist_size.l)
        classes = long(classes.l)
        total_size = long(total_size.l)
        i = 0
        self.__plistSize = plist_size
        self.__classes = classes
        self.__totalSize = total_size
        self.__prob_array["boxes"] = []
        self.__prob_array["probs"] = []

        while i < long(plist_size):
            # boxes has total_size size
            boxes = self.readBoxes(cc_file, total_size)
            probs = self.readProbs(cc_file, total_size, classes)
            self.__prob_array["probs"].append(probs)
            self.__prob_array["boxes"].append(boxes)
            i += 1

        cc_file.close()

    def pyFasterConstructor(self, filePath):
        try:
            f = open(filePath, "rb")
            tempGold = pickle.load(f)
            f.close()

        except:
            raise
        self.__pyFasterGold = tempGold

    def __copy__(self):
        return copy.deepcopy(self)

    def readBoxes(self, cc_file, n):
        i = 0
        boxes = np.empty(n, dtype=object)
        while i < n:
            box = Box()
            cc_file.readinto(box)
            # instead boxes I put the Rectangles to make it easy
            # (self, x, y, height, width, br_x, br_y):
            # x_min_gold = x_max_gold - gold[i].width;
            # y_min_gold = y_max_gold - gold[i].height;
            # left, top, right, bottom):
            left = int(box.x)
            bottom = int(box.y)
            h = int(box.h)
            w = int(box.w)
            boxes[i] = Rectangle.Rectangle(left, bottom, w, h)
            i += 1
        return boxes

    def readProbs(self, cc_file, total_size, classes):
        i = 0
        prob = np.empty((total_size, classes), dtype=object)

        while i < total_size:
            j = 0
            while j < classes:
                pb_ij = Float()
                cc_file.readinto(pb_ij)
                prob[i][j] = float(pb_ij.f)
                j += 1
            i += 1

        return prob

    """
    This method reads a csv file and stores it into
    __prob_array, where it is filled with all data
    about an indexed img detection
    the index is the name o the image itself
    """

    def darknetV2Constructor(self, filePath):
        csvfile = open(filePath, 'rb')

        spamreader = csv.reader(csvfile, delimiter=';')
        header = next(spamreader)
        # args->thresh,
        #  args->hier_thresh, img_list_size, args->img_list_path,
        #  args->config_file, args->cfg_data, args->model, args->weights,
        #                   total, classes);
        self.__thesh = float(header[0])
        self.__hierThresh = float(header[1])
        self.__plistSize = int(header[2])
        self.__imgListPath = str(header[3])
        self.__configFile = str(header[4])
        self.__cfgData = str(header[5])
        self.__model = str(header[6])
        self.__weights = str(header[7])
        self.__totalSize = int(header[8])
        self.__classes = int(header[9])

        for row in spamreader:
            probRes, boxRes = self.readProbsAndBoxesV2(spamreader)
            self.__prob_array[str(row[0])] = {}
            self.__prob_array[str(row[0])]['probs'] = probRes
            self.__prob_array[str(row[0])]['boxes'] = boxRes
            self.__prob_array[str(row[0])]['h'] = int(row[1])
            self.__prob_array[str(row[0])]['w'] = int(row[2])
            self.__prob_array[str(row[0])]['c'] = int(row[3])
            self.__imgsLocationList.append(str(row[0]))

        csvfile.close()

    def readProbsAndBoxesV2(self, spamreader, imgFilename=None):
        prob, boxes = None, None
        if self.__nn == 'darknetv2' and imgFilename:
            csvfile = open(self.__csvGoldFilePath, 'rb')
            spamreader = csv.reader(csvfile, delimiter=';')
            for i in spamreader:
                if imgFilename in i[0]:
                    # print imgFilename
                    break

            prob = np.empty((self.__totalSize, self.__classes), dtype=float)
            boxes = np.empty(self.__totalSize, dtype=object)
            prob.fill(0)
            boxes.fill(0)
            for i in xrange(0, self.__totalSize):
                # prob, b.x, b.y, b.w, b.h, class_);
                line = next(spamreader)

                left = float(line[1])
                bottom = float(line[2])
                w = float(line[3])
                h = float(line[4])
                class_ = int(line[5])

                prob[i][class_] = float(line[0])
                boxes[i] = Rectangle.Rectangle(left, bottom, w, h)
            #     if i == 0:
            #         print left, bottom, w, h, class_
            # print "On read probs and boxes method", prob[0], boxes[0]

            csvfile.close()
        elif self.__nn == 'darknetv2' and imgFilename == None:
            for i in xrange(0, self.__totalSize): next(spamreader)

        elif self.__nn != 'darknetv2':
            prob = np.empty((self.__totalSize, self.__classes), dtype=float)
            boxes = np.empty(self.__totalSize, dtype=object)
            prob.fill(0)
            boxes.fill(0)
            for i in xrange(0, self.__totalSize):
                #prob, b.x, b.y, b.w, b.h, class_);
                line = next(spamreader)
                left = float(line[1])
                bottom = float(line[2])
                w = float(line[3])
                h = float(line[4])
                class_ = int(line[5])

                prob[i][class_] = float(line[0])
                boxes[i] = Rectangle.Rectangle(left, bottom, w, h)


        return prob, boxes

    # ResNET constructor
    def resnetConstructor(self, filePath):
        csvfile = open(filePath, 'rb')
        spamreader = csv.reader(csvfile, delimiter=';')
        header = next(spamreader)

        self.__plistSize = int(header[0])
        for i in xrange(0, self.__plistSize):
            imgHeader = next(spamreader)

            self.__totalSize = int(imgHeader[0])
            img = str(imgHeader[1])

            probs = []
            indexes = []
            for j in xrange(0, self.__totalSize):
                line = next(spamreader)
                probs.append(float(line[0]))
                indexes.append(int(line[1]))

            self.__prob_array[img] = {"probs": probs, "indexes": indexes}

        csvfile.close()


#debug
# temp = GoldContent(nn='darknetv2', filepath='/home/fernando/Dropbox/LANSCE2017/K20_gold/darknet_v2/darknet_v2_gold.voc.2012.1K.csv')
# prob, boxes = temp.getProbArray(imgPath='/home/carol/radiation-benchmarks/data/VOC2012/2010_003258.jpg')
# for i in zip(prob, boxes):
#     if i[0][0]: print i
