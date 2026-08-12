"""[Feature Engineering·Target 생성]

병합된 시계열에서 날짜/주기/Lag/Rolling Feature를 만들고, 다음 1시간의 실제 값을
Target으로 이동(shift -1)합니다. 모든 Rolling 값은 shift(1) 이후 계산해 현재 행이
자기 자신의 정답을 보는 데이터 누수를 방지합니다.
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# 이 파일을 ml 폴더에서 직접 실행해도 `ml` 패키지를 찾도록 server 경로를 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.columns import FEATURE_COLUMNS, TARGET_COLUMNS
from ml.config import DATASET_PATH, PROCESSED_DIR
from ml.holidays import is_fixed_holiday


def add_features_and_targets(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values(["station_id", "datetime"]).drop_duplicates(["station_id", "datetime"], keep="last")
    station_group = df.groupby("station_id", group_keys=False)

    # 운영 중단·신규 개설로 긴 공백이 있으면 별도 연속 구간으로 분리합니다.
    # 따라서 shift(1)는 항상 같은 대여소의 정확히 1시간 전 행만 가리킵니다.
    interval = station_group["datetime"].diff()
    df["continuous_segment"] = interval.ne(pd.Timedelta(hours=1)).groupby(df["station_id"]).cumsum()
    grouped = df.groupby(["station_id", "continuous_segment"], group_keys=False)

    # 날짜·시간 Feature
    df["year"] = df["datetime"].dt.year  # 관측 연도
    df["month"] = df["datetime"].dt.month  # 관측 월
    df["hour"] = df["datetime"].dt.hour  # 관측 시간
    df["day_of_week"] = df["datetime"].dt.dayofweek  # 월요일 0 ~ 일요일 6
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype("int8")  # 주말 여부
    df["is_holiday"] = is_fixed_holiday(df["datetime"])  # 고정 공휴일 여부
    df["is_morning_peak"] = df["hour"].between(7, 9).astype("int8")  # 출근 시간 여부
    df["is_evening_peak"] = df["hour"].between(17, 19).astype("int8")  # 퇴근 시간 여부
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)  # 시간 주기성 sin
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)  # 시간 주기성 cos
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)  # 요일 주기성 sin
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)  # 요일 주기성 cos
    df["rainfall"] = pd.to_numeric(df["rainfall"], errors="coerce")
    df["is_raining"] = (df["rainfall"].fillna(0) > 0).astype("int8")  # 강수 여부

    # 과거 수요 Feature
    df["rental_lag_1h"] = grouped["rental_count"].shift(1)  # 1시간 전 대여량
    df["rental_lag_2h"] = grouped["rental_count"].shift(2)  # 2시간 전 대여량
    df["rental_lag_24h"] = grouped["rental_count"].shift(24)  # 전일 동일 시간 대여량
    df["rental_lag_168h"] = grouped["rental_count"].shift(168)  # 전주 동일 시간 대여량
    shifted_rentals = grouped["rental_count"].shift(1)
    segment_keys = [df["station_id"], df["continuous_segment"]]
    df["rental_rolling_mean_3h"] = shifted_rentals.groupby(segment_keys).rolling(3, min_periods=1).mean().reset_index(level=[0, 1], drop=True)
    df["rental_rolling_mean_24h"] = shifted_rentals.groupby(segment_keys).rolling(24, min_periods=3).mean().reset_index(level=[0, 1], drop=True)
    df["rental_rolling_std_24h"] = shifted_rentals.groupby(segment_keys).rolling(24, min_periods=3).std().reset_index(level=[0, 1], drop=True)
    same_hour_sum = sum(grouped["rental_count"].shift(24 * day) for day in range(1, 8))
    same_hour_count = sum(grouped["rental_count"].shift(24 * day).notna().astype(int) for day in range(1, 8))
    df["rental_rolling_mean_7d_same_hour"] = same_hour_sum / same_hour_count.replace(0, np.nan)  # 최근 7일 같은 시간 평균

    # 재고 Feature
    df["current_available_bikes"] = pd.to_numeric(df["current_available_bikes"], errors="coerce")
    df["available_bikes_lag_1h"] = grouped["current_available_bikes"].shift(1)  # 1시간 전 자전거 수
    df["available_bikes_change_1h"] = df["current_available_bikes"] - df["available_bikes_lag_1h"]  # 1시간 재고 증감

    # Target: 현재 시각 t의 Feature로 다음 시각 t+1을 예측합니다.
    df["target_rental_count_1h"] = grouped["rental_count"].shift(-1)  # 다음 1시간 실제 대여 건수

    # 모든 계약 컬럼이 존재하도록 보장합니다. 선택 외부 데이터가 없으면 NaN으로 남습니다.
    for column in FEATURE_COLUMNS + TARGET_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    return df


def build_feature_dataset() -> None:
    source = PROCESSED_DIR / "bike_hourly_merged.csv.gz"
    df = pd.read_csv(source, parse_dates=["datetime"])
    featured = add_features_and_targets(df)
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    featured.to_csv(DATASET_PATH, index=False, compression="gzip")
    print(f"Feature Engineering 완료: {len(featured):,}행 → {DATASET_PATH}")


if __name__ == "__main__":
    build_feature_dataset()
