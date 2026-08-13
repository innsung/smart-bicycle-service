"""기상청 ASOS 시간자료를 내려받아 ML 학습용 날씨 CSV를 생성합니다.

서울 ASOS 지점(108)의 기온·습도·강수량·풍속을 월별로 호출하고
`data/external/weather_hourly.csv`에 저장합니다. 인증키는 `.env`의
KMA_SERVICE_KEY를 읽으며 코드나 출력에 인증키를 노출하지 않습니다.
"""

from __future__ import annotations

import argparse
import calendar
import os
import sys
from pathlib import Path
from urllib.parse import unquote

import httpx
import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import settings  # .env 로드
from ml.config import WEATHER_PATH


ASOS_URL = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"


def _month_end(period: pd.Period) -> str:
    last_day = calendar.monthrange(period.year, period.month)[1]
    return f"{period.year:04d}{period.month:02d}{last_day:02d}"


def download_weather(start_month: str, end_month: str, station_id: str = "108") -> Path:
    service_key = unquote(os.getenv("KMA_SERVICE_KEY", "").strip())
    if not service_key:
        raise RuntimeError(".env에 KMA_SERVICE_KEY를 설정해 주세요.")

    frames: list[pd.DataFrame] = []
    periods = pd.period_range(start=start_month, end=end_month, freq="M")
    with httpx.Client(timeout=60) as client:
        for period in periods:
            params = {
                "serviceKey": service_key,
                "pageNo": 1,
                "numOfRows": 999,
                "dataType": "JSON",
                "dataCd": "ASOS",
                "dateCd": "HR",
                "startDt": period.strftime("%Y%m01"),
                "startHh": "00",
                "endDt": _month_end(period),
                "endHh": "23",
                "stnIds": station_id,
            }
            response = client.get(ASOS_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            header = payload["response"]["header"]
            if header["resultCode"] != "00":
                raise RuntimeError(f"기상청 API 오류: {header['resultCode']} {header['resultMsg']}")
            items = payload["response"]["body"]["items"]["item"]
            frame = pd.DataFrame(items)
            frames.append(pd.DataFrame({
                "datetime": pd.to_datetime(frame["tm"], errors="coerce"),
                "temperature": pd.to_numeric(frame["ta"], errors="coerce"),
                "humidity": pd.to_numeric(frame["hm"], errors="coerce"),
                "rainfall": pd.to_numeric(frame["rn"], errors="coerce").fillna(0),
                "wind_speed": pd.to_numeric(frame["ws"], errors="coerce"),
            }))
            print(f"ASOS {period} 다운로드 완료: {len(frame):,}행")

    weather = pd.concat(frames, ignore_index=True).dropna(subset=["datetime"])
    weather = weather.sort_values("datetime").drop_duplicates("datetime", keep="last")
    WEATHER_PATH.parent.mkdir(parents=True, exist_ok=True)
    weather.to_csv(WEATHER_PATH, index=False, encoding="utf-8-sig")
    print(f"날씨 저장 완료: {len(weather):,}행 → {WEATHER_PATH}")
    return WEATHER_PATH


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-month", required=True, help="시작 월 YYYY-MM")
    parser.add_argument("--end-month", required=True, help="종료 월 YYYY-MM")
    parser.add_argument("--station-id", default="108", help="ASOS 지점 번호(서울 108)")
    args = parser.parse_args()
    download_weather(args.start_month, args.end_month, args.station_id)
