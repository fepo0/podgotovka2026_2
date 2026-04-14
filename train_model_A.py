"""
https://github.com/facebookresearch/fastText/issues/956
https://fasttext.cc/docs/en/python-module.html
"""

import re
import shutil
import os

import fasttext
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

DATASET_PATH = "dataset_A.csv"

ARTIFACTS_DIR = "fasttext_A"
ASCII_WORK_DIR = "../fasttext_A_ascii_work"

FASTTEXT_DATA_DIR = "fasttext_A/fasttext_data"
ASCII_FASTTEXT_DATA_DIR = "../fasttext_A_ascii_work/fasttext_data"

TEXT_COLUMN = "comment_text"

LABEL_COLUMNS = [
    "toxic",
    "severe_toxic",
    "obscene",
    "threat",
    "insult",
    "identity_hate",
]


def normalize_text(text: str):
    # Делаем текст чище перед обучением
    text = str(text).replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def load_dataset(path: str) -> pd.DataFrame:
    return pd.read_csv(path).dropna(subset=[TEXT_COLUMN] + LABEL_COLUMNS).drop_duplicates()


def analyze_dataset(df: pd.DataFrame) -> None:
    print("DATASET A ANALYSIS")
    print(f"Строк: {len(df):,}")
    print(f"Колонок: {list(df.columns)}")
    print(f"Пустые: {(df[TEXT_COLUMN].astype(str).str.strip() == '').sum():,}")
    print()

    # Смотрим сколько 0 и 1 в каждом классе
    print("---------------------------")
    for label in LABEL_COLUMNS:
        counts = df[label].value_counts().sort_index()
        zeros = int(counts.get(0, 0))
        ones = int(counts.get(1, 0))

        print(f"{label}:")
        print(f"0 = {zeros:,}")
        print(f"1 = {ones:,}")
        print()


def save_fasttext_format(df: pd.DataFrame, label: str, output_path: str):
    # fastText учится на строках такого вида:
    # __label__0 some text
    # __label__1 some other text
    lines = []
    for _, row in df.iterrows():
        target = int(row[label])
        text = normalize_text(row[TEXT_COLUMN])
        if not text:
            continue
        lines.append(f"__label__{target} {text}")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def predict_label(model, text: str) -> int:
    text = normalize_text(text)
    if not text:
        return 0

    predictions = model.f.predict(f"{text}\n", 1, 0.0, "strict")
    if not predictions:
        return 0

    _, predicted_label = predictions[0]
    return int(predicted_label.replace("__label__", ""))


def evaluate_model(model, valid_df, label):
    y_true = valid_df[label].astype(int).tolist()
    texts = valid_df[TEXT_COLUMN].astype(str).map(normalize_text).tolist()

    predictions = []
    for text in texts:
        predictions.append(predict_label(model, text))

    accuracy = accuracy_score(y_true, predictions)
    f1 = f1_score(y_true, predictions, zero_division=0)
    report = classification_report(y_true, predictions, zero_division=0)
    return accuracy, f1, report


def train_for_label(df, label):
    label_dir = os.path.join(ARTIFACTS_DIR, label)
    ascii_label_dir = os.path.join(ASCII_WORK_DIR, label)
    os.makedirs(FASTTEXT_DATA_DIR, exist_ok=True)
    os.makedirs(ASCII_FASTTEXT_DATA_DIR, exist_ok=True)
    os.makedirs(label_dir, exist_ok=True)
    os.makedirs(ascii_label_dir, exist_ok=True)

    train_df, valid_df = train_test_split(
        df[[TEXT_COLUMN, label]],
        test_size=0.2,
        random_state=42,
        stratify=df[label],
    )

    train_txt = os.path.join(FASTTEXT_DATA_DIR, f"{label}_train.txt")
    valid_txt = os.path.join(FASTTEXT_DATA_DIR, f"{label}_valid.txt")
    ascii_train_txt = os.path.join(ASCII_FASTTEXT_DATA_DIR, f"{label}_train.txt")
    ascii_valid_txt = os.path.join(ASCII_FASTTEXT_DATA_DIR, f"{label}_valid.txt")
    save_fasttext_format(train_df, label, train_txt)
    save_fasttext_format(valid_df, label, valid_txt)
    save_fasttext_format(train_df, label, ascii_train_txt)
    save_fasttext_format(valid_df, label, ascii_valid_txt)

    model = fasttext.train_supervised(
        input=ascii_train_txt,
        lr=0.5,
        epoch=20,
        dim=100,
        wordNgrams=2,
        minn=2,
        maxn=5,
        loss="ova",  # много 0 и мало 1
    )

    ascii_model_path = os.path.join(ascii_label_dir, f"{label}_fasttext.bin")
    model_path = os.path.join(label_dir, f"{label}_fasttext.bin")
    model.save_model(ascii_model_path)
    shutil.copy2(ascii_model_path, model_path)

    accuracy, f1, report = evaluate_model(model, valid_df, label)

    print(f"Label: {label}")
    print(f"Train size: {len(train_df)}")
    print(f"Validation size: {len(valid_df)}")
    print(f"Model saved to: {model_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1: {f1:.4f}")
    print("Classification report:")
    print(report)
    print()


df = load_dataset(DATASET_PATH)

# Анализируем датасет перед обучением.
analyze_dataset(df)

for label in LABEL_COLUMNS:
    train_for_label(df, label)
