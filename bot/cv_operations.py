from ultralytics import YOLO
from cv2 import imread, QRCodeDetector
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

class Model():
    def __init__(self):
        self.modelpath = Path(__file__).parent.parent/'computer_vision_polygon'/'models'/'best_yolo.pt'
        self.model = YOLO(self.model)
        self.detector = QRCodeDetector()
    def analyze(self, path, conf=0.003):
        img = imread(path)
        data, bbox, straight_qrcode = self.detector.detectAndDecode(img)
        if data:
            if re.fullmatch(r'[A-Z0-9]{24}', data):
             pass

        results = self.model(
            source  = path,
            conf    = conf,
            iou     = 0.45,
            imgsz   = 640,
            # save    = True,
            # name    = 'inference_test',
            verbose = False,
        )
        l=[]
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf   = float(box.conf[0])
            name   = UNIFIED_CLASSES[cls_id] if cls_id < len(UNIFIED_CLASSES) else f'cls_{cls_id}'
            l.append((name, conf))
        return l