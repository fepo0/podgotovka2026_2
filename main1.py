import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
import fasttext
import re
import os
from functools import lru_cache

# + Федорцова П.С.
FASTTEXT_MODELS_DIR = "fasttext_A"
FASTTEXT_A_ASCII_WORK_DIR = "../fasttext_A_ascii_work"
FASTTEXT_B_MODEL_PATH = "fasttext_B/cyberbullying_fasttext.bin"
FASTTEXT_B_ASCII_MODEL_PATH = "../fasttext_B_ascii_work/cyberbullying_fasttext.bin"
FASTTEXT_LOAD_CACHE_DIR = "../fasttext_load_cache"
TOXIC_LABELS = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
]
# - Федорцова П.С.


def get_pred(model, text):
  text = clean_text(text)
# + Федорцова П.С. 
#   pred = model.predict(text)
#   pred_int = int(pred[0][0][9])
  if not text:
    return 0
  predictions = model.f.predict(f"{text}\n", 1, 0.0, "strict")
  if not predictions:
    return 0
  pred_int = int(predictions[0][1].replace("__label__", ""))
# - Федорцова П.С.
  return pred_int

def get_model(path):
  # + Федорцова П.С.
  # model = fasttext.load_model(path)
  try:
    model = fasttext.load_model(path)
  except ValueError:
    source_path = path
    os.makedirs(FASTTEXT_LOAD_CACHE_DIR, exist_ok=True)
    cached_model_path = os.path.join(FASTTEXT_LOAD_CACHE_DIR, os.path.basename(source_path))
    with open(source_path, "rb") as source_file:
      with open(cached_model_path, "wb") as cached_file:
        cached_file.write(source_file.read())
    model = fasttext.load_model(cached_model_path)
# return model1
  return model
# - Федорцова П.С.

# + Федорцова П.С.
@lru_cache(maxsize=1)
def load_toxic_models():
    models = {}
    for label in TOXIC_LABELS:
        model_path = os.path.join(FASTTEXT_MODELS_DIR, label, f"{label}_fasttext.bin")
        ascii_model_path = os.path.join(FASTTEXT_A_ASCII_WORK_DIR, label, f"{label}_fasttext.bin")
        if os.path.exists(ascii_model_path):
            models[label] = get_model(ascii_model_path)
        elif os.path.exists(model_path):
            models[label] = get_model(model_path)
    return models


@lru_cache(maxsize=1)
def load_cyberbullying_model():
    if os.path.exists(FASTTEXT_B_MODEL_PATH):
        return get_model(FASTTEXT_B_MODEL_PATH)
    if os.path.exists(FASTTEXT_B_ASCII_MODEL_PATH):
        return get_model(FASTTEXT_B_ASCII_MODEL_PATH)
    return None


def predict_toxic_labels(text: str) -> dict[str, int]:
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return {label: 0 for label in TOXIC_LABELS}

    models = load_toxic_models()
    predictions = {}
    for label in TOXIC_LABELS:
        model = models.get(label)
        predictions[label] = get_pred(model, cleaned_text) if model is not None else 0
    return predictions


def predict_cyberbullying_type(text: str) -> int:
    cleaned_text = clean_text(text)
    if not cleaned_text:
        return 4

    model = load_cyberbullying_model()
    if model is None:
        return 4

    return get_pred(model, cleaned_text)
# - Федорцова П.С.

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\sa-zA-Z0-9@\[\]]',' ',text)
    text = re.sub(r'\w*\d+\w*', '', text)
    text = re.sub('\s{2,}', " ", text)
    return text

app = FastAPI(title='BabaYaga')

class Comment(BaseModel):
    # + Федорцова П.С.
    # comm: str
    comm: str = Field(validation_alias="text")
    # - Федорцова П.С.

class Usefull_comm_to_tg(BaseModel):
    toxic: int 
    severe_toxic: int
# + Федорцова П.С.
#   obscere: int    
    obscene: int
# - Федорцова П.С.
    threat: int
    insult: int
    identity_hate: int

class Cyberbul_to_tg(BaseModel):
    # + Федорцова П.С.
    # come_type: int()
    come_type: int
    # - Федорцова П.С.

class Coandce_to_tg(BaseModel):
    toxic: int 
    severe_toxic: int
# + Федорцова П.С.
#   obscere: int
    obscene: int
    threat: int
# - Федорцова П.С.
    insult: int
    identity_hate: int
    type_cyberbyllying: int
# + Федорцова П.С.
#class Cyber_Buller_Comm(BaseModel):
# - Федорцова П.С.

@app.get("/")
def read_root():
    return {"messege": "fuck u!"}

@app.post("/comment")
def post_comment(text:Comment):
    # + Федорцова П.С.
    toxic_pred = predict_toxic_labels(text.comm)
    # - Федорцова П.С.
    usefull_com = Usefull_comm_to_tg(
        # + Федорцова П.С.
        # toxic=0,
        # severe_toxic = 0,
        # obscere = 0,
        # threat = 0,
        # insult = 0,
        # identity_hate = 0)
        toxic=toxic_pred["toxic"],
        severe_toxic = toxic_pred["severe_toxic"],
        obscene = toxic_pred["obscene"],
        threat = toxic_pred["threat"],
        insult = toxic_pred["insult"],
        identity_hate = toxic_pred["identity_hate"])
        # - Федорцова П.С.
    return usefull_com

@app.post("/cyberbullying")
def post_cyberbul_comm(text:Comment):    
    cyberbul_comm = Cyberbul_to_tg(
        # + Федорцова П.С.
        # come_type = get_pred(get_model("optimized.model"), clean_text(text.comm)))
        come_type = predict_cyberbullying_type(text.comm))
        # - Федорцова П.С.
    return cyberbul_comm

@app.post("/coandcy")
def post_coandcy_comm(text:Comment):
    # + Федорцова П.С.
    toxic_pred = predict_toxic_labels(text.comm)
    # - Федорцова П.С.
    coandce_comm = Coandce_to_tg(
        # + Федорцова П.С.
        # toxic = 0,
        # severe_toxic = 0,
        # obscere = 0,
        # insult = 0,
        # identity_hate = 0,
        # type_cyberbyllying = 0
        toxic = toxic_pred["toxic"],
        severe_toxic = toxic_pred["severe_toxic"],
        obscene = toxic_pred["obscene"],
        threat = toxic_pred["threat"],
        insult = toxic_pred["insult"],
        identity_hate = toxic_pred["identity_hate"],
        type_cyberbyllying = predict_cyberbullying_type(text.comm)
        # - Федорцова П.С.
        )
    return coandce_comm



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)