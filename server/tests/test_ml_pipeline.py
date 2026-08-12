"""작은 인메모리 데이터로 Feature와 Target의 시간 방향을 검증합니다."""

import importlib

import pandas as pd


def run() -> None:
    module = importlib.import_module("ml.03_feature_engineering")
    hours = pd.date_range("2025-01-01", periods=200, freq="h")
    source = pd.DataFrame({
        "station_id": "102",
        "station_name": "망원역 1번출구 앞",
        "datetime": hours,
        "rental_count": range(200),
        "district": "마포구",
        "rack_count": 20,
        "temperature": 10,
        "humidity": 50,
        "rainfall": 0,
        "wind_speed": 2,
        "current_available_bikes": 10,
    })
    result = module.add_features_and_targets(source)
    row = result.iloc[168]
    assert row["rental_lag_1h"] == 167
    assert row["rental_lag_24h"] == 144
    assert row["rental_lag_168h"] == 0
    assert row["target_rental_count_1h"] == 169
    assert "current_occupancy_ratio" not in result.columns
    print("ML pipeline test passed")


if __name__ == "__main__":
    run()
