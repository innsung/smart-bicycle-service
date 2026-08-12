"""API 추론용 대여소·시간대별 최신 이용 패턴 스냅샷 생성.

대용량 Feature CSV를 API 요청마다 읽지 않도록 station_id + hour별 가장 최근
Feature만 작은 CSV로 저장합니다. 사용자는 과거 이용량을 직접 입력하지 않습니다.
"""

import pandas as pd

from ml.config import DATASET_PATH, INFERENCE_FEATURES_PATH


STORE_COLUMNS = [
    "station_id", "station_name", "district", "datetime", "hour",
    "rental_lag_1h", "rental_lag_2h", "rental_lag_24h", "rental_lag_168h",
    "rental_rolling_mean_3h", "rental_rolling_mean_24h",
    "rental_rolling_mean_7d_same_hour", "rental_rolling_std_24h",
    "current_available_bikes", "available_bikes_lag_1h", "available_bikes_change_1h",
]


def build_inference_store() -> None:
    latest_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(DATASET_PATH, usecols=STORE_COLUMNS, chunksize=200_000, low_memory=False):
        chunk["datetime"] = pd.to_datetime(chunk["datetime"], errors="coerce")
        latest_parts.append(
            chunk.sort_values("datetime").drop_duplicates(["station_id", "hour"], keep="last")
        )
    store = pd.concat(latest_parts, ignore_index=True)
    store = store.sort_values("datetime").drop_duplicates(["station_id", "hour"], keep="last")
    INFERENCE_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    store.to_csv(INFERENCE_FEATURES_PATH, index=False, encoding="utf-8-sig")
    print(f"추론 Feature 저장 완료: {len(store):,}행 → {INFERENCE_FEATURES_PATH}")


if __name__ == "__main__":
    build_inference_store()
