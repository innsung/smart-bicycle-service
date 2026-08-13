"""따릉이 수요 예측 API에서 사용하는 요청 데이터 형식."""

from datetime import date as Date

from pydantic import BaseModel, Field


class DemandForecastRequest(BaseModel):
    """React에서 전달하는 대여소와 예측 시점."""

    station_id: str = Field(min_length=1, description="서울시 따릉이 대여소 ID")
    date: Date = Field(description="예측 날짜")
    hour: int = Field(ge=0, le=23, description="예측 시간(0~23시)")
