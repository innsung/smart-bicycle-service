# 따릉이 수요·혼잡도 ML 파이프라인

## 파일별 역할

1. `01_merge_data.py`: 시간대별 이용정보, 재고, 날씨, 대여소 마스터 정제·병합
2. `02_eda.py`: 결측률·분포·시간 및 요일 패턴 EDA
3. `03_feature_engineering.py`: 시간/Lag/Rolling Feature와 다음 1시간 Target 생성
4. `04_split_data.py`: Train/Validation/Test 시간순 분리
5. `05_train.py`: Baseline 비교, 전처리 Pipeline, fit, MAE/RMSE 평가 및 저장
6. `07_build_inference_store.py`: API가 빠르게 조회할 대여소·시간별 Feature 스냅샷 생성
7. `run_pipeline.py`: 위 단계를 순서대로 실행

각 Feature와 Target 변수의 전체 의미는 `columns.py`에 주석으로 작성되어 있습니다.

## 원본 데이터

- `server/data3/*.csv`: 공공자전거 이용정보(시간대별)
- `server/data/*.csv`: 대여소별 1시간 단위 대여 가능 자전거 수
- `server/data/external/station_master.csv`: 선택이지만 혼잡도 계산에 필수
- `server/data/external/weather_hourly.csv`: 날씨 Feature를 사용하려면 필요

### station_master.csv 필수 컬럼

```csv
station_id,district
102,마포구,20
```

한글 별칭 `대여소번호,자치구,거치대수`도 지원합니다.

### weather_hourly.csv 필수 컬럼

```csv
datetime,temperature,humidity,rainfall,wind_speed
2025-01-01 00:00:00,-2.1,61,0,2.4
```

한글 별칭 `일시,기온,습도,강수량,풍속`도 지원합니다.

## 실행

먼저 코드와 1개월 데이터 흐름만 확인합니다.

```powershell
cd server
.\.venv\Scripts\python.exe -m ml.run_pipeline --sample-files 1 --skip-train
```

전체 데이터 학습:

```powershell
.\.venv\Scripts\python.exe -m ml.run_pipeline
```

한 달 단위 성능 테스트:

```powershell
.\.venv\Scripts\python.exe -m ml.run_pipeline --year-month 2025-10
```

결과 지표는 `models/artifacts/metrics.json`, 모델은
`models/artifacts/demand_model.joblib`에 저장됩니다.

전체 데이터는 수천만 행이 될 수 있으므로 충분한 디스크와 메모리를 확인한 뒤 실행합니다.
운영용으로는 다음 단계에서 CSV 대신 연도·월별 Parquet 파티션과 zero-demand downsampling을
적용하는 것을 권장합니다.

## 시간순 분리

- Train: 2022-01-01 ~ 2024-12-31
- Validation: 2025-01-01 ~ 2025-06-30
- Test: 2025-07-01 ~ 2025-12-31
- 2026년: 최종 최신 추론 또는 별도 검증

## 주의

- 현재 공휴일 코드는 양력 고정 공휴일만 포함합니다.
- 설날·추석·대체공휴일은 공식 공휴일 데이터를 추가해야 합니다.
- `data`의 `거치대수량`은 현재 대여 가능 자전거 수이며 대여소 전체 정원이 아닙니다.
- 반납 가능 여부와 거치대 점유율은 서비스 범위에서 제외했습니다.
## 동일 Test 월로 1·3·6개월 모델 비교

과거 날씨를 먼저 내려받습니다(서울 ASOS 108):

```powershell
python -m ml.00_download_weather --start-month 2025-06 --end-month 2025-12
```

2025년 12월을 동일한 Test로 고정하고 학습 기간만 바꿉니다:

```powershell
python -m ml.run_pipeline --train-months 1 --test-month 2025-12
python -m ml.run_pipeline --train-months 3 --test-month 2025-12
python -m ml.run_pipeline --train-months 6 --test-month 2025-12
```

각 결과는 `models/artifacts/metrics_1m.json`, `metrics_3m.json`,
`metrics_6m.json`으로 자동 저장됩니다. 모델 Target은 다음 1시간 대여수요이며,
부족 위험도는 예측 수요와 실시간 대여 가능 자전거 수를 비교해 계산합니다.
