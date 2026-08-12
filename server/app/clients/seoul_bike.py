import asyncio
import time
from dataclasses import dataclass

import httpx

from app.core.config import settings


class SeoulBikeError(RuntimeError):
    pass


@dataclass(frozen=True)
class RealtimeStation:
    station_id: str
    name: str
    rack_count: int
    available_bikes: int
    shared: float
    latitude: float
    longitude: float


class SeoulBikeClient:
    def __init__(self) -> None:
        self._cache: list[RealtimeStation] | None = None
        self._cached_at = 0.0
        self._lock = asyncio.Lock()

    async def get_all_stations(self) -> list[RealtimeStation]:
        if self._cache and time.monotonic() - self._cached_at < settings.realtime_cache_seconds:
            return self._cache

        if not settings.seoul_api_key:
            raise SeoulBikeError(
                "SEOUL_OPEN_DATA_API_KEY가 설정되지 않았습니다. server/.env에 서울 열린데이터광장 인증키를 입력하세요."
            )

        async with self._lock:
            if self._cache and time.monotonic() - self._cached_at < settings.realtime_cache_seconds:
                return self._cache

            first_page, _ = await self._fetch_page(1, 1000)
            stations = list(first_page)
            # API의 list_total_count가 페이지 크기(1000)로 내려오는 경우가 있어
            # 마지막 페이지가 1000개 미만일 때까지 직접 순회합니다.
            start = 1001
            while len(stations) < 5000:
                page, _ = await self._fetch_page(start, start + 999)
                stations.extend(page)
                if len(page) < 1000:
                    break
                start += 1000

            self._cache = stations
            self._cached_at = time.monotonic()
            return stations

    async def _fetch_page(self, start: int, end: int) -> tuple[list[RealtimeStation], int]:
        url = (
            f"{settings.seoul_api_base_url}/{settings.seoul_api_key}"
            f"/json/bikeList/{start}/{end}/"
        )
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise SeoulBikeError(f"서울시 실시간 따릉이 API 호출에 실패했습니다: {exc}") from exc

        result = payload.get("RESULT")
        if result:
            raise SeoulBikeError(result.get("MESSAGE", "서울시 API가 오류를 반환했습니다."))

        body = payload.get("rentBikeStatus")
        if not body:
            raise SeoulBikeError("서울시 API 응답에 rentBikeStatus가 없습니다.")

        rows = [self._parse_station(row) for row in body.get("row", [])]
        return rows, int(body.get("list_total_count", len(rows)))

    @staticmethod
    def _parse_station(row: dict) -> RealtimeStation:
        def as_int(value) -> int:
            try:
                return int(float(value or 0))
            except (TypeError, ValueError):
                return 0

        def as_float(value) -> float:
            try:
                return float(value or 0)
            except (TypeError, ValueError):
                return 0.0

        return RealtimeStation(
            station_id=str(row.get("stationId", "")),
            name=str(row.get("stationName", "")),
            rack_count=as_int(row.get("rackTotCnt")),
            available_bikes=as_int(row.get("parkingBikeTotCnt")),
            shared=as_float(row.get("shared")),
            latitude=as_float(row.get("stationLatitude")),
            longitude=as_float(row.get("stationLongitude")),
        )
