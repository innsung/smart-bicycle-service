"""선택한 미래 시각의 대여수요와 자전거 부족 위험도를 계산하는 서비스."""

from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd

from clients.kma_weather import get_hourly_forecast
from clients.seoul_bike import RealtimeStation, SeoulBikeClient
from ml.config import INFERENCE_FEATURES_PATH, MODEL_PATH
from schemas.forecast import DemandForecastRequest


RISK_THRESHOLDS = (
    (90, "매우 높음"),
    (70, "높음"),
    (40, "보통"),
    (0, "낮음"),
)
SEOUL_TZ = ZoneInfo("Asia/Seoul")


class ForecastService:
    """실시간 대여소·날씨·과거 Feature를 조합해 수요를 예측합니다."""

    def __init__(self, bike_client: SeoulBikeClient) -> None:
        self.bike_client = bike_client

    async def forecast(self, request: DemandForecastRequest) -> dict:
        stations = await self.bike_client.get_all_stations()
        station = find_station(stations, request.station_id)
        if station is None:
            raise LookupError("선택한 대여소를 실시간 API에서 찾을 수 없습니다.")

        target_datetime = datetime.combine(
            request.date, datetime.min.time(), SEOUL_TZ
        ).replace(hour=request.hour)
        weather = await get_hourly_forecast(
            station.latitude, station.longitude, target_datetime
        )
        ml_station_id = usage_station_id(station)
        historical = get_historical_features(ml_station_id, request.hour)
        feature_row = build_feature_row(
            station_id=ml_station_id,
            target_datetime=target_datetime,
            weather=weather,
            historical=historical,
            current_available_bikes=station.available_bikes,
        )
        result = predict_demand_and_risk(feature_row)
        result.update({
            "station_id": station.station_id,
            "usage_station_id": ml_station_id,
            "station_name": clean_station_name(station.name),
            "prediction_datetime": target_datetime.isoformat(),
            "weather": weather,
            "historical_features": {
                "recent_1h_rental_count": historical["rental_lag_1h"],
                "prev_day_same_hour_rental_count": historical["rental_lag_24h"],
                "rolling_7d_same_hour_avg": historical[
                    "rental_rolling_mean_7d_same_hour"
                ],
                "source_datetime": historical["datetime"],
            },
            "message": shortage_message(result),
        })
        return result


def usage_station_id(station: RealtimeStation) -> str:
    """실시간 API 대여소명을 ML 학습 데이터의 station_id로 변환합니다."""
    matched = re.match(r"^\s*(\d+)", station.name)
    if matched:
        return matched.group(1).lstrip("0")
    return "".join(filter(str.isdigit, station.station_id)).lstrip("0")


def find_station(
    stations: list[RealtimeStation], requested_id: str
) -> RealtimeStation | None:
    """서울시 API ID와 이용정보 CSV 번호를 모두 허용해 대여소를 찾습니다."""
    requested_id = requested_id.strip()
    requested_digits = "".join(filter(str.isdigit, requested_id)).lstrip("0")
    return next(
        (
            station
            for station in stations
            if station.station_id == requested_id
            or usage_station_id(station) == requested_digits
            or "".join(filter(str.isdigit, station.station_id)).lstrip("0")
            == requested_digits
        ),
        None,
    )


def clean_station_name(name: str) -> str:
    return re.sub(r"^\s*\d+\s*[.\-_:]?\s*", "", name).strip()


def shortage_message(result: dict) -> str:
    if result["shortage_count"] > 0:
        return (
            f"예측 수요가 현재 자전거보다 {result['shortage_count']}대 많아 "
            "재배치를 권장합니다."
        )
    remaining = max(result["available_bikes"] - result["predicted_demand"], 0)
    return f"예측 수요를 충족할 수 있으나 예상 여유 자전거는 {remaining}대입니다."


