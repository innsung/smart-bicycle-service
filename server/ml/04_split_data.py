"""[데이터 분리]

시계열 데이터는 랜덤 분리하면 미래 정보가 과거 학습에 섞일 수 있습니다. 따라서
2022~2024 Train, 2025 상반기 Validation, 2025 하반기 Test로 시간순 분리합니다.
"""

import pandas as pd
import sys
from pathlib import Path

# 이 파일을 ml 폴더에서 직접 실행해도 `ml` 패키지를 찾도록 server 경로를 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.config import DATASET_PATH, PROCESSED_DIR, TEST_END, TRAIN_END, VALIDATION_END


def split_by_time(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    datetime = pd.to_datetime(df["datetime"])
    train = df[datetime <= TRAIN_END].copy()  # 모델이 학습하는 과거 데이터
    validation = df[(datetime > TRAIN_END) & (datetime <= VALIDATION_END)].copy()  # 모델 선택·튜닝 데이터
    test = df[(datetime > VALIDATION_END) & (datetime <= TEST_END)].copy()  # 최종 성능 확인 데이터
    return train, validation, test


def save_splits() -> None:
    df = pd.read_csv(DATASET_PATH, parse_dates=["datetime"])
    for name, split in zip(("train", "validation", "test"), split_by_time(df)):
        path = PROCESSED_DIR / f"{name}.csv.gz"
        split.to_csv(path, index=False, compression="gzip")
        print(f"{name}: {len(split):,}행 → {path}")


def save_month_splits() -> None:
    """선택한 한 달을 날짜순 70% Train, 15% Validation, 15% Test로 분리합니다."""
    df = pd.read_csv(DATASET_PATH, parse_dates=["datetime"])
    unique_times = pd.Series(df["datetime"].dropna().sort_values().unique())
    if len(unique_times) < 7 * 24:
        raise ValueError("월 단위 성능 테스트에는 최소 7일 이상의 연속 데이터가 필요합니다.")
    train_cut = unique_times.iloc[int(len(unique_times) * 0.70) - 1]
    validation_cut = unique_times.iloc[int(len(unique_times) * 0.85) - 1]
    # target은 현재 시각이 아니라 1시간 뒤 대여량이므로 target 시각을 기준으로 나눕니다.
    # 이렇게 해야 Train 마지막 행의 정답이 Validation 구간에서 넘어오는 누수를 막을 수 있습니다.
    target_datetime = df["datetime"] + pd.Timedelta(hours=1)
    splits = {
        "train": df[target_datetime <= train_cut].copy(),
        "validation": df[(target_datetime > train_cut) & (target_datetime <= validation_cut)].copy(),
        "test": df[target_datetime > validation_cut].copy(),
    }
    for name, split in splits.items():
        path = PROCESSED_DIR / f"{name}.csv.gz"
        split.to_csv(path, index=False, compression="gzip")
        print(f"{name}: {len(split):,}행 ({split['datetime'].min()} ~ {split['datetime'].max()}) → {path}")


def save_fixed_test_splits(test_month: str) -> None:
    """Test 월을 고정하고, 그 이전 학습 구간의 마지막 15%를 Validation으로 분리합니다."""
    df = pd.read_csv(DATASET_PATH, parse_dates=["datetime"])
    test_period = pd.Period(test_month, freq="M")
    test_start = test_period.start_time
    test_end = test_period.end_time
    target_datetime = df["datetime"] + pd.Timedelta(hours=1)
    pretest = df[target_datetime < test_start].copy()
    test = df[(target_datetime >= test_start) & (target_datetime <= test_end)].copy()
    unique_times = pd.Series(pretest["datetime"].dropna().sort_values().unique())
    if len(unique_times) < 7 * 24:
        raise ValueError("고정 Test 평가 전에 최소 7일 이상의 학습 데이터가 필요합니다.")
    validation_cut = unique_times.iloc[int(len(unique_times) * 0.85) - 1]
    train = pretest[pretest["datetime"] <= validation_cut].copy()
    validation = pretest[pretest["datetime"] > validation_cut].copy()
    for name, split in {"train": train, "validation": validation, "test": test}.items():
        path = PROCESSED_DIR / f"{name}.csv.gz"
        split.to_csv(path, index=False, compression="gzip")
        print(f"{name}: {len(split):,}행 ({split['datetime'].min()} ~ {split['datetime'].max()}) → {path}")


if __name__ == "__main__":
    save_splits()
