# Задание 2 — Детекция средств безопасности (YOLOv8)

Проект для обучения и использования модели YOLOv8 для детекции объектов на изображениях и видео:
- каска / нет каски
- маска / нет маски
- жилет / нет жилета
- человек, конус, грузовик, автомобиль

В проекте есть:
- скрипт подготовки датасета и запуска обучения;
- API на FastAPI для обработки картинок и видео;
- UI на Flet для отправки файлов в API;
- утилита визуальной проверки разметки.

## Структура и назначение файлов

- `train_yolo.py` — подготовка датасета и запуск обучения YOLOv8:
  - удаляет пустые label-файлы и соответствующие изображения;
  - формирует `css-data/data_custom.yaml`;
  - запускает обучение модели.
- `main.py` — backend API (FastAPI):
  - POST `/img` для обработки изображения;
  - POST `/video` для обработки видео;
  - загружает веса модели (`best.pt`, если есть, иначе `yolov8n.pt`).
- `app.py` — desktop/web UI (Flet) для работы с API:
  - загрузка изображения/видео;
  - отправка в API;
  - просмотр и сохранение результата.
- `work_dataset_img.py` — утилита проверки качества разметки:
  - берет несколько пар `image + label`;
  - отрисовывает bounding boxes;
  - сохраняет примеры в корень проекта.
- `requirements.txt` — Python-зависимости с зафиксированными версиями.
- `css-data/` — датасет в формате YOLO:
  - `train/`, `valid/`, `test/`;
  - внутри каждого: `images/` и `labels/`.
- `css-data/data_custom.yaml` — конфиг датасета для YOLO (пути + классы).

## Классы в разметке датасета

Используется 10 классов:

- `0` — `helmet` (каска)
- `1` — `mask` (маска)
- `2` — `no_helmet` (без каски)
- `3` — `no_mask` (без маски)
- `4` — `no_vest` (без жилета)
- `5` — `person` (человек)
- `6` — `cone` (сигнальный конус)
- `7` — `vest` (жилет)
- `8` — `truck` (грузовик)
- `9` — `car` (автомобиль)

## Какие методы есть

### `train_yolo.py`
- `find_image_for_label(images_dir, label_stem)` — ищет изображение для label по stem и расширению.
- `clean_empty_labels_for_split(split_dir)` — удаляет пустые `.txt` и соответствующие картинки.
- `create_dataset_yaml(dataset_root)` — создает `data_custom.yaml`.
- `train_yolo(yaml_path)` — запускает обучение через `ultralytics.YOLO`.

### `main.py` (API)
- `load_model()` — загрузка модели из `runs/.../best.pt` или базовой `yolov8n.pt`.
- `decode_b64_to_image(data_b64)` — декодирование base64 -> OpenCV image.
- `encode_image_to_b64(img)` — кодирование OpenCV image -> base64.
- `classes_to_description(found)` — формирование текстового описания по найденным классам.
- `run_detection_and_draw(frame)` — инференс + отрисовка боксов/меток.
- `detect_img(payload)` — endpoint `/img`.
- `detect_video(payload)` — endpoint `/video`.

### `app.py` (UI)
- `main(page)` — сборка UI и регистрация обработчиков.
- `show_message(text, color)` — вывод уведомлений.
- `save_file_result(e)` — сохранение результата (картинка/видео).
- `pick_image_result(e)` — выбор и предпросмотр входного изображения.
- `send_image_to_api(_)` — отправка изображения в API.
- `save_image_result(_)` — сохранение выходного изображения.
- `pick_video_result(e)` — выбор входного видео.
- `send_video_to_api(_)` — отправка видео в API.
- `save_video_result(_)` — сохранение выходного видео.
- `open_output_video(_)` — открытие обработанного видео.

### `work_dataset_img.py`
- `get_image_label_pairs(images_dir, labels_dir, limit)` — сбор пар image/label.
- `parse_yolo_label_line(line)` — парсинг строки YOLO-разметки.
- `yolo_to_xyxy(...)` — конвертация YOLO-координат в пиксели (`x1,y1,x2,y2`).
- `draw_boxes(image_path, label_path, output_path, classes_set)` — отрисовка боксов и сохранение файла.
- `process_split(split_name, base_dir, output_dir, classes_set)` — обработка одного split.

## Какие JSON используются

Но есть JSON-формат обмена с API:

### Endpoint: `POST /img`
Запрос:
```json
{
  "img": "base64"
}
```
Ответ:
```json
{
  "img": "base64",
  "description": "..."
}
```

### Endpoint: `POST /video`
Запрос:
```json
{
  "video": "base64"
}
```
Ответ:
```json
{
  "video": "base64",
  "description": "..."
}
```

## Запуск проекта

1) Установить зависимости:
```bash
pip install -r requirements.txt
```

2) Обучить модель:
```bash
python train_yolo.py
```

3) Запустить API:
```bash
python main.py
```

4) Запустить UI:
```bash
python app.py
```

По умолчанию UI отправляет запросы в `http://127.0.0.1:8000`.