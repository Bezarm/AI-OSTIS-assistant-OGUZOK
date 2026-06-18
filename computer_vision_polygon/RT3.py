from ultralytics import YOLO

model = YOLO('/home/akimg/pyml/OGUZOK/AI-OSTIS-assistant-OGUZOK/computer_vision_polygon/models/best_yolo.pt')

results = model(
    source  = '/home/akimg/pyml/OGUZOK/AI-OSTIS-assistant-OGUZOK/computer_vision_polygon/stest/23.jpg',
    conf    = 0.25,
    iou     = 0.45,
    imgsz   = 640,
    save    = True,
    name    = 'inference_test',
    verbose = False,
)

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

r = results[0]
print(f'Найдено объектов: {len(r.boxes)}')
for box in r.boxes:
    cls_id = int(box.cls[0])
    conf   = float(box.conf[0])
    name   = UNIFIED_CLASSES[cls_id] if cls_id < len(UNIFIED_CLASSES) else f'cls_{cls_id}'
    print(f'  {name:25s}: conf={conf:.3f}')