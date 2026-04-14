from pathlib import Path
import cv2
import numpy as np

CLASS_COLORS = {
    0: (0, 0, 255),        # красный
    1: (0, 165, 255),      # оранжевый
    2: (0, 255, 255),      # желтый
    3: (0, 255, 0),        # зеленый
    4: (255, 255, 0),      # голубой
    5: (255, 0, 0),        # синий
    6: (255, 0, 255),      # фиолетовый
    7: (255, 255, 255),    # белый
    8: (0, 0, 0),          # черный
    9: (128, 128, 128),    # серый
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_image_label_pairs(images_dir: Path, labels_dir: Path, limit: int = 10):
    pairs = []
    image_files = sorted(images_dir.iterdir())

    for image_path in image_files:
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_path = labels_dir / f"{image_path.stem}.txt"
        if label_path.exists():
            pairs.append((image_path, label_path))

        if len(pairs) == limit:
            break

    return pairs


def parse_yolo_label_line(line: str):
    parts = line.strip().split()
    if len(parts) != 5:
        return None

    class_id = int(float(parts[0]))
    x_center = float(parts[1])
    y_center = float(parts[2])
    width = float(parts[3])
    height = float(parts[4])

    return class_id, x_center, y_center, width, height


def yolo_to_xyxy(x_center, y_center, width, height, img_w, img_h):
    x_center_px = x_center * img_w
    y_center_px = y_center * img_h
    box_w_px = width * img_w
    box_h_px = height * img_h

    x1 = int(x_center_px - box_w_px / 2)
    y1 = int(y_center_px - box_h_px / 2)
    x2 = int(x_center_px + box_w_px / 2)
    y2 = int(y_center_px + box_h_px / 2)

    x1 = max(0, min(x1, img_w - 1))
    y1 = max(0, min(y1, img_h - 1))
    x2 = max(0, min(x2, img_w - 1))
    y2 = max(0, min(y2, img_h - 1))

    return x1, y1, x2, y2


def draw_boxes(image_path: Path, label_path: Path, output_path: Path, classes_set: set):
    raw_bytes = np.fromfile(str(image_path), dtype=np.uint8)
    image = cv2.imdecode(raw_bytes, cv2.IMREAD_COLOR)
    if image is None:
        print(f"Не удалось прочитать изображение: {image_path}")
        return

    img_h, img_w = image.shape[:2]

    with label_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        parsed = parse_yolo_label_line(line)
        if parsed is None:
            continue

        class_id, x_center, y_center, width, height = parsed
        classes_set.add(class_id)

        x1, y1, x2, y2 = yolo_to_xyxy(x_center, y_center, width, height, img_w, img_h)
        color = CLASS_COLORS.get(class_id, (0, 255, 255))

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            str(class_id),
            (x1, max(18, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    # На Windows cv2.imwrite может не работать с кириллицей в пути.
    # Поэтому сохраняем через imencode + tofile.
    ext = output_path.suffix if output_path.suffix else ".jpg"
    success, encoded = cv2.imencode(ext, image)
    if not success:
        print(f"Ошибка кодирования изображения: {output_path}")
        return

    encoded.tofile(str(output_path))

    if output_path.exists():
        print(f"Сохранено: {output_path.name}")
    else:
        print(f"Не удалось сохранить файл: {output_path}")


def process_split(split_name: str, base_dir: Path, output_dir: Path, classes_set: set):
    images_dir = base_dir / split_name / "images"
    labels_dir = base_dir / split_name / "labels"

    pairs = get_image_label_pairs(images_dir, labels_dir, limit=10)
    print(f"\n{split_name.upper()}: найдено пар для обработки = {len(pairs)}")

    for idx, (image_path, label_path) in enumerate(pairs, start=1):
        output_name = f"{split_name}_{idx:02d}_{image_path.name}"
        output_path = output_dir / output_name
        draw_boxes(image_path, label_path, output_path, classes_set)


def main():
    root_dir = Path(__file__).resolve().parent
    dataset_dir = root_dir / "css-data"

    classes_found = set()

    process_split("test", dataset_dir, root_dir, classes_found)
    process_split("train", dataset_dir, root_dir, classes_found)

    print("\nВсе найденные классы в аннотациях:")
    if classes_found:
        print(sorted(classes_found))
    else:
        print("Классы не найдены")


main()