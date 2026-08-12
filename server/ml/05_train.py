"""[fit: Baseline 비교·모델 학습·평가]

전일 동일 시간 대여량을 Baseline으로 사용하고, 범주형/수치형 전처리와
HistGradientBoostingRegressor를 하나의 Pipeline으로 fit합니다. 평가는 MAE·RMSE로
수행하며 학습과 추론의 전처리가 달라지지 않도록 Pipeline 전체를 저장합니다.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

# 이 파일을 ml 폴더에서 직접 실행해도 `ml` 패키지를 찾도록 server 경로를 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.columns import CATEGORICAL_FEATURES, FEATURE_COLUMNS, NUMERIC_FEATURES
from ml.config import ARTIFACT_DIR, METRICS_PATH, MODEL_PATH, PROCESSED_DIR, RANDOM_STATE


TARGET = "target_rental_count_1h"  # 다음 1시간의 실제 대여 건수를 예측하는 회귀 Target


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),  # 평균적으로 몇 건 틀리는지
        "rmse": round(float(mean_squared_error(y_true, y_pred) ** 0.5), 4),  # 큰 오차에 가중치를 둔 지표
    }


def load_split(name: str) -> pd.DataFrame:
    frame = pd.read_csv(PROCESSED_DIR / f"{name}.csv.gz", low_memory=False)
    return frame.dropna(subset=[TARGET])


def train(metrics_label: str | None = None) -> None:
    train_df = load_split("train")
    validation_df = load_split("validation")
    test_df = load_split("test")
    if train_df.empty or validation_df.empty or test_df.empty:
        raise ValueError("Train/Validation/Test 중 빈 데이터가 있습니다. 기간과 원본 CSV를 확인하세요.")

    # 외부 데이터가 전부 없는 Feature는 모델에서 제외하되 계약 목록 자체는 유지합니다.
    active_numeric = [column for column in NUMERIC_FEATURES if not train_df[column].isna().all()]
    active_features = CATEGORICAL_FEATURES + active_numeric
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    numeric_pipeline = Pipeline([("imputer", SimpleImputer(strategy="median"))])
    preprocessor = ColumnTransformer([
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ("numeric", numeric_pipeline, active_numeric),
    ])
    model = HistGradientBoostingRegressor(
        learning_rate=0.08,
        max_iter=250,
        max_leaf_nodes=31,
        l2_regularization=0.1,
        random_state=RANDOM_STATE,
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(train_df[active_features], train_df[TARGET])  # fit: 과거 Feature와 실제 Target 관계 학습

    baseline_prediction = validation_df["rental_lag_24h"].fillna(validation_df["rental_lag_1h"]).fillna(0)
    validation_prediction = np.maximum(0, pipeline.predict(validation_df[active_features]))
    test_prediction = np.maximum(0, pipeline.predict(test_df[active_features]))
    metrics = {
        "target": TARGET,
        "active_features": active_features,
        "excluded_all_missing_features": [column for column in FEATURE_COLUMNS if column not in active_features],
        "baseline_validation": regression_metrics(validation_df[TARGET], baseline_prediction),
        "model_validation": regression_metrics(validation_df[TARGET], validation_prediction),
        "model_test": regression_metrics(test_df[TARGET], test_prediction),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "feature_columns": active_features, "target": TARGET}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if metrics_label:
        labeled_path = ARTIFACT_DIR / f"metrics_{metrics_label}.json"
        labeled_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"비교 지표 저장 완료 → {labeled_path}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"모델 저장 완료 → {MODEL_PATH}")


if __name__ == "__main__":
    train()
