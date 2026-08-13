"""기상청 단기예보 API 클라이언트."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import unquote

import httpx

from core.config import settings


SEOUL_TZ = ZoneInfo("Asia/Seoul")
FORECAST_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"


class KmaWeatherError(RuntimeError):
    pass


def latitude_longitude_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
    """기상청 Lambert Conformal Conic 격자(nx, ny)로 변환합니다."""
    re, grid = 6371.00877, 5.0
    slat1, slat2, olon, olat = 30.0, 60.0, 126.0, 38.0
    xo, yo = 43.0, 136.0
    degrad = math.pi / 180.0
    re /= grid
    slat1, slat2, olon, olat = [value * degrad for value in (slat1, slat2, olon, olat)]
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(
        math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    )
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5) ** sn * math.cos(slat1) / sn
    ro = re * sf / math.tan(math.pi * 0.25 + olat * 0.5) ** sn
    ra = re * sf / math.tan(math.pi * 0.25 + latitude * degrad * 0.5) ** sn
    theta = (longitude * degrad - olon) * sn
    return int(ra * math.sin(theta) + xo + 0.5), int(ro - ra * math.cos(theta) + yo + 0.5)


def _latest_base_datetime(now: datetime) -> datetime:
    available = now - timedelta(minutes=15)
    slots = (2, 5, 8, 11, 14, 17, 20, 23)
    candidates = [available.replace(hour=hour, minute=0, second=0, microsecond=0) for hour in slots]
    valid = [candidate for candidate in candidates if candidate <= available]
    return max(valid) if valid else (available - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)


def _parse_precipitation(value: str) -> float:
    value = str(value).strip()
    if value in {"강수없음", "없음", "-"}:
        return 0.0
    if "미만" in value:
        return 0.5
    try:
        return float(value.replace("mm", "").strip())
    except ValueError as exc:
        raise KmaWeatherError(f"강수량 값을 변환할 수 없습니다: {value}") from exc


async def get_hourly_forecast(latitude: float, longitude: float, target: datetime) -> dict:
    if not settings.kma_service_key:
        raise KmaWeatherError(".env에 KMA_SERVICE_KEY가 설정되지 않았습니다.")
    target = target.astimezone(SEOUL_TZ)
    base = _latest_base_datetime(datetime.now(SEOUL_TZ))
    nx, ny = latitude_longitude_to_grid(latitude, longitude)
    params = {
        "serviceKey": unquote(settings.kma_service_key),
        "pageNo": 1, "numOfRows": 1000, "dataType": "JSON",
        "base_date": base.strftime("%Y%m%d"), "base_time": base.strftime("%H%M"),
        "nx": nx, "ny": ny,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(FORECAST_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        header = payload["response"]["header"]
        if header["resultCode"] != "00":
            raise KmaWeatherError(f"기상청 API 오류: {header['resultCode']} {header['resultMsg']}")
        items = payload["response"]["body"]["items"]["item"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise KmaWeatherError(f"기상청 단기예보 호출에 실패했습니다: {exc}") from exc

    date_key, time_key = target.strftime("%Y%m%d"), target.strftime("%H00")
    values = {item["category"]: item["fcstValue"] for item in items
              if item["fcstDate"] == date_key and item["fcstTime"] == time_key}
    required = {"TMP", "REH", "PCP", "WSD"}
    if not required.issubset(values):
        raise KmaWeatherError("선택한 시각은 현재 단기예보 제공 범위 밖입니다.")
    rainfall = _parse_precipitation(values["PCP"])
    return {
        "temperature": float(values["TMP"]), "humidity": float(values["REH"]),
        "rainfall": rainfall, "wind_speed": float(values["WSD"]),
        "is_raining": rainfall > 0, "nx": nx, "ny": ny,
        "forecast_datetime": target.isoformat(), "base_datetime": base.isoformat(),
    }
