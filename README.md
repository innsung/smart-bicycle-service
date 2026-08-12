# smart-bicycle-service
프로젝트 1

#### 2026-08-11     
- React의 mock JSON 대신 FastAPI API 연동
- 서울시 실시간 API + Data 폴더의 csv 파일로 운영 대여소·대여 가능 자전거등 각종 항목 표시
    - GET /api/bike/seoul/summary → 실시간 API + 이용정보 CSV 둘 다 사용
    - GET /api/bike/seoul/stations → 실시간 API만 사용
    - GET /api/ai/bike/analysis → 이용정보 CSV 또는 생성된 JSON 캐시 사용
- 대여소명 앞 번호 제거(4자리 번호 5571, 2281 등)
- localhost:5174 CORS 문제 해결(서버가 이미 실행중이면 5173이 아니라 5174를 반환)
- 오류 발생 시 프론트에 원인 표시
- JSON 디스크 캐시로 응답시간을 약 34초에서 0.1초로 단축
- app/api/routes/bike.py -> app/services/bike_service.py ->
- api일 경우 : app/api/clients/seoul_bike.py or csv 불러올 경우 : app/api/repositories/usage_repository.py ->
![alt text](<2026-08-11 img.png>)

#### 2026-08-12
- AI 수요예측 화면을 React에 추가
- 초기 mock 예측 로직을 제거하고, 실제 FastAPI ML 예측 API와 연결
  - `POST /api/ai/bike/forecast`

- 서울시 공공자전거 이용정보(시간대별) CSV를 이용한 ML 학습 파이프라인 구축
  - 데이터 병합(merge)
  - EDA
  - Feature Engineering
  - 시간순 Train/Validation/Test 분리
  - 모델 학습 및 MAE·RMSE 평가
  - 추론용 Feature 생성

- 다음 1시간 대여수요 예측 모델 개발
  - 모델: `HistGradientBoostingRegressor`
  - Target: `target_rental_count_1h`
  - 학습 모델: `demand_model.joblib`
  - 최종적으로 최근 3개월 모델 선택

- 주요 Feature 구성
  - 대여소, 지역
  - 연도, 월, 시간, 요일
  - 주말·휴일 여부
  - 출퇴근 시간 여부
  - 기온, 습도, 강수량, 풍속
  - 최근 1시간·2시간 대여량
  - 전일·전주 동일 시간대 대여량
  - 최근 3시간·24시간 평균
  - 최근 7일 동일 시간대 평균
  - 현재 대여 가능 자전거 수 및 증감량

- 모델 목적을 `대여수요 예측 + 자전거 부족 위험도`로 확정
- 사용하지 않는 반납·점유 관련 Feature 및 Target 제거
  - `rack_count`
  - `current_occupancy_ratio`
  - `target_available_bikes_1h`
  - `target_shortage_1h`
  - `target_return_full_1h`

- 자전거 부족 위험도 계산 기능 구현
  - 예상 부족 대수  
    `max(예측 대여수요 - 현재 자전거 수, 0)`
  - 부족 위험도  
    `예측 대여수요 / 현재 자전거 수 × 100`
  - 위험 등급: 낮음·보통·높음·매우 높음
  - 현재 자전거가 0대인 상황 등의 경계값 처리

- 1개월·3개월·6개월 모델 성능 비교
  - 모든 모델의 Test 기간을 `2025년 12월`로 고정
  - 1개월: 2025년 11월 학습
  - 3개월: 2025년 9~11월 학습
  - 6개월: 2025년 6~11월 학습
  - 세 모델의 성능 차이는 작았지만 정확도·범용성·학습 효율을 고려해 3개월 모델 선택
  - 결과 파일
    - `metrics_1m.json`
    - `metrics_3m.json`
    - `metrics_6m.json`

