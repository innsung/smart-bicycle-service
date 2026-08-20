"""회원별 AI 수요예측 결과를 저장하는 SQLAlchemy 모델."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.connection import Base

if TYPE_CHECKING:
    from models.member import BikeMember


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BikePredictionHistory(Base):
    """bike_member 1명에 여러 예측 이력이 연결되는 N측 테이블입니다."""

    __tablename__ = "bike_prediction_history"

    prediction_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("bike_member.member_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    station_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    station_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prediction_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    predicted_demand: Mapped[int] = mapped_column(Integer, nullable=False)
    available_bikes: Mapped[int] = mapped_column(Integer, nullable=False)
    shortage_count: Mapped[int] = mapped_column(Integer, nullable=False)
    shortage_risk_percent: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    member: Mapped["BikeMember"] = relationship(back_populates="prediction_histories")
