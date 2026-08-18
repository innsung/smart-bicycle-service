"""[데이터 정제·병합]

1. data3의 공공자전거 이용정보(시간대별)를 대여소×날짜×시간으로 집계합니다.
2. data의 대여 가능 자전거 수를 station_id + datetime 기준으로 병합합니다.
3. 선택 데이터인 대여소 마스터와 날씨 CSV가 있으면 함께 병합합니다.

이 파일은 아직 Feature/Target을 만들지 않고, 서로 다른 원천 데이터의 키와 타입을
통일해 하나의 기본 테이블을 만드는 역할만 담당합니다.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# `server/ml`에서 `python 01_merge_data.py`로 직접 실행할 때 server를 import 경로에 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.config import AVAILABILITY_DIR, HOURLY_USAGE_DIR, PROCESSED_DIR, STATION_MASTER_PATH, WEATHER_PATH


def normalise_station_id(series: pd.Series) -> pd.Series:
    """00102, 102, ST-102처럼 다른 대여소 번호 표기를 숫자 문자열로 통일합니다."""
    return series.astype(str).str.extract(r"(\d+)", expand=False).fillna("").str.lstrip("0").replace("", "0")


def clean_station_name(series: pd.Series) -> pd.Series:
    """`2715. 대여소명` 앞의 대여소 번호를 제거합니다."""
    return series.astype(str).str.replace(r"^\s*\d+\s*[.\-_:]?\s*", "", regex=True).str.strip()


def read_csv_flexible(path: Path, **kwargs):
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding, **kwargs)
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"지원하지 않는 CSV 인코딩입니다: {path}")


def detect_csv_encoding(path: Path, required_columns: list[str]) -> str:
    """헤더의 필수 컬럼이 정상 해석되는 인코딩을 선택합니다."""
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            columns = pd.read_csv(path, encoding=encoding, nrows=0).columns
            if set(required_columns).issubset(columns):
                return encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"필수 컬럼을 해석할 수 있는 인코딩이 없습니다: {path}")


def aggregate_hourly_usage(path: Path) -> pd.DataFrame:
    pieces = []
    usecols = ["대여일자", "대여시간", "대여소번호", "대여소명", "이용건수"]
    encoding = detect_csv_encoding(path, usecols)
    for chunk in pd.read_csv(path, encoding=encoding, encoding_errors="replace", usecols=usecols, chunksize=250_000, low_memory=False):
        chunk["station_id"] = normalise_station_id(chunk["대여소번호"])
        chunk["station_name"] = clean_station_name(chunk["대여소명"])
        chunk["date"] = pd.to_datetime(chunk["대여일자"], errors="coerce")
        chunk["hour"] = pd.to_numeric(chunk["대여시간"], errors="coerce")
        chunk["rental_count"] = pd.to_numeric(chunk["이용건수"], errors="coerce").fillna(0)
        chunk = chunk.dropna(subset=["date", "hour"])
        grouped = chunk.groupby(["station_id", "station_name", "date", "hour"], as_index=False)["rental_count"].sum()
        pieces.append(grouped)
    combined = pd.concat(pieces, ignore_index=True)
    combined = combined.groupby(["station_id", "station_name", "date", "hour"], as_index=False)["rental_count"].sum()

    # 원본에는 대여가 0건인 시간이 없으므로 월별 연속 시간축을 만들어 0으로 채웁니다.
    combined["datetime"] = combined["date"] + pd.to_timedelta(combined["hour"], unit="h")
    station_names = combined.sort_values("datetime").drop_duplicates("station_id", keep="last").set_index("station_id")["station_name"]
    # 마지막 관측일의 23시까지만 생성합니다. ceil("D")를 사용하면 다음 달 하루가
    # 인공적인 0건 데이터로 추가되어 Test 성능이 왜곡될 수 있습니다.
    last_hour = combined["datetime"].max().normalize() + pd.Timedelta(hours=23)
    hours = pd.date_range(combined["datetime"].min().floor("D"), last_hour, freq="h")
    complete_index = pd.MultiIndex.from_product([station_names.index, hours], names=["station_id", "datetime"])
    completed = (
        combined.groupby(["station_id", "datetime"])["rental_count"]
        .sum()
        .reindex(complete_index, fill_value=0)
        .rename("rental_count")
        .reset_index()
    )
    completed["station_name"] = completed["station_id"].map(station_names)
    return completed


def aggregate_availability(path: Path) -> pd.DataFrame:
    frame = read_csv_flexible(path, low_memory=False)
    frame["station_id"] = normalise_station_id(frame["대여소번호"])
    frame["date"] = pd.to_datetime(frame["일시"], errors="coerce")
    frame["hour"] = pd.to_numeric(frame["시간대"], errors="coerce")
    frame["current_available_bikes"] = pd.to_numeric(frame["거치대수량"], errors="coerce")
    return frame[["station_id", "date", "hour", "current_available_bikes"]].dropna(subset=["date", "hour"])


def load_optional_station_master() -> pd.DataFrame | None:
    if not STATION_MASTER_PATH.exists():
        return None
    frame = read_csv_flexible(STATION_MASTER_PATH, low_memory=False)
    aliases = {"대여소번호": "station_id", "대여소_ID": "station_id", "자치구": "district"}
    frame = frame.rename(columns={key: value for key, value in aliases.items() if key in frame.columns})
    required = {"station_id", "district"}
    if not required.issubset(frame.columns):
        raise ValueError(f"station_master.csv 필수 컬럼: {sorted(required)}")
    frame["station_id"] = normalise_station_id(frame["station_id"])
    return frame[["station_id", "district"]].drop_duplicates("station_id")


def load_optional_weather() -> pd.DataFrame | None:
    if not WEATHER_PATH.exists():
        return None
    frame = read_csv_flexible(WEATHER_PATH, low_memory=False)
    aliases = {"일시": "datetime", "기온": "temperature", "습도": "humidity", "강수량": "rainfall", "풍속": "wind_speed"}
    frame = frame.rename(columns={key: value for key, value in aliases.items() if key in frame.columns})
    required = {"datetime", "temperature", "humidity", "rainfall", "wind_speed"}
    if not required.issubset(frame.columns):
        raise ValueError(f"weather_hourly.csv 필수 컬럼: {sorted(required)}")
    frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce").dt.floor("h")
    return frame[list(required)].drop_duplicates("datetime")


def merge_source_files(
    usage_files: list[Path],
    availability_files: list[Path],
    completion_label: str,
) -> Path:
    """선택된 기간과 관계없이 동일한 정제·병합·저장 절차를 수행합니다."""
    usage = pd.concat(
        [aggregate_hourly_usage(path) for path in usage_files], ignore_index=True
    )
    usage = usage.groupby(
        ["station_id", "station_name", "datetime"], as_index=False
    )["rental_count"].sum()

    if availability_files:
        availability = pd.concat(
            [aggregate_availability(path) for path in availability_files],
            ignore_index=True,
        )
        availability["datetime"] = availability["date"] + pd.to_timedelta(
            availability["hour"], unit="h"
        )
        availability = (
            availability.drop(columns=["date", "hour"])
            .drop_duplicates(["station_id", "datetime"], keep="last")
        )
        usage = usage.merge(
            availability, on=["station_id", "datetime"], how="left"
        )
    else:
        usage["current_available_bikes"] = pd.NA

    station_master = load_optional_station_master()
    if station_master is not None:
        usage = usage.merge(station_master, on="station_id", how="left")
    else:
        usage["district"] = "미상"

    weather = load_optional_weather()
    if weather is not None:
        usage = usage.merge(weather, on="datetime", how="left")
    else:
        for column in ("temperature", "humidity", "rainfall", "wind_speed"):
            usage[column] = pd.NA

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "bike_hourly_merged.csv.gz"
    usage.sort_values(["station_id", "datetime"]).to_csv(
        output, index=False, compression="gzip"
    )
    print(f"{completion_label}: {len(usage):,}행 → {output}")
    return output


def find_usage_file(period: pd.Period, candidates: list[Path]) -> Path:
    """파일명에서 연월을 찾아 한 달에 해당하는 이용정보 CSV 하나를 반환합니다."""
    digits = period.strftime("%Y%m")
    matched = [
        path
        for path in candidates
        if digits in re.sub(r"\D", "", path.stem)
        or digits[2:] in re.sub(r"\D", "", path.stem)
    ]
    if len(matched) != 1:
        raise FileNotFoundError(
            f"{period} 이용정보 CSV를 정확히 1개 찾지 못했습니다: {matched}"
        )
    return matched[0]


def build_base_dataset(max_files: int | None = None) -> Path:
    usage_files = sorted(HOURLY_USAGE_DIR.glob("*.csv"))
    availability_files = sorted(path for path in AVAILABILITY_DIR.glob("*.csv") if "data_" in path.name or re.match(r"\d{2}\.\d{2}", path.name))
    if max_files:
        usage_files = usage_files[-max_files:]
        availability_files = availability_files[-max_files:]
    if not usage_files:
        raise FileNotFoundError(f"시간대별 이용정보 CSV가 없습니다: {HOURLY_USAGE_DIR}")
    return merge_source_files(usage_files, availability_files, "병합 완료")


def build_month_dataset(year_month: str) -> Path:
    """YYYY-MM에 해당하는 시간대별 이용정보 파일만 선택해 병합합니다."""
    digits = year_month.replace("-", "")
    if not re.fullmatch(r"\d{6}", digits):
        raise ValueError("--year-month는 YYYY-MM 형식이어야 합니다. 예: 2025-10")

    period = pd.Period(year_month, freq="M")
    usage_file = find_usage_file(period, list(HOURLY_USAGE_DIR.glob("*.csv")))
    availability_candidates = [
        path for path in AVAILABILITY_DIR.glob("*.csv")
        if digits[2:] in re.sub(r"\D", "", path.stem)
    ]
    return merge_source_files(
        [usage_file], availability_candidates, f"{year_month} 병합 완료"
    )


def build_period_dataset(start_month: str, months: int) -> Path:
    """시작 월부터 연속된 N개월의 이용정보·대여 가능 정보를 병합합니다."""
    if months < 1:
        raise ValueError("--months는 1 이상이어야 합니다.")
    try:
        periods = pd.period_range(start=pd.Period(start_month, freq="M"), periods=months, freq="M")
    except ValueError as exc:
        raise ValueError("--start-month는 YYYY-MM 형식이어야 합니다. 예: 2025-10") from exc

    usage_files: list[Path] = []
    availability_files: list[Path] = []
    all_usage_files = list(HOURLY_USAGE_DIR.glob("*.csv"))
    all_availability_files = list(AVAILABILITY_DIR.glob("*.csv"))
    for period in periods:
        digits = period.strftime("%Y%m")
        usage_files.append(find_usage_file(period, all_usage_files))
        availability_files.extend(path for path in all_availability_files
                                  if digits[2:] in re.sub(r"\D", "", path.stem))
    return merge_source_files(
        usage_files,
        availability_files,
        f"{periods[0]} ~ {periods[-1]} 병합 완료",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-files", type=int, default=None, help="개발 테스트용 최근 N개 파일만 처리")
    parser.add_argument("--year-month", help="한 달 성능 테스트용 YYYY-MM")
    parser.add_argument("--start-month", help="연속 기간 시작 월 YYYY-MM")
    parser.add_argument("--months", type=int, default=3, help="연속 학습 개월 수(기본 3)")
    args = parser.parse_args()
    if args.start_month:
        build_period_dataset(args.start_month, args.months)
    elif args.year_month:
        build_month_dataset(args.year_month)
    else:
        build_base_dataset(args.max_files)