- 기상청 날씨 데이터 연동
  - `.env`의 `KMA_SERVICE_KEY` 사용
  - 과거 학습 데이터: 서울 ASOS 시간자료
  - 실제 예측 데이터: 기상청 단기예보 API
  - 위도·경도를 기상청 격자 `nx`, `ny`로 변환
  - 기온·습도·강수량·풍속 자동 조회
  - 2025년 6~12월 ASOS 날씨 5,136행 생성
  - `weather_hourly.csv`에 저장 후 따릉이 데이터와 시간 기준 병합

- React 입력 방식을 백엔드 자동 조회 방식으로 변경
  - 사용자가 입력하는 값
    - 대여소
    - 예측 날짜
    - 예측 시간
  - 백엔드가 자동으로 조회하는 값
    - 현재 대여 가능 자전거 수
    - 기온·습도·강수량·풍속
    - 최근 1시간 대여량
    - 전일 동일 시간대 대여량
    - 최근 7일 동일 시간대 평균
    - 날짜·요일·출퇴근 시간 Feature

- 추론 응답 속도 개선
  - 대용량 학습 CSV를 API 요청마다 읽지 않도록 추론용 스냅샷 생성
  - `inference_features.csv`
  - 대여소별·시간대별 최신 Feature 66,888행 저장
  - 학습 모델은 최초 요청 시 한 번만 불러오고 메모리에 캐시

- React 수요예측 결과 화면 구현
  - 예측 대여수요
  - 현재 대여 가능 자전거
  - 예상 부족 대수
  - 자전거 부족 위험도
  - 위험 등급
  - 재배치 권장 또는 예상 여유 자전거 안내
  - 예측에 사용된 날씨와 과거 이용 패턴 표시

- 예측 날짜 범위 개선
  - 오늘
  - 내일
  - 2일 후
  - 3일 후
  - 오늘을 선택하면 이미 지난 시간은 시간 목록에서 제외

- 대여소 선택 UI 개선
  - 서울시 실시간 API에서 전체 대여소 2,736개 조회
  - 대여소 앞 번호 기준 숫자 오름차순 정렬
  - 대여소 번호 또는 이름 검색 기능 추가
  - 드롭다운 높이 제한 및 내부 스크롤 적용
  - 각 대여소의 현재 자전거 수 표시
  - 선택된 대여소 체크 표시

- 서울시 실시간 API 전체 페이지 조회 오류 수정
  - 기존에는 첫 1,000개 대여소만 조회
  - 마지막 페이지까지 순차 호출하도록 변경
  - 자전거 0대인 대여소를 목록 앞에 정렬하던 로직 제거

- 서울시 실시간 대여소 ID와 ML 대여소 번호 매핑
  - 실시간 API: `ST-9999`
  - 학습 CSV: `207`
  - 대여소명 앞 번호를 추출해 ML Feature와 연결

- 백엔드 코드 리팩토링
  - 일반 따릉이 조회와 AI 예측 라우터 분리
  - `app/api/routes/bike.py : → 실시간 조회 및 통계 분석`
    - 실시간 요약 : GET /api/bike/seoul/summary
    - 대여소 목록 : GET /api/bike/seoul/stations
    - 이용 분석 : GET /api/ai/bike/analysis
  - `app/api/routes/forecast.py : → ML 모델 기반 미래 수요예측`
    - 예측 요청 처리
    - 대여소 ID 매핑
    - 기상청 날씨 조회
    - 과거 Feature 조회
    - 예측 결과 반환
  - `app/services/demand_forecast_service.py`
    - ML 모델 로딩
    - Feature 구성
    - 수요 예측
    - 부족 위험도 계산

- 최종 예측 처리 구조

  ```text
  React 수요예측 실행
  → POST /api/ai/bike/forecast
  → 서울시 실시간 API에서 대여소·현재 자전거 조회
  → 기상청 단기예보에서 날씨 조회
  → inference_features.csv에서 과거 이용 패턴 조회
  → demand_model.joblib로 다음 1시간 수요 예측
  → 부족 대수·위험도 계산
  → React 결과 박스에 표시

  ```

![alt text](<2026-08-12 img.png>)
