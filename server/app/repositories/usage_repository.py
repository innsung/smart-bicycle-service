from __future__ import annotations

import json
import re
import threading
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.config import settings


_CACHE_LOCK = threading.Lock()


class UsageDataError(RuntimeError):
    pass


ALIASES = {
    "period": ["RENT_NM", "대여일자", "대여일시", "대여년월", "년월", "일시"],
    "station_id": ["STATION_NO", "대여소번호"],
    "station_name": ["STATION_NAME", "대여소명", "대여소"],
    "age": ["AGE_TYPE", "연령", "연령대", "연령대코드"],
    "use_count": ["USE_CNT", "건수", "이용건수", "대여건수"],
    "move_time": ["MOVE_TIME", "이용시간", "이용시간(분)", "이동시간"],
}


@dataclass(frozen=True)
class UsageAnalysis:
    year: int
    latest_period: str
    total_usage: int
    average_minutes: float
    monthly_usage: list[dict]
    top_stations: list[dict]
    age_distribution: list[dict]
    insights: list[dict]


class UsageRepository:
    """공식 '공공자전거 이용정보(월별)' CSV를 청크 단위로 집계한다."""

    def get_analysis(self, year: int | None = None) -> UsageAnalysis:
        files = tuple(sorted(settings.usage_data_dir.glob("*.csv")))
        if not files:
            raise UsageDataError(
                f"이용정보 CSV가 없습니다. 서울시 '공공자전거 이용정보(월별)' CSV를 "
                f"{settings.usage_data_dir} 폴더에 넣으세요."
            )
        signature = _files_signature(files)
        cache_path = _cache_path(year)

        # summary와 analysis가 동시에 최초 호출되어 CSV를 중복 집계하지 않도록 한다.
        with _CACHE_LOCK:
            cached = _read_disk_cache(cache_path, signature)
            if cached is not None:
                return cached

            result = self._aggregate(files, year)
            _write_disk_cache(cache_path, signature, result)
            return result

    @staticmethod
    @lru_cache(maxsize=8)
    def _aggregate(files: tuple[Path, ...], requested_year: int | None) -> UsageAnalysis:
        monthly: dict[str, int] = {}
        station_by_year: dict[str, dict[str, int]] = {}
        age_by_year: dict[str, dict[str, int]] = {}
        total_move_time_by_year: dict[str, float] = {}
        time_weight_by_year: dict[str, int] = {}

        for path in files:
            for chunk in _read_csv_chunks(path):
                columns = _resolve_columns(chunk.columns)
                required = {"period", "use_count"}
                if not required.issubset(columns):
                    raise UsageDataError(
                        f"{path.name}에 필수 컬럼이 없습니다: period/RENT_NM, use_count/USE_CNT"
                    )

                period = _normalise_period(chunk[columns["period"]])
                counts = pd.to_numeric(chunk[columns["use_count"]], errors="coerce").fillna(0)
                valid = period.notna()
                if requested_year is not None:
                    valid &= period.str[:4].eq(str(requested_year))
                if not valid.any():
                    continue

                frame = chunk.loc[valid].copy()
                frame["_period"] = period.loc[valid]
                frame["_count"] = counts.loc[valid]
                frame["_year"] = frame["_period"].str[:4]
                for key, value in frame.groupby("_period")["_count"].sum().items():
                    monthly[key] = monthly.get(key, 0) + int(value)

                if "station_name" in columns:
                    grouped = frame.groupby(["_year", columns["station_name"]])["_count"].sum()
                    for (year_key, key), value in grouped.items():
                        totals = station_by_year.setdefault(str(year_key), {})
                        name = _clean_station_name(key)
                        totals[name] = totals.get(name, 0) + int(value)

                if "age" in columns:
                    grouped = frame.groupby(["_year", columns["age"]])["_count"].sum()
                    for (year_key, key), value in grouped.items():
                        totals = age_by_year.setdefault(str(year_key), {})
                        age = _clean_text_value(key) or "미상"
                        totals[age] = totals.get(age, 0) + int(value)

                if "move_time" in columns:
                    times = pd.to_numeric(frame[columns["move_time"]], errors="coerce")
                    usable = times.notna() & times.ge(0) & frame["_count"].gt(0)
                    for year_key, year_frame in frame.loc[usable].groupby("_year"):
                        indexes = year_frame.index
                        key = str(year_key)
                        total_move_time_by_year[key] = total_move_time_by_year.get(key, 0.0) + float(
                            times.loc[indexes].sum()
                        )
                        time_weight_by_year[key] = time_weight_by_year.get(key, 0) + int(
                            year_frame["_count"].sum()
                        )

        if not monthly:
            suffix = f" {requested_year}년" if requested_year else ""
            raise UsageDataError(f"이용정보 CSV에서{suffix} 데이터를 찾지 못했습니다.")

        selected_year = requested_year or max(int(key[:4]) for key in monthly)
        year_key = str(selected_year)
        selected_monthly = {k: v for k, v in monthly.items() if k.startswith(str(selected_year))}
        station_totals = station_by_year.get(year_key, {})
        age_totals = age_by_year.get(year_key, {})
        total_move_time = total_move_time_by_year.get(year_key, 0.0)
        time_weight = time_weight_by_year.get(year_key, 0)
        total_usage = sum(selected_monthly.values())
        age_sum = sum(age_totals.values()) or 1
        month_rows = [
            {"month": f"{int(key[4:6])}월", "count": value}
            for key, value in sorted(selected_monthly.items())
        ]
        top_rows = [
            {"name": name, "count": count}
            for name, count in sorted(station_totals.items(), key=lambda item: item[1], reverse=True)[:6]
        ]
        age_rows = [
            {"age": age, "percent": round(count * 100 / age_sum, 1)}
            for age, count in sorted(age_totals.items(), key=lambda item: item[1], reverse=True)
        ]
        average_minutes = round(total_move_time / time_weight, 1) if time_weight else 0.0

        return UsageAnalysis(
            year=selected_year,
            latest_period=max(selected_monthly),
            total_usage=total_usage,
            average_minutes=average_minutes,
            monthly_usage=month_rows,
            top_stations=top_rows,
            age_distribution=age_rows,
            insights=_build_insights(month_rows, top_rows, age_rows),
        )


