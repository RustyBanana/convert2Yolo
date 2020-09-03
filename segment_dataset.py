import os
import argparse
import zipfile

def main():
    parser = argparse.ArgumentParser(description='Segment a labelled dataset into separate datasets by class')
    parser.add_argument('--img_path', type=str, help='directory of image folder')
    parser.add_argument('--img_file_ext', type=str, help='.jpg/.png',
                        default='.jpg')
    parser.add_argument('--label_path', type=str,
                        help='directory of label folder')
    parser.add_argument('--class_list_file', type=str,
                        help='directory of *.names file', default="./")
    parser.add_argument('--class_name', type=str,
                        help='names of classes to segment', default="")
    parser.add_argument('--manifest_path', type=str,
                        help='directory of manipast file', default="./")
    parser.add_argument('--zip_file_path', type=str,
                        help='save images to zip file if set', default="")
    args = parser.parse_args()

    # Map from class name to class index
    classIndexMap = getClassIndexMap(args.class_list_file)

    # Map from class index to class name
    classNameMap = {v: k for k, v in classIndexMap.items()}

    if args.class_name:
        classesToKeep = args.class_name.split(" ")
    else:
        classesToKeep = list(classIndexMap.keys())

    classIndexesToKeep = [classIndexMap[className] for className in classesToKeep]
    classIndexesToKeep = set(classIndexesToKeep)

    # int: List[str] = classIndex: imgPath
    manifestData = {classIndex:[] for classIndex in classIndexesToKeep}

    # int: List[str] = classIndex: labelPath
    # Store label file paths so they can be zipped later if necessary
    labelFilePaths = {classIndex:[] for classIndex in classIndexesToKeep}

    # Is a byte string
    directory = os.fsencode(args.label_path)

    for file in os.listdir(directory):
        # Is a string
        filename = os.fsdecode(file)
        if filename.endswith(".txt"):
            filePath = os.path.join(args.label_path, filename)

            with open(filePath) as labelFile:
                """ Example format:
                    1 0.623 0.277 0.326 0.551
                    3 0.549 0.683 0.903 0.602
                """
                # Extract the class index (first number) from each line
                classIndexes = set()
                for line in labelFile:
                    classIndex = int(line.split(" ", 1)[0])
                    classIndexes.add(classIndex)

                # relative path, e.g. path/to/img_folder/COCO_val2015_000032.jpg
                imgFilePath = args.img_path + filename[:-4] + args.img_file_ext

                # Add imgFilePath to manifest data for the classes to keep
                for classIndex in classIndexes:
                    if classIndex in classIndexesToKeep:
                        manifestData[classIndex].append(imgFilePath)
                        labelFilePaths[classIndex].append(filePath)

    # Save manifest data
    for classIndex, classImgs in manifestData.items():
        manifestFileName = "manifest_" + classNameMap[classIndex] + ".txt"
        manifestFilePath = args.manifest_path + manifestFileName

        labelPaths = labelFilePaths[classIndex]

        # Save manifest file
        with open(manifestFilePath, 'w') as manifestFile:
            manifestFile.write("\n".join(classImgs)+"\n")

        # Zip images into a file
        if args.zip_file_path:
            createZip(classImgs, labelPaths, manifestFilePath, args.class_list_file,
                    f"{args.zip_file_path}/{classNameMap[classIndex]}.zip")

def getClassIndexMap(classListFile):
    """ Get mapping from class name to class index given in classListFile
    Returns
    -------
    "className": classIndex
    e.g. {"person": 0, "car": 2, "truck": 4}
    """
    classIndexMap = {}
    with open(classListFile, 'r') as classFile:
        i = 0
        for line in classFile:
            className = line.strip()
            classIndexMap[className] = i
            i += 1
    
    return classIndexMap

def createZip(imgPaths, labelPaths, manifestPath, classListPath, outputPath):
    zipf = zipfile.ZipFile(outputPath, 'w', zipfile.ZIP_DEFLATED)

    # Write images
    for filePath in imgPaths:
        newFilePath = "images/" + filePath.split('/')[-1]
        zipf.write(filePath, newFilePath)

    # Write labels
    for labelPath in labelPaths:
        newLabelPath = "labels/" + labelPath.split('/')[-1]
        zipf.write(labelPath, newLabelPath)

    # Write manifest
    zipf.write(manifestPath, manifestPath.split('/')[-1])

    # Write class list
    zipf.write(classListPath, classListPath.split('/')[-1])

    zipf.close()

if __name__ == "__main__":
    main()