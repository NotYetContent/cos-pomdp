# Browse data

import cv2
import os
import yaml
import numpy as np
from PIL import Image
import time
from ..utils import normalized_xywh_to_xyxy

def yolo_load_info(dataset_yaml_path, for_train=True):
    """
    Loads the config & filenames but doesn't
    open the data files.
    Returns: datadir, filenames, classes, colors
    """
    with open(dataset_yaml_path) as f:
        config = yaml.safe_load(f)

    if for_train:
        datadir = os.path.join(config["path"], "train")
    else:
        datadir = os.path.join(config["path"], "val")
    fnames = map(lambda fname: os.path.splitext(fname)[0],
                 os.listdir(os.path.join(datadir, "images")))
    classes = config["names"]
    colors = config["colors"]
    return (datadir,
            list(sorted(fnames)),
            classes,
            colors)

def yolo_load_one(datadir, fname):
    """
    Loads one sample. The sample is located at

    {datadir}/images/{fname}.jpg
    {datadir}/labels/{fname}.txt
    """
    with open(os.path.join(datadir, "labels", fname + ".txt")) as fa:
        annotations = []
        for line in fa.readlines():
            annot = list(line.strip().split())
            annot[0] = int(annot[0])
            annot[1:] = map(float, annot[1:])
            annotations.append(annot)
            with open(os.path.join(datadir, "images", fname + ".jpg"), 'rb') as i:
                im = Image.open(i)
                return np.array(im), annotations

def yolo_plot_one(img, annotations, classes, colors, line_thickness=2,
                  center=True, show_label=True):
    """
    Borrowing code from: https://github.com/ultralytics/yolov5/blob/master/utils/plots.py#L68
    Args:
       img (array): Image array (np.array) or PIL.Image.Image
       annotations (list): list of [class, x_center, y_center, width, height] annotations
       classes (list): Ordered classes; i in annotation class corresponds to the class
           at index 0 of this list.
    """
    _img = img
    if isinstance(img, Image.Image):
        _img = np.array(img)

    tl = line_thickness or round(0.002 * (_img.shape[0] + _img.shape[1]) / 2) # line/font thickness
    for annot in annotations:
        class_int = annot[0]
        xywh = annot[1:]
        x1, y1, x2, y2 = normalized_xywh_to_xyxy(xywh, _img.shape[:2], center=center)
        cv2.rectangle(_img, (x1, y1), (x2, y2), colors[class_int],
                      thickness=tl, lineType=cv2.LINE_AA)
        if show_label:
            tf = max(tl - 1, 1)  # font thickness
            t_size = cv2.getTextSize(classes[class_int], 0,
                                     fontScale=tl/3,
                                     thickness=tf)[0]
            # the background color of the class label
            cv2.rectangle(_img,
                          (x1, y1),
                          (x1 + t_size[0], y1 - t_size[1] - 3),
                          colors[class_int], -1, cv2.LINE_AA)  # filled
            cv2.putText(_img, classes[class_int],
                        (x1, y1 - 2), 0, tl / 3, [255, 255, 255],
                        thickness=tf, lineType=cv2.LINE_AA)
    if isinstance(img, Image.Image):
        # Returns PIL image if input is PIL image
        _img = Image.fromarray(_img)
    return _img


def kb_browse(model="yolo", **kwargs):
    """
    Browsing samples with keyboard control
    samples: list of samples
    model: either 'yolo' or 'frcnn'
    """
    import cv2
    # Load samples
    print("Loading samples...")
    if model == "yolo":
        dataset_yaml_path =\
            kwargs.get("dataset_yaml_path",
                       os.path.join("yolov5-dataset.yaml"))
        for_train = kwargs.get("for_train", True)
        datadir, files, classes, colors =\
            yolo_load_info(dataset_yaml_path, for_train=for_train)

    # Start simple keyboard listener
    controls = {
        "a": -1,
        "d": 1,
    }
    from pprint import pprint
    pprint(controls)

    idx = 0
    while True:
        if model == "yolo":
            img, annotations = yolo_load_one(datadir, files[idx])
            img = yolo_plot_one(img, annotations, classes, colors)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        else:
            raise ValueError("Cannot handle {}".format(model))

        cv2.imshow(model, img_rgb)
        key = cv2.waitKey(0)
        if chr(key) in controls:
            idx += controls[chr(key)]
        elif chr(key) == 'q':
            print("quit")
            return
        time.sleep(0.1)

if __name__ == "__main__":
    # make sure you are under data/ and run python -m cosp.vision.data.browse
    import sys
    model = "yolo"
    dataset_yaml_path = "yolov5-dataset.yaml"
    for i, arg in enumerate(sys.argv):
        if i == 0:
            continue
        if arg == "-m":
            model = sys.argv[i+1]
        if arg == "-p":
            dataset_yaml_path = sys.argv[i+1]
    kb_browse(model, dataset_yaml_path=dataset_yaml_path)
