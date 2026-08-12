"""수요예측 후처리의 경계값과 실제 모델 추론을 검증합니다."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.demand_forecast_service import (
    build_feature_row,
    calculate_shortage_risk,
    predict_demand_and_risk,
)


def run() -> None:
    assert calculate_shortage_risk(29, 20) == {
        "predicted_demand": 29,
        "available_bikes": 20,
        "shortage_count": 9,
        "shortage_risk_percent": 100.0,
        "risk_level": "매우 높음",
        "demand_level": "높음",
        "shortage_risk": True,
    }
    assert calculate_shortage_risk(0, 0)["shortage_risk_percent"] == 0
    assert calculate_shortage_risk(3, 0)["shortage_risk_percent"] == 100
    assert calculate_shortage_risk(5, 20)["risk_level"] == "낮음"

    row = build_feature_row(
        station_id="207",
        target_datetime=datetime(2025, 12, 15, 10, tzinfo=ZoneInfo("Asia/Seoul")),
        weather={"temperature": 2.1, "humidity": 45, "rainfall": 0, "wind_speed": 2.0, "is_raining": False},
        historical={
            "district": "영등포구",
            "rental_lag_1h": 24, "rental_lag_2h": 22, "rental_lag_24h": 31,
            "rental_lag_168h": 29, "rental_rolling_mean_3h": 23,
            "rental_rolling_mean_24h": 18, "rental_rolling_mean_7d_same_hour": 29,
            "rental_rolling_std_24h": 4, "available_bikes_lag_1h": 19,
            "available_bikes_change_1h": 1,
        },
        current_available_bikes=20,
    )
    result = predict_demand_and_risk(row)
    assert result["predicted_demand"] >= 0
    assert 0 <= result["shortage_risk_percent"] <= 100
    assert result["available_bikes"] == 20
    print("demand forecast service test passed", result)


if __name__ == "__main__":
    run()
