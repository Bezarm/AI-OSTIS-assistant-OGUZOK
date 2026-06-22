from ultralytics import YOLO
from cv2 import imread, QRCodeDetector, imdecode, IMREAD_COLOR
from cv2 import imdecode
import numpy as np
from pathlib import Path
import requests
import re

UNIFIED_CLASSES = [
  "apple",
  "avocado",
  "bacon",
  "banana",
  "beef",
  "bell_pepper",
  "blueberry",
  "bread",
  "broccoli",
  "butter",
  "cabbage",
  "carrot",
  "cauliflower",
  "celery",
  "cheese",
  "chicken",
  "chili_pepper",
  "coconut",
  "coriander",
  "cream",
  "cucumber",
  "egg",
  "eggplant",
  "fish",
  "flour_grain",
  "garlic",
  "ginger",
  "gourd",
  "grape",
  "leafy_greens",
  "lemon",
  "mango",
  "melon",
  "milk",
  "mushroom",
  "noodles",
  "nuts",
  "oil",
  "olive",
  "onion",
  "orange",
  "peach",
  "pear",
  "peas",
  "pineapple",
  "pomegrante",
  "pork",
  "potato",
  "pudding",
  "pumpkin",
  "raddish",
  "rice",
  "shrimp",
  "spinach",
  "strawberry",
  "sugar",
  "tomato"
]

_YOLO_TO_KB_INGR = {
    "egg":           "egg",
    "potato":        "potapo",
    "onion":         "onion",
    "sugar":         "sugar",
    "carrot":        "carrot",
    "oil":           "vegetable_oil",
    "flour_grain":   "flour",
    "butter":        "butter",
    "milk":          "milk",
    "rice":          "rice",
    "garlic":        "garlic",
    "cucumber":      "cucumber",
    "tomato":        "tomato",
    "cabbage":       "cabbage",
    "bread":         "bread",
    "cheese":        "cheese",
    "apple":         "apples",
    "noodles":       "macarones",
    "cream":         "sour_cream",
    "beef":          "ground_beef",
}

class Model():
    def __init__(self):
        self.modelpath = Path(__file__).parent.parent/'computer_vision_polygon'/'models'/'best_yolo.pt'
        self.model = YOLO(self.modelpath)
    
    def _map_to_ingrs(self, detections):
        seen = set()
        result = []
        for name in detections:
            kb_id = _YOLO_TO_KB_INGR.get(name)
            if kb_id and kb_id not in seen:
                seen.add(kb_id)
                result.append(kb_id)
        return result

    def analyze(self, file_bytes, conf=0.03):
        # img = imread(path)
        # data, bbox, straight_qrcode = self.detector.detectAndDecode(img)
        # if data:
        #     if re.fullmatch(r'[A-Z0-9]{24}', data):
        #      pass

        np_arr = np.frombuffer(file_bytes.read(), dtype=np.uint8)
        img = imdecode(np_arr, IMREAD_COLOR)
        print("pre")
        results = self.model(
            source  = img,
            conf    = conf,
            iou     = 0.45,
            imgsz   = 640,
            # save    = True,
            # name    = 'inference_test',
            verbose = False,
        )
        print("post")
        detections = []
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            name   = UNIFIED_CLASSES[cls_id] if cls_id < len(UNIFIED_CLASSES) else f'cls_{cls_id}'
            detections.append(name)
        print(detections)
        print(self._map_to_ingrs(detections))
        return self._map_to_ingrs(detections)