from pathlib import Path
import os


CLASS_NAMES = [
    "helmet",
    "mask",
    "no_helmet",
    "no_mask",
    "no_vest",
    "person",
    "cone",
    "vest",
    "truck",
    "car",
]

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp"]


def find_image_for_label(images_dir: Path, label_stem: str):
    for ext in IMAGE_EXTENSIONS:
        img_path = images_dir / f"{label_stem}{ext}"
        if img_path.exists():
            return img_path
    return None


def clean_empty_labels_for_split(split_dir: Path):
    labels_dir = split_dir / "labels"
    images_dir = split_dir / "images"

    if not labels_dir.exists() or not images_dir.exists():
        print(f"Пропуск {split_dir.name}: нет images/labels")
        return 0, 0

    deleted_labels = 0
    deleted_images = 0

    label_files = sorted(labels_dir.glob("*.txt"))
    for label_path in label_files:
        content = label_path.read_text(encoding="utf-8").strip()
        if content == "":
            image_path = find_image_for_label(images_dir, label_path.stem)

            try:
                label_path.unlink()
                deleted_labels += 1
                print(f"Удален пустой label: {label_path.name}")
            except Exception as e:
                print(f"Ошибка удаления label {label_path.name}: {e}")

            if image_path is not None and image_path.exists():
                try:
                    image_path.unlink()
                    deleted_images += 1
                    print(f"Удалено фото: {image_path.name}")
                except Exception as e:
                    print(f"Ошибка удаления фото {image_path.name}: {e}")

    return deleted_labels, deleted_images


def create_dataset_yaml(dataset_root: Path):
    yaml_path = dataset_root / "data_custom.yaml"
    yaml_text = (
        f"path: {dataset_root.as_posix()}\n"
        "train: train/images\n"
        "val: valid/images\n"
        "test: test/images\n"
        "\n"
        f"nc: {len(CLASS_NAMES)}\n"
        "names:\n"
    )

    for i, name in enumerate(CLASS_NAMES):
        yaml_text += f"  {i}: {name}\n"

    yaml_path.write_text(yaml_text, encoding="utf-8")
    print(f"\nYAML создан: {yaml_path}")
    return yaml_path


def train_yolo(yaml_path: Path):
    try:
        from ultralytics import YOLO
    except ImportError:
        print("\nUltralytics не установлен.")
        print("Установи командой: pip install ultralytics")
        return

    model = YOLO("yolov8n.pt")
    model.train(
        data=str(yaml_path),
        epochs=14,
        imgsz=640,
        batch=8,
        project="runs",
        name="helmet_dataset_yolov8n",
        pretrained=True,
    )


def main():
    root_dir = Path(__file__).resolve().parent
    dataset_root = root_dir / "css-data"

    print("=== 1. Чистка пустых аннотаций ===")
    total_labels = 0
    total_images = 0

    for split_name in ["train", "valid", "test"]:
        split_dir = dataset_root / split_name
        dl, di = clean_empty_labels_for_split(split_dir)
        total_labels += dl
        total_images += di

    print(f"\nИтог удаления: labels={total_labels}, images={total_images}")

    print("\n=== 2. Создание YAML ===")
    yaml_path = create_dataset_yaml(dataset_root)

    print("\n=== 3. Старт обучения YOLOv8 ===")
    train_yolo(yaml_path)


if __name__ == "__main__":
    os.environ["PYTHONUTF8"] = "1"
    main()
