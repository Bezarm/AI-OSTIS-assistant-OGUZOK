#!/usr/bin/env python3
"""
detect_ingredients.py — Распознавание ингредиентов на фото.

Использование:
    # Одно изображение
    python detect_ingredients.py --model best_model.pth --image food.jpg

    # Папка с изображениями
    python detect_ingredients.py --model best_model.pth --input ./photos/ --output ./results/

    # Только список ингредиентов без визуализации
    python detect_ingredients.py --model best_model.pth --image food.jpg --no-viz

    # Изменить порог уверенности (0.0–1.0, по умолчанию 0.5)
    python detect_ingredients.py --model best_model.pth --image food.jpg --conf 0.4

    # JSON-вывод (удобно для интеграции)
    python detect_ingredients.py --model best_model.pth --image food.jpg --json

Чекпоинт должен быть сохранён функцией из ноутбука (содержит
'model_state_dict', 'class_map', 'num_classes').
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image

# ── Опциональные зависимости (matplotlib нужен только для визуализации) ──
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from torchvision.models.detection import (
        fasterrcnn_resnet50_fpn_v2,
        FasterRCNN_ResNet50_FPN_V2_Weights,
    )
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
except ImportError:
    print("Ошибка: установите torchvision:  pip install torchvision")
    sys.exit(1)

# ── Поддерживаемые форматы изображений ──────────────────────────────────────
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif'}


# ════════════════════════════════════════════════════════════════════════════
#  Модель
# ════════════════════════════════════════════════════════════════════════════

def build_model(num_classes: int):
    """Строит Faster R-CNN ResNet50-FPN v2 с кастомным head."""
    weights = FasterRCNN_ResNet50_FPN_V2_Weights.DEFAULT
    model = fasterrcnn_resnet50_fpn_v2(weights=weights)
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    return model


def load_model(checkpoint_path: str, device: torch.device):
    """
    Загружает модель из чекпоинта.

    Ожидаемые ключи в .pth:
        model_state_dict  — веса модели
        class_map         — dict {class_name: category_id}
        num_classes       — int (включая фоновый класс)

    Если class_map отсутствует — пробует загрузить class_map.json
    рядом с чекпоинтом.
    """
    ckpt_path = Path(checkpoint_path)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Чекпоинт не найден: {checkpoint_path}")

    print(f"Загружаем чекпоинт: {ckpt_path.name}")
    ckpt = torch.load(checkpoint_path, map_location=device)

    # ── class_map ────────────────────────────────────────────────────────────
    class_map = ckpt.get('class_map')
    if class_map is None:
        # ищем class_map.json рядом с .pth
        json_candidate = ckpt_path.parent / 'class_map.json'
        if json_candidate.exists():
            with open(json_candidate) as f:
                class_map = json.load(f)
            print(f"  class_map загружен из {json_candidate.name}")
        else:
            raise ValueError(
                "В чекпоинте нет 'class_map', и class_map.json не найден рядом с моделью. "
                "Укажите путь вручную через --class-map."
            )

    # ── num_classes ───────────────────────────────────────────────────────────
    num_classes = ckpt.get('num_classes')
    if num_classes is None:
        num_classes = max(class_map.values()) + 1  # +1 background
        print(f"  num_classes определён из class_map: {num_classes}")

    # ── строим и загружаем веса ───────────────────────────────────────────────
    model = build_model(num_classes)
    model.load_state_dict(ckpt['model_state_dict'])
    model.to(device).eval()

    epoch = ckpt.get('epoch', '?')
    val_score = ckpt.get('val_score')
    val_str = f", val_score={val_score:.4f}" if val_score is not None else ""
    print(f"  ✓ Загружено (эпоха {epoch}{val_str}, классов {len(class_map)})")

    id_to_name = {v: k for k, v in class_map.items()}
    return model, class_map, id_to_name


# ════════════════════════════════════════════════════════════════════════════
#  Инференс
# ════════════════════════════════════════════════════════════════════════════

# Нормализация — те же параметры, что при обучении
_TRANSFORM = T.Compose([
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


@torch.no_grad()
def predict(
    model,
    image: Image.Image,
    device: torch.device,
    conf_threshold: float = 0.5,
):
    """
    Возвращает dict с ключами:
        boxes   — тензор (N, 4) в формате [x1, y1, x2, y2]
        labels  — тензор (N,) category_id
        scores  — тензор (N,) уверенность
    """
    tensor = _TRANSFORM(image).unsqueeze(0).to(device)

    with torch.cuda.amp.autocast(enabled=device.type == 'cuda'):
        output = model(tensor)[0]

    mask = output['scores'] > conf_threshold
    return {
        'boxes':  output['boxes'][mask].cpu(),
        'labels': output['labels'][mask].cpu(),
        'scores': output['scores'][mask].cpu(),
    }


# ════════════════════════════════════════════════════════════════════════════
#  Визуализация
# ════════════════════════════════════════════════════════════════════════════

def visualize(
    image: Image.Image,
    preds: dict,
    id_to_name: dict,
    save_path: str | None = None,
    show: bool = True,
    title: str = "",
):
    """Рисует боксы с подписями на изображении."""
    if not HAS_MPL:
        print("Matplotlib не установлен — визуализация недоступна. pip install matplotlib")
        return

    n_classes = max(id_to_name.keys()) if id_to_name else 12
    cmap = plt.cm.get_cmap('tab20', max(n_classes + 1, 20))

    fig, ax = plt.subplots(figsize=(14, 9))
    ax.imshow(image)

    for box, label, score in zip(preds['boxes'], preds['labels'], preds['scores']):
        x1, y1, x2, y2 = box.numpy()
        lid = label.item()
        name = id_to_name.get(lid, f'class_{lid}')
        color = cmap(lid % 20)

        rect = patches.Rectangle(
            (x1, y1), x2 - x1, y2 - y1,
            linewidth=2, edgecolor=color, facecolor='none'
        )
        ax.add_patch(rect)
        ax.text(
            x1, max(y1 - 4, 0),
            f'{name}  {score:.2f}',
            fontsize=8, color='white', va='bottom',
            bbox=dict(boxstyle='round,pad=0.25', facecolor=color, alpha=0.85, linewidth=0),
        )

    n = len(preds['boxes'])
    header = f"{title}  •  " if title else ""
    ax.set_title(f"{header}Найдено: {n} объект{'ов' if n != 1 else ''}", fontsize=13)
    ax.axis('off')
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"  Сохранено: {save_path}")
    if show:
        plt.show()
    plt.close()


# ════════════════════════════════════════════════════════════════════════════
#  Форматирование результата
# ════════════════════════════════════════════════════════════════════════════

def format_results(preds: dict, id_to_name: dict) -> list[dict]:
    """Возвращает список dict для вывода / JSON."""
    results = []
    for box, label, score in zip(preds['boxes'], preds['labels'], preds['scores']):
        x1, y1, x2, y2 = box.numpy().tolist()
        results.append({
            'ingredient': id_to_name.get(label.item(), f'class_{label.item()}'),
            'score': round(float(score), 4),
            'box': {'x1': round(x1), 'y1': round(y1), 'x2': round(x2), 'y2': round(y2)},
        })
    # сортировка по убыванию уверенности
    results.sort(key=lambda r: r['score'], reverse=True)
    return results


def print_results(results: list[dict], image_name: str = ""):
    """Красивый вывод в терминал."""
    if image_name:
        print(f"\n{'─' * 50}")
        print(f"  {image_name}")
        print(f"{'─' * 50}")

    if not results:
        print("  Ингредиентов не найдено.")
        return

    # уникальные ингредиенты (лучший score)
    seen = {}
    for r in results:
        ing = r['ingredient']
        if ing not in seen or r['score'] > seen[ing]:
            seen[ing] = r['score']

    print(f"  Ингредиентов: {len(results)} детекций, {len(seen)} уникальных\n")
    for ing, score in sorted(seen.items(), key=lambda x: -x[1]):
        bar = '█' * int(score * 20)
        print(f"  {ing:<22} {score:.3f}  {bar}")


# ════════════════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════════════════

def parse_args():
    p = argparse.ArgumentParser(
        description="Распознавание ингредиентов на фото (Faster R-CNN)",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=__doc__,
    )

    # ── источник ──────────────────────────────────────────────────────────────
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument('--image',  metavar='PATH', help='Одно изображение')
    src.add_argument('--input',  metavar='DIR',  help='Папка с изображениями')

    # ── модель ────────────────────────────────────────────────────────────────
    p.add_argument('--model',     required=True, metavar='PATH',
                   help='Путь к .pth чекпоинту')
    p.add_argument('--class-map', metavar='PATH',
                   help='Путь к class_map.json (если не встроен в чекпоинт)')

    # ── параметры инференса ────────────────────────────────────────────────────
    p.add_argument('--conf',   type=float, default=0.5, metavar='F',
                   help='Порог уверенности (default: 0.5)')
    p.add_argument('--device', default='auto', choices=['auto', 'cpu', 'cuda'],
                   help='Устройство (default: auto)')

    # ── вывод ─────────────────────────────────────────────────────────────────
    p.add_argument('--output',  metavar='DIR',
                   help='Папка для сохранения результатов (визуализация + JSON)')
    p.add_argument('--no-viz',  action='store_true',
                   help='Не рисовать/показывать изображение')
    p.add_argument('--no-show', action='store_true',
                   help='Не открывать окно просмотра (только сохранить)')
    p.add_argument('--json',    action='store_true',
                   help='Вывести итог в JSON (для интеграции)')

    return p.parse_args()


def resolve_device(choice: str) -> torch.device:
    if choice == 'auto':
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    return torch.device(choice)


def collect_images(args) -> list[Path]:
    if args.image:
        p = Path(args.image)
        if not p.exists():
            print(f"Ошибка: файл не найден: {p}")
            sys.exit(1)
        return [p]
    else:
        folder = Path(args.input)
        if not folder.is_dir():
            print(f"Ошибка: папка не найдена: {folder}")
            sys.exit(1)
        images = sorted(
            f for f in folder.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not images:
            print(f"В папке {folder} нет изображений.")
            sys.exit(1)
        print(f"Найдено {len(images)} изображений в {folder}")
        return images


# ════════════════════════════════════════════════════════════════════════════
#  main
# ════════════════════════════════════════════════════════════════════════════

def main():
    args = parse_args()

    device = resolve_device(args.device)
    print(f"Устройство: {device}")

    # ── загружаем модель ───────────────────────────────────────────────────────
    model, class_map, id_to_name = load_model(args.model, device)

    # ── переопределяем class_map если указан вручную ───────────────────────────
    if args.class_map:
        with open(args.class_map) as f:
            class_map = json.load(f)
        id_to_name = {v: k for k, v in class_map.items()}
        print(f"class_map загружен из {args.class_map} ({len(class_map)} классов)")

    # ── папка для вывода ────────────────────────────────────────────────────────
    out_dir = None
    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)

    images = collect_images(args)
    all_results = {}  # image_name -> list[dict]

    for img_path in images:
        t0 = time.perf_counter()
        image = Image.open(img_path).convert('RGB')
        preds = predict(model, image, device, conf_threshold=args.conf)
        elapsed = time.perf_counter() - t0

        results = format_results(preds, id_to_name)
        all_results[img_path.name] = results

        if not args.json:
            print_results(results, img_path.name)
            print(f"  Время инференса: {elapsed * 1000:.1f} мс")

        # ── визуализация ────────────────────────────────────────────────────────
        if not args.no_viz:
            save_path = None
            if out_dir:
                save_path = str(out_dir / f"{img_path.stem}_detected{img_path.suffix}")

            show_window = not args.no_show and not out_dir  # показываем только если нет --output

            visualize(
                image, preds, id_to_name,
                save_path=save_path,
                show=show_window,
                title=img_path.name,
            )

        # ── JSON на диск (один файл на изображение) ─────────────────────────────
        if out_dir:
            json_path = out_dir / f"{img_path.stem}_results.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'image': img_path.name,
                    'conf_threshold': args.conf,
                    'detections': results,
                }, f, ensure_ascii=False, indent=2)

    # ── JSON-вывод в stdout (--json) ────────────────────────────────────────────
    if args.json:
        output = all_results if len(all_results) > 1 else list(all_results.values())[0]
        print(json.dumps(output, ensure_ascii=False, indent=2))

    # ── итоговое summary (батч) ─────────────────────────────────────────────────
    if len(images) > 1 and not args.json:
        print(f"\n{'═' * 50}")
        print(f"  Обработано: {len(images)} изображений")
        total_dets = sum(len(v) for v in all_results.values())
        all_ingredients = {}
        for dets in all_results.values():
            for d in dets:
                ing = d['ingredient']
                all_ingredients[ing] = all_ingredients.get(ing, 0) + 1
        print(f"  Всего детекций: {total_dets}")
        print(f"  Уникальных ингредиентов: {len(all_ingredients)}")
        top = sorted(all_ingredients.items(), key=lambda x: -x[1])[:10]
        print("  Топ-10 по встречаемости:")
        for ing, cnt in top:
            print(f"    {ing:<22} {cnt}×")
        if out_dir:
            summary_path = out_dir / 'summary.json'
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_images': len(images),
                    'total_detections': total_dets,
                    'conf_threshold': args.conf,
                    'ingredient_counts': dict(sorted(all_ingredients.items(), key=lambda x: -x[1])),
                    'per_image': all_results,
                }, f, ensure_ascii=False, indent=2)
            print(f"\n  Summary: {summary_path}")


if __name__ == '__main__':
    main()