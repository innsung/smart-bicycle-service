"""[전체 실행 오케스트레이터]

아래 순서로 각 단계를 실행합니다.
merge → EDA → Feature Engineering → 시간순 분리 → fit/평가 → 모델 저장

`--sample-files 1`은 코드 검증용이며 여러 연도가 필요한 실제 fit에는 사용하지 않습니다.
"""

import argparse
import importlib
import sys
from pathlib import Path

# 이 파일을 ml 폴더에서 직접 실행해도 `ml` 패키지를 찾도록 server 경로를 추가합니다.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def run(sample_files: int | None = None, skip_train: bool = False, year_month: str | None = None,
        start_month: str | None = None, months: int = 3,
        train_months: int | None = None, test_month: str | None = None) -> None:
    merge = importlib.import_module("ml.01_merge_data")
    eda = importlib.import_module("ml.02_eda")
    features = importlib.import_module("ml.03_feature_engineering")
    split = importlib.import_module("ml.04_split_data")
    train = importlib.import_module("ml.05_train")
    inference_store = importlib.import_module("ml.07_build_inference_store")

    if train_months is not None and test_month:
        test_period = __import__("pandas").Period(test_month, freq="M")
        first_train_month = test_period - train_months
        merge.build_period_dataset(str(first_train_month), train_months + 1)
    elif start_month:
        merge.build_period_dataset(start_month, months)
    elif year_month:
        merge.build_month_dataset(year_month)
    else:
        merge.build_base_dataset(max_files=sample_files)
    eda.run_eda()
    features.build_feature_dataset()
    if train_months is not None and test_month:
        split.save_fixed_test_splits(test_month)
    elif year_month or start_month:
        split.save_month_splits()
    else:
        split.save_splits()
    if not skip_train:
        train.train(f"{train_months}m" if train_months is not None else None)
        inference_store.build_inference_store()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-files", type=int, default=None, help="개발 확인용 최근 N개 원본 파일")
    parser.add_argument("--skip-train", action="store_true", help="병합·EDA·Feature·분리까지만 실행")
    parser.add_argument("--year-month", help="한 달 학습·평가용 YYYY-MM (예: 2025-10)")
    parser.add_argument("--start-month", help="연속 기간 학습 시작 월 YYYY-MM (예: 2025-10)")
    parser.add_argument("--months", type=int, default=3, help="연속 학습 개월 수(기본 3)")
    parser.add_argument("--train-months", type=int, choices=[1, 3, 6], help="고정 Test 비교용 학습 개월 수")
    parser.add_argument("--test-month", help="세 모델이 공통으로 사용할 Test 월 YYYY-MM")
    args = parser.parse_args()
    if args.year_month and args.start_month:
        parser.error("--year-month와 --start-month는 동시에 사용할 수 없습니다.")
    if bool(args.train_months) != bool(args.test_month):
        parser.error("--train-months와 --test-month는 함께 사용해야 합니다.")
    run(args.sample_files, args.skip_train, args.year_month, args.start_month, args.months,
        args.train_months, args.test_month)
