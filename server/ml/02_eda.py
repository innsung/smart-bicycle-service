"""[EDA: 탐색적 데이터 분석]

병합 데이터의 기간, 결측률, 대여량 분포, 시간·요일별 패턴과 상위 대여소를 계산해
reports/eda에 CSV·JSON으로 저장합니다. 모델 학습 전에 데이터 품질을 점검하는 단계입니다.
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# 이 파일을 ml 폴더에서 직접 실행해도 `ml` 패키지를 찾도록 server 경로를 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.config import EDA_DIR, PROCESSED_DIR


def run_eda() -> None:
    source = PROCESSED_DIR / "bike_hourly_merged.csv.gz"
    df = pd.read_csv(source, parse_dates=["datetime"])
    EDA_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "row_count": int(len(df)),
        "station_count": int(df["station_id"].nunique()),
        "start_datetime": str(df["datetime"].min()),
        "end_datetime": str(df["datetime"].max()),
        "duplicate_keys": int(df.duplicated(["station_id", "datetime"]).sum()),
        "missing_rate_percent": {column: round(float(value), 2) for column, value in (df.isna().mean() * 100).items()},
        "rental_count_statistics": df["rental_count"].describe().round(2).to_dict(),
    }
    (EDA_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.dayofweek
    df.groupby("hour", as_index=False)["rental_count"].mean().to_csv(EDA_DIR / "hourly_pattern.csv", index=False)
    df.groupby("day_of_week", as_index=False)["rental_count"].mean().to_csv(EDA_DIR / "weekday_pattern.csv", index=False)
    df.groupby(["station_id", "station_name"], as_index=False)["rental_count"].sum().nlargest(20, "rental_count").to_csv(EDA_DIR / "top_stations.csv", index=False)

    sns.set_theme(style="whitegrid")
    hourly = df.groupby("hour", as_index=False)["rental_count"].mean()
    ax = sns.lineplot(data=hourly, x="hour", y="rental_count", marker="o")
    ax.set(title="Average rental demand by hour", xlabel="Hour", ylabel="Average rentals")
    plt.tight_layout()
    plt.savefig(EDA_DIR / "hourly_demand.png", dpi=160)
    plt.close()
    print(f"EDA 완료 → {EDA_DIR}")


if __name__ == "__main__":
    run_eda()
