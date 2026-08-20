"""따릉이 수요·부족 위험도 예측 HTTP API."""

from functools import lru_cache

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from clients.kma_weather import KmaWeatherError
from clients.seoul_bike import SeoulBikeClient, SeoulBikeError
from core.security import get_current_member_id, get_optional_member_id
from database.connection import get_db
from models.prediction import BikePredictionHistory
from schemas.forecast import DemandForecastRequest, PredictionHistoryResponse
from services.forecast import ForecastService


router = APIRouter(tags=["bike-demand-forecast"])


@lru_cache
def get_forecast_service() -> ForecastService:
    """강의 구조처럼 라우터가 사용할 Service 의존성을 한 곳에서 생성합니다."""
    return ForecastService(SeoulBikeClient())


@router.post("/ai/bike/forecast")
async def forecast_demand(
    request: DemandForecastRequest,
    member_id: int | None = Depends(get_optional_member_id),
    db: Session = Depends(get_db),
):
    try:
        result = await get_forecast_service().forecast(request)
        if member_id is not None:
            history = BikePredictionHistory(
                member_id=member_id,
                station_id=result["station_id"],
                station_name=result["station_name"],
                prediction_datetime=datetime.fromisoformat(result["prediction_datetime"]),
                predicted_demand=result["predicted_demand"],
                available_bikes=result["available_bikes"],
                shortage_count=result["shortage_count"],
                shortage_risk_percent=result["shortage_risk_percent"],
                risk_level=result["risk_level"],
            )
            db.add(history)
            db.commit()
            db.refresh(history)
            result["history_id"] = history.prediction_id
        else:
            result["history_id"] = None
        return result
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (SeoulBikeError, KmaWeatherError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/ai/bike/forecast/history", response_model=list[PredictionHistoryResponse])
def get_prediction_history(
    limit: int = Query(default=20, ge=1, le=100),
    member_id: int = Depends(get_current_member_id),
    db: Session = Depends(get_db),
):
    """로그인 회원 본인의 최신 수요예측 이력을 조회합니다."""
    statement = (
        select(BikePredictionHistory)
        .where(BikePredictionHistory.member_id == member_id)
        .order_by(BikePredictionHistory.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement))
