import base64
import tempfile
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ultralytics import YOLO


CLASS_NAMES = {
    0: "helmet",
    1: "mask",
    2: "no_helmet",
    3: "no_mask",
    4: "no_vest",
    5: "person",
    6: "cone",
    7: "vest",
    8: "truck",
    9: "car",
}

COLORS = {
    0: (0, 255, 0),
    1: (0, 255, 255),
    2: (0, 0, 255),
    3: (0, 69, 255),
    4: (102, 0, 204),
    5: (255, 255, 255),
    6: (255, 128, 0),
    7: (255, 0, 0),
    8: (128, 128, 128),
    9: (255, 0, 255),
}


class ImgIn(BaseModel):
    img: str


class ImgOut(BaseModel):
    img: str
    description: str


class VideoIn(BaseModel):
    video: str


class VideoOut(BaseModel):
    video: str
    description: str


def load_model() -> YOLO:
    root = Path(__file__).resolve().parent
    default_best = root / "runs" / "helmet_dataset_yolov8n" / "weights" / "best.pt"
    model_path = default_best if default_best.exists() else "yolov8n.pt"
    return YOLO(str(model_path))


MODEL = load_model()
app = FastAPI(title="Safety Detection API")


def decode_b64_to_image(data_b64: str) -> np.ndarray:
    try:
        raw = base64.b64decode(data_b64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Плохое изображение")
        return img
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Wrong image base64: {e}")


def encode_image_to_b64(img: np.ndarray) -> str:
    ok, encoded = cv2.imencode(".jpg", img)
    if not ok:
        raise HTTPException(status_code=500, detail="Can not encode image")
    return base64.b64encode(encoded.tobytes()).decode("utf-8")


def classes_to_description(found: set[int]) -> str:
    lines = []
    person = 5 in found
    danger_objects = any(x in found for x in [6, 8, 9])

    if person:
        helmet_text = "есть каска" if 0 in found else "нет каски"
        mask_text = "есть маска" if 1 in found else "нет маски"
        vest_text = "есть жилет" if 7 in found else "нет жилета"
        lines.append(f"Обнаружен человек: {helmet_text}, {mask_text}, {vest_text}.")

    if person and danger_objects:
        lines.append("Предупреждение: опасная зона.")

    if not lines:
        return "Опасных объектов не обнаружено."

    return " ".join(lines)


def run_detection_and_draw(frame: np.ndarray):
    result = MODEL.predict(frame, conf=0.25, verbose=False)[0]
    found_classes = set()

    if result.boxes is not None:
        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            found_classes.add(cls_id)

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            color = COLORS.get(cls_id, (0, 255, 255))
            label = f"{CLASS_NAMES.get(cls_id, str(cls_id))} {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

    return frame, found_classes


@app.post("/img", response_model=ImgOut)
def detect_img(payload: ImgIn):
    img = decode_b64_to_image(payload.img)
    img_out, found = run_detection_and_draw(img)
    desc = classes_to_description(found)
    return ImgOut(img=encode_image_to_b64(img_out), description=desc)


@app.post("/video", response_model=VideoOut)
def detect_video(payload: VideoIn):
    try:
        video_bytes = base64.b64decode(payload.video)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Wrong video base64: {e}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        in_path = temp_dir_path / "in.mp4"
        out_path = temp_dir_path / "out.mp4"
        in_path.write_bytes(video_bytes)

        cap = cv2.VideoCapture(str(in_path))
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="Can not open input video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))
        if not writer.isOpened():
            cap.release()
            raise HTTPException(status_code=500, detail="Can not create output video")

        all_classes = set()

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame_out, found = run_detection_and_draw(frame)
            all_classes.update(found)
            writer.write(frame_out)

        cap.release()
        writer.release()

        if not out_path.exists():
            raise HTTPException(status_code=500, detail="Output video was not saved")

        out_b64 = base64.b64encode(out_path.read_bytes()).decode("utf-8")
        desc = classes_to_description(all_classes)
        return VideoOut(video=out_b64, description=desc)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
