"""
inference.py — разметка изображений с помощью обученной модели детекции ингредиентов.

Использование:
    python inference.py --model best_model.pth --image photo.jpg
    python inference.py --model best_model.pth --image photo.jpg --conf 0.4 --out result.jpg
    python inference.py --model best_model.pth --image photo.jpg --no-display

Зависимости:
    pip install torch torchvision pillow matplotlib
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from PIL import Image


# ─────────────────────────────────────────────────────────────
# Минимальная реализация Faster R-CNN без лишних импортов.
# Используем torchvision только для самой модели — никакого
# обучающего кода, датасетов, albumentations и т.д.
# ─────────────────────────────────────────────────────────────

def build_model_from_checkpoint(checkpoint_path: str, device: torch.device):
    """
    Загружает модель полностью из checkpoint:
    - num_classes берётся из самого .pth файла
    - веса backbone восстанавливаются из state_dict (не скачиваются заново)
    - возвращает (model, class_map)
    """
    from torchvision.models.detection import fasterrcnn_resnet50_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

    print(f"Загружаю checkpoint: {checkpoint_path}")
    ckpt = torch.load(checkpoint_path, map_location=device)

    # ── Извлекаем метаданные из checkpoint ──────────────────────
    num_classes = ckpt.get("num_classes")
    class_map   = ckpt.get("class_map")   # {name: id}

    if num_classes is None:
        # Определяем num_classes из весов классификатора
        cls_score_key = "roi_heads.box_predictor.cls_score.weight"
        if cls_score_key in ckpt.get("model_state_dict", ckpt):
            state = ckpt.get("model_state_dict", ckpt)
            num_classes = state[cls_score_key].shape[0]
            print(f"  num_classes определён из весов: {num_classes}")
        else:
            raise ValueError(
                "Не удалось определить num_classes из checkpoint. "
                "Передайте --num-classes вручную."
            )

    if class_map is None:
        print("  Предупреждение: class_map не найден в checkpoint.")
        print("  Попробую загрузить class_map.json из той же папки.")
        class_map_path = Path(checkpoint_path).parent / "class_map.json"
        if class_map_path.exists():
            with open(class_map_path) as f:
                class_map = json.load(f)
            print(f"  Загружен: {class_map_path}")
        else:
            # Fallback: числовые метки
            class_map = {f"class_{i}": i for i in range(1, num_classes)}
            print("  class_map.json не найден, используются числовые метки.")

    print(f"  num_classes = {num_classes}")
    print(f"  Классов в class_map: {len(class_map)}")

    # ── Строим архитектуру без предобученных весов ───────────────
    # weights=None — не скачиваем ImageNet веса, они будут в state_dict
    model = fasterrcnn_resnet50_fpn(weights=None, num_classes=num_classes)

    # Заменяем head под нужное num_classes
    # (на случай если checkpoint был сохранён со стандартным head)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    # ── Загружаем веса ───────────────────────────────────────────
    state_dict = ckpt.get("model_state_dict", ckpt)
    missing, unexpected = model.load_state_dict(state_dict, strict=False)

    if missing:
        print(f"  Отсутствующие ключи ({len(missing)}): {missing[:5]}{'...' if len(missing)>5 else ''}")
    if unexpected:
        print(f"  Неожиданные ключи ({len(unexpected)}): {unexpected[:5]}{'...' if len(unexpected)>5 else ''}")
    if not missing and not unexpected:
        print("  Веса загружены без ошибок ✓")

    model.to(device)
    model.eval()
    return model, class_map


# ─────────────────────────────────────────────────────────────
# Препроцессинг — только PIL + torchvision.transforms
# ─────────────────────────────────────────────────────────────

def preprocess(image_path: str):
    """
    Читает изображение и превращает в тензор [1, 3, H, W] float32 в [0, 1].
    Faster R-CNN принимает изображения в оригинальном размере,
    внутренняя нормализация и resize происходят внутри модели.
    """
    from torchvision import transforms as T

    img = Image.open(image_path).convert("RGB")
    tensor = T.ToTensor()(img)   # [3, H, W], float32, [0,1]
    return img, tensor


# ─────────────────────────────────────────────────────────────
# Инференс
# ─────────────────────────────────────────────────────────────

@torch.no_grad()
def predict(model, tensor: torch.Tensor, device: torch.device, conf_threshold: float):
    """
    Прогоняет один тензор через модель, фильтрует по порогу уверенности.
    Возвращает словарь с boxes, labels, scores — всё на CPU.
    """
    inp = [tensor.to(device)]
    preds = model(inp)
    pred  = preds[0]

    mask = pred["scores"] >= conf_threshold
    return {
        "boxes":  pred["boxes"][mask].cpu(),
        "labels": pred["labels"][mask].cpu(),
        "scores": pred["scores"][mask].cpu(),
    }


# ─────────────────────────────────────────────────────────────
# Визуализация
# ─────────────────────────────────────────────────────────────

# 20 различимых цветов для классов
PALETTE = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#42d4f4", "#f032e6", "#bfef45", "#fabed4",
    "#469990", "#dcbeff", "#9A6324", "#fffac8", "#800000",
    "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9",
]


def draw_predictions(
    image: Image.Image,
    predictions: dict,
    class_map: dict,
    conf_threshold: float,
    output_path: str | None,
    display: bool,
):
    id_to_name = {v: k for k, v in class_map.items()}

    boxes  = predictions["boxes"]
    labels = predictions["labels"]
    scores = predictions["scores"]

    fig, ax = plt.subplots(1, 1, figsize=(14, 9))
    ax.imshow(image)

    for box, label, score in zip(boxes, labels, scores):
        x1, y1, x2, y2 = box.tolist()
        lid   = label.item()
        name  = id_to_name.get(lid, f"class_{lid}")
        color = PALETTE[lid % len(PALETTE)]

        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=2,
            edgecolor=color,
            facecolor="none",
            linestyle="solid",
        )
        ax.add_patch(rect)

        # Подпись над bbox
        label_text = f"{name}  {score:.2f}"
        ax.text(
            x1, max(y1 - 6, 0),
            label_text,
            fontsize=9,
            fontweight="bold",
            color="white",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor=color,
                alpha=0.85,
                edgecolor="none",
            ),
        )

    n = len(boxes)
    ax.set_title(
        f"Детекция ингредиентов  |  {n} объект{'ов' if n != 1 else ''}  "
        f"|  порог = {conf_threshold:.2f}",
        fontsize=12,
        pad=10,
    )
    ax.axis("off")
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Результат сохранён: {output_path}")

    if display:
        plt.show()
    else:
        plt.close()


# ─────────────────────────────────────────────────────────────
# Текстовый вывод результатов
# ─────────────────────────────────────────────────────────────

def print_results(predictions: dict, class_map: dict):
    id_to_name = {v: k for k, v in class_map.items()}
    boxes  = predictions["boxes"]
    labels = predictions["labels"]
    scores = predictions["scores"]

    if len(boxes) == 0:
        print("Объекты не найдены.")
        return

    # Группируем по классу
    from collections import defaultdict
    grouped = defaultdict(list)
    for box, lbl, score in zip(boxes, labels, scores):
        name = id_to_name.get(lbl.item(), f"class_{lbl.item()}")
        grouped[name].append((score.item(), box.tolist()))

    print(f"\n{'─'*52}")
    print(f"  Найдено объектов: {len(boxes)}")
    print(f"{'─'*52}")
    for name in sorted(grouped):
        detections = grouped[name]
        for i, (score, (x1, y1, x2, y2)) in enumerate(detections, 1):
            tag = f"[{i}]" if len(detections) > 1 else "   "
            print(
                f"  {tag} {name:<22} "
                f"score={score:.3f}  "
                f"bbox=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})"
            )
    print(f"{'─'*52}\n")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Инференс детектора ингредиентов (Faster R-CNN)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--model",       required=True,  help="Путь к .pth checkpoint")
    p.add_argument("--image",       required=True,  help="Путь к изображению")
    p.add_argument("--conf",        type=float, default=0.5,
                   help="Порог уверенности (0–1)")
    p.add_argument("--out",         default=None,
                   help="Сохранить результат в файл (jpg/png). "
                        "По умолчанию: <image>_result.jpg")
    p.add_argument("--no-display",  action="store_true",
                   help="Не открывать окно с изображением")
    p.add_argument("--num-classes", type=int, default=None,
                   help="Число классов (включая background). "
                        "Если не указано — берётся из checkpoint.")
    p.add_argument("--cpu",         action="store_true",
                   help="Принудительно использовать CPU")
    return p.parse_args()


def main():
    args = parse_args()

    # ── Устройство ───────────────────────────────────────────
    if args.cpu or not torch.cuda.is_available():
        device = torch.device("cpu")
    else:
        device = torch.device("cuda")
    print(f"Устройство: {device}")

    # ── Проверка файлов ──────────────────────────────────────
    if not Path(args.model).exists():
        print(f"Ошибка: файл модели не найден: {args.model}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.image).exists():
        print(f"Ошибка: изображение не найдено: {args.image}", file=sys.stderr)
        sys.exit(1)

    # ── Загрузка модели ──────────────────────────────────────
    model, class_map = build_model_from_checkpoint(args.model, device)

    # Переопределяем num_classes если указан вручную
    if args.num_classes is not None:
        from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
        in_f = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_f, args.num_classes)
        model.to(device).eval()

    # ── Препроцессинг ────────────────────────────────────────
    print(f"Обрабатываю изображение: {args.image}")
    image, tensor = preprocess(args.image)
    print(f"  Размер: {image.width}×{image.height}")

    # ── Инференс ─────────────────────────────────────────────
    predictions = predict(model, tensor, device, conf_threshold=args.conf)

    # ── Вывод результатов ────────────────────────────────────
    print_results(predictions, class_map)

    # ── Визуализация ─────────────────────────────────────────
    if args.out is None:
        stem = Path(args.image).stem
        args.out = str(Path(args.image).parent / f"{stem}_result.jpg")

    draw_predictions(
        image       = image,
        predictions = predictions,
        class_map   = class_map,
        conf_threshold = args.conf,
        output_path = args.out,
        display     = not args.no_display,
    )


if __name__ == "__main__":
    main()