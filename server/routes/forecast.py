"""다음 1시간 따릉이 수요·부족 위험도 예측 API."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from clients.kma_weather import KmaWeatherError, get_hourly_forecast
from clients.seoul_bike import RealtimeStation, SeoulBikeError
from routes.bike import get_bike_service
from schemas.forecast import DemandForecastRequest
from services.forecast import (
    build_feature_row,
    get_historical_features,
    predict_demand_and_risk,
)


router = APIRouter(tags=["bike-demand-forecast"])
SEOUL_TZ = ZoneInfo("Asia/Seoul")


def usage_station_id(station: RealtimeStation) -> str:
    """실시간 API 대여소명 앞 번호를 ML 학습 데이터의 station_id로 변환합니다."""
    matched = re.match(r"^\s*(\d+)", station.name)
    if matched:
        return matched.group(1).lstrip("0")
    return "".join(filter(str.isdigit, station.station_id)).lstrip("0")


def find_station(stations: list[RealtimeStation], requested_id: str) -> RealtimeStation | None:
    requested_id = requested_id.strip()
    requested_digits = "".join(filter(str.isdigit, requested_id)).lstrip("0")
    return next(
        (
            station for station in stations
            if station.station_id == requested_id
            or usage_station_id(station) == requested_digits
            or "".join(filter(str.isdigit, station.station_id)).lstrip("0") == requested_digits
        ),
        None,
    )


@router.post("/ai/bike/forecast")
async def forecast_demand(request: DemandForecastRequest):
    if not 0 <= request.hour <= 23:
        raise HTTPException(status_code=422, detail="hour는 0~23 사이여야 합니다.")

    try:
        stations = await get_bike_service().client.get_all_stations()
        station = find_station(stations, request.station_id)
        if station is None:
            raise HTTPException(status_code=404, detail="선택한 대여소를 실시간 API에서 찾을 수 없습니다.")

        target_datetime = datetime.combine(request.date, datetime.min.time(), SEOUL_TZ).replace(hour=request.hour)
        weather = await get_hourly_forecast(station.latitude, station.longitude, target_datetime)
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
            "station_name": re.sub(r"^\s*\d+\s*[.\-_:]?\s*", "", station.name).strip(),
            "prediction_datetime": target_datetime.isoformat(),
            "weather": weather,
            "historical_features": {
                "recent_1h_rental_count": historical["rental_lag_1h"],
                "prev_day_same_hour_rental_count": historical["rental_lag_24h"],
                "rolling_7d_same_hour_avg": historical["rental_rolling_mean_7d_same_hour"],
                "source_datetime": historical["datetime"],
            },
            "message": shortage_message(result),
        })
        return result
    except HTTPException:
        raise
    except (SeoulBikeError, KmaWeatherError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def shortage_message(result: dict) -> str:
    if result["shortage_count"] > 0:
        return f"예측 수요가 현재 자전거보다 {result['shortage_count']}대 많아 재배치를 권장합니다."
    remaining = max(result["available_bikes"] - result["predicted_demand"], 0)
    return f"예측 수요를 충족할 수 있으나 예상 여유 자전거는 {remaining}대입니다."