def _read_csv_chunks(path: Path):
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "cp949", "utf-8"):
        try:
            yield from pd.read_csv(path, encoding=encoding, chunksize=200_000, low_memory=False)
            return
        except UnicodeDecodeError as exc:
            last_error = exc
    raise UsageDataError(f"{path.name} 인코딩을 읽을 수 없습니다: {last_error}")


def _resolve_columns(columns) -> dict[str, str]:
    lookup = {_normalise_column_name(column): str(column) for column in columns}
    resolved = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lookup:
                resolved[canonical] = lookup[alias]
                break
    return resolved


def _normalise_column_name(column) -> str:
    """연도별 원본 파일에 섞여 있는 BOM·공백·작은따옴표를 제거한다."""
    return str(column).lstrip("\ufeff").strip().strip("'\"").strip()


def _clean_text_value(value) -> str:
    return str(value).strip().strip("'\"").strip()


def _clean_station_name(value) -> str:
    """대여소명 앞에 붙은 `2715.`, `5515 ` 같은 대여소 번호를 제거한다."""
    original = _clean_text_value(value)
    cleaned = re.sub(r"^\d+\s*(?:[.\-_:]\s*)?", "", original).strip()
    return cleaned or original


def _files_signature(files: tuple[Path, ...]) -> list[dict]:
    return [
        {
            "name": path.name,
            "size": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
        }
        for path in files
    ]


def _cache_path(year: int | None) -> Path:
    cache_dir = settings.usage_data_dir.parent / "processed"
    suffix = str(year) if year is not None else "latest"
    return cache_dir / f"usage_analysis_{suffix}.json"


def _read_disk_cache(cache_path: Path, signature: list[dict]) -> UsageAnalysis | None:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        if payload.get("source_signature") != signature:
            return None
        return UsageAnalysis(**payload["analysis"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None


def _write_disk_cache(
    cache_path: Path, signature: list[dict], result: UsageAnalysis
) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = cache_path.with_suffix(".tmp")
    payload = {"source_signature": signature, "analysis": asdict(result)}
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temporary_path.replace(cache_path)


def _normalise_period(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.replace(r"[^0-9]", "", regex=True)
    return text.where(text.str.len().ge(6)).str[:6]


def _build_insights(months: list[dict], stations: list[dict], ages: list[dict]) -> list[dict]:
    insights = []
    if len(months) >= 2 and months[-2]["count"]:
        change = (months[-1]["count"] - months[-2]["count"]) / months[-2]["count"] * 100
        insights.append({
            "tag": "월간 추이",
            "icon": "TrendingUp" if change >= 0 else "Activity",
            "title": f"최근 월 이용량이 전월보다 {abs(change):.1f}% {'증가' if change >= 0 else '감소'}",
            "description": "서울시 공공자전거 이용정보의 실제 이용건수를 월별로 비교한 결과입니다.",
            "metricLabel": "전월 대비",
            "metricValue": f"{change:+.1f}%",
            "tone": "up" if change >= 0 else "down",
        })
    if stations:
        insights.append({
            "tag": "인기 대여소", "icon": "MapPin",
            "title": f"이용량 1위는 {stations[0]['name']}",
            "description": "선택 기간의 대여소별 이용건수를 합산한 결과입니다.",
            "metricLabel": "이용건수", "metricValue": f"{stations[0]['count']:,}건", "tone": "up",
        })
    if ages:
        insights.append({
            "tag": "이용자", "icon": "Users",
            "title": f"가장 높은 이용 비중은 {ages[0]['age']}",
            "description": "미상 값을 포함한 연령대별 실제 이용건수 비율입니다.",
            "metricLabel": "이용 비율", "metricValue": f"{ages[0]['percent']:.1f}%", "tone": "neutral",
        })
    return insights
