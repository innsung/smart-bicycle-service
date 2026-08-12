"""ML 파이프라인의 경로와 학습 기간을 한 곳에서 관리하는 설정 파일."""

from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parents[1]

HOURLY_USAGE_DIR = SERVER_DIR / "data3"  # 시간대별 이용정보 원본 CSV 폴더
AVAILABILITY_DIR = SERVER_DIR / "data"  # 시간대별 대여 가능 자전거 수 원본 CSV 폴더
EXTERNAL_DIR = SERVER_DIR / "data" / "external"  # 날씨·대여소 마스터 추가 위치
PROCESSED_DIR = SERVER_DIR / "data" / "ml_processed"  # 정제·Feature 결과 저장 위치
ARTIFACT_DIR = SERVER_DIR / "models" / "artifacts"  # 학습 모델·평가지표 저장 위치
EDA_DIR = SERVER_DIR / "reports" / "eda"  # EDA 표·그래프 저장 위치

STATION_MASTER_PATH = EXTERNAL_DIR / "station_master.csv"
WEATHER_PATH = EXTERNAL_DIR / "weather_hourly.csv"
DATASET_PATH = PROCESSED_DIR / "bike_demand_features.csv.gz"
MODEL_PATH = ARTIFACT_DIR / "demand_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"
INFERENCE_FEATURES_PATH = ARTIFACT_DIR / "inference_features.csv"

# 시간순 분리 기준. 랜덤 분리를 사용하지 않아 미래 정보 누수를 막습니다.
TRAIN_END = "2024-12-31 23:00:00"
VALIDATION_END = "2025-06-30 23:00:00"
TEST_END = "2025-12-31 23:00:00"

RANDOM_STATE = 42
