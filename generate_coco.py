# -*-coding:utf-8-*-

import os
from xml.etree.ElementTree import dump
import json
import pprint
import random

import argparse


from Format import VOC, COCO, UDACITY, KITTI, YOLO

parser = argparse.ArgumentParser(description='label Converting example.')
parser.add_argument('--datasets', type=str, help='type of datasets')
parser.add_argument('--img_path', type=str, help='directory of image folder')
parser.add_argument('--label', type=str,
                    help='directory of label folder or label file path')
parser.add_argument('--convert_output_path', type=str,
                    help='directory of label folder')
parser.add_argument('--img_type', type=str, help='type of image')
parser.add_argument('--manifest_path', type=str,
                    help='directory of manipast file', default="./")
parser.add_argument('--cls_list_file', type=str,
                    help='directory of *.names file', default="./")
parser.add_argument('--num_samples', type=int,
                    help='min images per class', default=2000)
parser.add_argument('--seed', type=int,
                    help='random seed to use for dataset generation', default=1337)

args = parser.parse_args()

def indexDataset(data):
    """ Builds a dict which maps image file names to the set of classes in each image.

    Returns
    -------
    Dict[str: set[str]]
        Image file name to classes in image mapping. e.g.
        "COCO_val2014_00032.jpg": {"person", "car"}
    """

    # Initialize an empty set for each class
    datasetIndex = {}

    # Iterate through data
    for fileName, imageData in data.items():
        # item is a dict with format documented in Format.py

        # Get all classes which are visible in the scene
        classesInScene = set()
        for objectIndex, objectData in imageData["objects"].items():
            if objectIndex != "num_obj":
                classesInScene.add(objectData["name"])

        datasetIndex[fileName] = classesInScene

    return datasetIndex


def sampleDataset(data, minSamples, classes=set(), seed=None):
    # Use random seed if available for deterministic behaviour. If seed=None,
    # system time is used instead
    random.seed(a=seed)

    datasetIndex = indexDataset(data)

    datasetCount = {className: 0 for className in classes}
    includedData = list()

    keepImageNames = []

    imageNames = list(datasetIndex.keys())

    datasetFull = False
    while len(imageNames) > 0 and not datasetFull:
        # Sample for a random image name
        randIndex = random.randint(0, len(imageNames)-1)
        imageName = imageNames[randIndex]

        # Remove the image name from the list
        del imageNames[randIndex]

        # Get a set of the classes in the image
        classesInImage = datasetIndex[imageName]

        # Check if there is room in this dataset for more samples
        addImage = False
        for className in classesInImage:
            if datasetCount[className] < minSamples:
                addImage = True
                break

        if addImage:
            keepImageNames.append(imageName)
            for className in classesInImage:
                datasetCount[className] += 1

            # Check if dataset is full
            datasetFull = True
            for _, numSamples in datasetCount.items():
                if numSamples < minSamples:
                    datasetFull = False
            print(datasetCount)

    # Construct a new dataset
    newData = {imageName: data[imageName] for imageName in keepImageNames}

    return newData

def main(config):

    if config["datasets"] == "VOC":
        voc = VOC()
        yolo = YOLO(os.path.abspath(config["cls_list"]))

        flag, data = voc.parse(config["label"])

        if flag == True:

            flag, data = yolo.generate(data)
            if flag == True:
                flag, data = yolo.save(data, config["output_path"], config["img_path"],
                                       config["img_type"], config["manifest_path"])

                if flag == False:
                    print("Saving Result : {}, msg : {}".format(flag, data))

            else:
                print("YOLO Generating Result : {}, msg : {}".format(flag, data))

        else:
            print("VOC Parsing Result : {}, msg : {}".format(flag, data))

    elif config["datasets"] == "COCO":
        coco = COCO()

        keep = {
                "person",
                "bicycle",
                "car",
                "motorcycle",
                "bus",
                "train",
                "truck"}

        flag, data, cls_hierarchy = coco.parse(
            config["label"], config["img_path"], keep=keep)

        data = sampleDataset(data, config["num_samples"], keep, config["seed"])

        yolo = YOLO(os.path.abspath(
            config["cls_list"]), cls_hierarchy=cls_hierarchy)

        if flag == True:
            flag, data = yolo.generate(data)

            if flag == True:
                flag, data = yolo.save(data, config["output_path"], config["img_path"],
                                       config["img_type"], config["manifest_path"])

                if flag == False:
                    print("Saving Result : {}, msg : {}".format(flag, data))

            else:
                print("YOLO Generating Result : {}, msg : {}".format(flag, data))

        else:
            print("COCO Parsing Result : {}, msg : {}".format(flag, data))

    elif config["datasets"] == "UDACITY":
        udacity = UDACITY()
        yolo = YOLO(os.path.abspath(config["cls_list"]))

        flag, data = udacity.parse(config["label"])

        if flag == True:
            flag, data = yolo.generate(data)

            if flag == True:
                flag, data = yolo.save(data, config["output_path"], config["img_path"],
                                       config["img_type"], config["manifest_path"])

                if flag == False:
                    print("Saving Result : {}, msg : {}".format(flag, data))

            else:
                print("UDACITY Generating Result : {}, msg : {}".format(flag, data))

        else:
            print("COCO Parsing Result : {}, msg : {}".format(flag, data))

    elif config["datasets"] == "KITTI":
        kitti = KITTI()
        yolo = YOLO(os.path.abspath(config["cls_list"]))

        flag, data = kitti.parse(
            config["label"], config["img_path"], img_type=config["img_type"])

        if flag == True:
            flag, data = yolo.generate(data)

            if flag == True:
                flag, data = yolo.save(data, config["output_path"], config["img_path"],
                                       config["img_type"], config["manifest_path"])

                if flag == False:
                    print("Saving Result : {}, msg : {}".format(flag, data))

            else:
                print("YOLO Generating Result : {}, msg : {}".format(flag, data))

        else:
            print("KITTI Parsing Result : {}, msg : {}".format(flag, data))

    else:
        print("Unkwon Datasets")


if __name__ == '__main__':

    config = {
        "datasets": args.datasets,
        "img_path": args.img_path,
        "label": args.label,
        "img_type": args.img_type,
        "manifest_path": args.manifest_path,
        "output_path": args.convert_output_path,
        "cls_list": args.cls_list_file,
        "num_samples": args.num_samples,
        "seed": args.seed
    }

    main(config)
