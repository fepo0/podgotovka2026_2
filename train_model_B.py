import re
import shutil
import os

import fasttext
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

DATASET_PATH = "dataset_B.csv"

ARTIFACTS_DIR = "fasttext_B"
ASCII_WORK_DIR = "../fasttext_B_ascii_work"

FASTTEXT_DATA_DIR = "fasttext_B/fasttext_data"
ASCII_FASTTEXT_DATA_DIR = "../fasttext_B_ascii_work/fasttext_data"

TEXT_COLUMN = "tweet_text"
LABEL_COLUMN = "cyberbullying_type"


def normalize_text(text: str) -> str:
    text = str(text).replace("\n", " ").replace("\r", " ")
    text = text.lower()
    text = re.sub(r"[^\sa-zA-Z0-9@\[\]]", " ", text)
    text = re.sub(r"\w*\d+\w*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path).dropna(subset=[TEXT_COLUMN, LABEL_COLUMN]).drop_duplicates()
    df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int)
    return df


def analyze_dataset(df: pd.DataFrame) -> None:
    print("DATASET B ANALYSIS")
    print(f"Строк: {len(df):,}")
    print(f"Колонок: {list(df.columns)}")
    print(f"Пустые: {(df[TEXT_COLUMN].astype(str).str.strip() == '').sum():,}")
    print()

    print("---------------------------")
    print(f"{LABEL_COLUMN}:")
    counts = df[LABEL_COLUMN].value_counts().sort_index()
    for class_id, count in counts.items():
        print(f"{int(class_id)} = {int(count):,}")
    print()


def save_fasttext_format(df: pd.DataFrame, output_path: str) -> None:
    lines = []
    for _, row in df.iterrows():
        target = int(row[LABEL_COLUMN])
        text = normalize_text(row[TEXT_COLUMN])
        if not text:
            continue
        lines.append(f"__label__{target} {text}")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


def predict_label(model, text: str) -> int:
    text = normalize_text(text)
    if not text:
        return 4

    predictions = model.f.predict(f"{text}\n", 1, 0.0, "strict")
    if not predictions:
        return 4

    _, predicted_label = predictions[0]
    return int(predicted_label.replace("__label__", ""))


def evaluate_model(model, valid_df: pd.DataFrame) -> tuple[float, float, str]:
    y_true = valid_df[LABEL_COLUMN].astype(int).tolist()
    texts = valid_df[TEXT_COLUMN].astype(str).tolist()

    predictions = []
    for text in texts:
        predictions.append(predict_label(model, text))

    accuracy = accuracy_score(y_true, predictions)
    f1 = f1_score(y_true, predictions, average="weighted", zero_division=0)
    report = classification_report(y_true, predictions, zero_division=0)
    return accuracy, f1, report


def train_model(df: pd.DataFrame) -> None:
    os.makedirs(FASTTEXT_DATA_DIR, exist_ok=True)
    os.makedirs(ASCII_FASTTEXT_DATA_DIR, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(ASCII_WORK_DIR, exist_ok=True)

    train_df, valid_df = train_test_split(
        df[[TEXT_COLUMN, LABEL_COLUMN]],
        test_size=0.2,
        random_state=42,
        stratify=df[LABEL_COLUMN],
    )

    train_txt = os.path.join(FASTTEXT_DATA_DIR, "cyberbullying_train.txt")
    valid_txt = os.path.join(FASTTEXT_DATA_DIR, "cyberbullying_valid.txt")
    ascii_train_txt = os.path.join(ASCII_FASTTEXT_DATA_DIR, "cyberbullying_train.txt")
    ascii_valid_txt = os.path.join(ASCII_FASTTEXT_DATA_DIR, "cyberbullying_valid.txt")

    save_fasttext_format(train_df, train_txt)
    save_fasttext_format(valid_df, valid_txt)
    save_fasttext_format(train_df, ascii_train_txt)
    save_fasttext_format(valid_df, ascii_valid_txt)

    model = fasttext.train_supervised(
        input=ascii_train_txt,
        lr=0.5,
        epoch=20,
        dim=100,
        wordNgrams=2,
        minn=2,
        maxn=5,
        loss="softmax",
    )

    ascii_model_path = os.path.join(ASCII_WORK_DIR, "cyberbullying_fasttext.bin")
    model_path = os.path.join(ARTIFACTS_DIR, "cyberbullying_fasttext.bin")
    model.save_model(ascii_model_path)
    shutil.copy2(ascii_model_path, model_path)

    accuracy, f1, report = evaluate_model(model, valid_df)

    print("Label: cyberbullying_type")
    print(f"Train size: {len(train_df)}")
    print(f"Validation size: {len(valid_df)}")
    print(f"Model saved to: {model_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"F1 weighted: {f1:.4f}")
    print("Classification report:")
    print(report)
    print()


df = load_dataset(DATASET_PATH)

# Анализируем датасет перед обучением.
analyze_dataset(df)
train_model(df)