def calculate_shortage_risk(predicted_demand: int | float, available_bikes: int | float) -> dict:
    """예측 수요와 현재 자전거 수를 비교해 부족 대수와 위험도를 계산합니다."""
    demand = max(0, int(round(float(predicted_demand))))
    available = max(0, int(float(available_bikes)))
    shortage_count = max(demand - available, 0)

    if demand == 0:
        risk_percent = 0.0
    elif available == 0:
        risk_percent = 100.0
    else:
        risk_percent = min(100.0, round(demand / available * 100, 1))

    risk_level = next(label for threshold, label in RISK_THRESHOLDS if risk_percent >= threshold)
    return {
        "predicted_demand": demand,
        "available_bikes": available,
        "shortage_count": shortage_count,
        "shortage_risk_percent": risk_percent,
        "risk_level": risk_level,
        "demand_level": "높음" if risk_percent >= 70 else "보통" if risk_percent >= 40 else "낮음",
        "shortage_risk": shortage_count > 0,
    }


@lru_cache(maxsize=1)
def _load_model_artifact() -> dict:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"학습 모델을 찾을 수 없습니다: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def _load_inference_features() -> pd.DataFrame:
    if not INFERENCE_FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"추론 Feature를 찾을 수 없습니다: {INFERENCE_FEATURES_PATH}. "
            "python -m ml.07_build_inference_store를 먼저 실행하세요."
        )
    frame = pd.read_csv(INFERENCE_FEATURES_PATH, dtype={"station_id": str})
    frame["station_key"] = frame["station_id"].str.extract(r"(\d+)", expand=False).str.lstrip("0")
    return frame


def get_historical_features(station_id: str, hour: int) -> dict:
    """선택 대여소·시간대의 최신 과거 이용 패턴을 자동 조회합니다."""
    station_key = "".join(filter(str.isdigit, str(station_id))).lstrip("0")
    store = _load_inference_features()
    matched = store[(store["station_key"] == station_key) & (store["hour"] == hour)]
    if matched.empty:
        raise ValueError(f"대여소 {station_id}의 {hour:02d}시 과거 이용 패턴이 없습니다.")
    return matched.sort_values("datetime").iloc[-1].to_dict()


def build_feature_row(
    *, station_id: str, target_datetime: datetime, weather: dict,
    historical: dict, current_available_bikes: int,
) -> dict:
    """API 입력과 자동 조회 데이터를 학습 시 사용한 Feature 이름으로 변환합니다."""
    hour = target_datetime.hour
    dow = target_datetime.weekday()
    return {
        "station_id": station_id,
        "district": historical.get("district") or "미상",
        "year": target_datetime.year,
        "month": target_datetime.month,
        "hour": hour,
        "day_of_week": dow,
        "is_weekend": int(dow >= 5),
        "is_holiday": int(dow >= 5),
        "is_morning_peak": int(7 <= hour <= 9),
        "is_evening_peak": int(17 <= hour <= 19),
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "dow_sin": np.sin(2 * np.pi * dow / 7),
        "dow_cos": np.cos(2 * np.pi * dow / 7),
        "temperature": weather["temperature"],
        "humidity": weather["humidity"],
        "rainfall": weather["rainfall"],
        "is_raining": int(weather["is_raining"]),
        "wind_speed": weather["wind_speed"],
        "rental_lag_1h": historical["rental_lag_1h"],
        "rental_lag_2h": historical["rental_lag_2h"],
        "rental_lag_24h": historical["rental_lag_24h"],
        "rental_lag_168h": historical["rental_lag_168h"],
        "rental_rolling_mean_3h": historical["rental_rolling_mean_3h"],
        "rental_rolling_mean_24h": historical["rental_rolling_mean_24h"],
        "rental_rolling_mean_7d_same_hour": historical["rental_rolling_mean_7d_same_hour"],
        "rental_rolling_std_24h": historical["rental_rolling_std_24h"],
        "current_available_bikes": current_available_bikes,
        "available_bikes_lag_1h": historical.get("available_bikes_lag_1h", current_available_bikes),
        "available_bikes_change_1h": historical.get("available_bikes_change_1h", 0),
    }


def predict_demand_and_risk(feature_row: dict) -> dict:
    """저장된 3개월 모델로 수요를 예측하고 부족 위험도를 후처리합니다."""
    artifact = _load_model_artifact()
    feature_columns = artifact["feature_columns"]
    frame = pd.DataFrame([{column: feature_row.get(column) for column in feature_columns}])
    prediction = float(artifact["pipeline"].predict(frame)[0])
    return calculate_shortage_risk(prediction, feature_row["current_available_bikes"])
