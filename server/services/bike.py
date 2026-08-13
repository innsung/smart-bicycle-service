from datetime import datetime
import re
from zoneinfo import ZoneInfo

from clients.seoul_bike import RealtimeStation, SeoulBikeClient
from repositories.usage import UsageDataError, UsageRepository


SEOUL_TZ = ZoneInfo("Asia/Seoul")


class BikeService:
    def __init__(self, client: SeoulBikeClient, usage_repository: UsageRepository) -> None:
        self.client = client
        self.usage_repository = usage_repository

    async def get_summary(self) -> list[dict]:
        stations = await self.client.get_all_stations()
        available = sum(item.available_bikes for item in stations)
        empty = sum(item.available_bikes == 0 for item in stations)
        average_shared = sum(item.shared for item in stations) / len(stations) if stations else 0

        try:
            usage = self.usage_repository.get_analysis()
            usage_stat = {
                "label": f"{usage.year}년 총 이용",
                "value": f"{usage.total_usage:,}", "unit": "건", "trend": "공식 집계",
            }
            duration_stat = {
                "label": "평균 이용 시간",
                "value": f"{usage.average_minutes:.1f}", "unit": "분", "trend": "공식 집계",
            }
        except UsageDataError:
            usage_stat = {
                "label": "이용정보", "value": "-", "unit": "", "trend": "CSV 필요",
            }
            duration_stat = {
                "label": "평균 거치율", "value": f"{average_shared:.1f}", "unit": "%", "trend": "실시간",
            }

        return [
            usage_stat,
            {"label": "운영 대여소", "value": f"{len(stations):,}", "unit": "개소", "trend": "실시간"},
            {"label": "대여 가능", "value": f"{available:,}", "unit": "대", "trend": f"빈 대여소 {empty:,}곳"},
            duration_stat,
        ]

    async def get_stations(self, limit: int) -> dict:
        stations = await self.client.get_all_stations()
        # 문자열 정렬(102, 1020, 103)이 아닌 대여소명 앞 번호의 숫자 오름차순으로 정렬합니다.
        def station_number(item: RealtimeStation) -> tuple[int, str]:
            matched = re.match(r"^\s*(\d+)", item.name)
            return (int(matched.group(1)) if matched else 999999, item.name)

        visible = sorted(stations, key=station_number)[:limit]
        return {
            "stations": [self._station_card(item) for item in visible],
            "hourlyUsage": [],
            "updatedAt": datetime.now(SEOUL_TZ).isoformat(),
            "source": "서울시 공공자전거 실시간 대여정보 API",
        }

    def get_analysis(self, year: int | None) -> dict:
        result = self.usage_repository.get_analysis(year)
        return {
            "year": result.year,
            "period": result.latest_period,
            "monthlyUsage": result.monthly_usage,
            "topStations": result.top_stations,
            "ageDistribution": result.age_distribution,
            "insights": result.insights,
            "source": "서울시 공공자전거 이용정보(월별) CSV",
            "updatedAt": datetime.now(SEOUL_TZ).isoformat(),
        }

    @staticmethod
    def _station_card(item: RealtimeStation) -> dict:
        if item.available_bikes == 0:
            status = "EMPTY"
        elif item.available_bikes <= 3:
            status = "LOW"
        else:
            status = "GOOD"
        return {
            "id": item.station_id,
            "name": item.name,
            "distance": "-",
            "available": item.available_bikes,
            "total": item.rack_count,
            "status": status,
            "latitude": item.latitude,
            "longitude": item.longitude,
        }
