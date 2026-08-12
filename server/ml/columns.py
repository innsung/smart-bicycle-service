"""Feature와 Target 컬럼의 의미를 정의하는 파일.

변수명 옆 주석은 각 컬럼이 모델에서 무엇을 의미하는지 설명합니다.
"""

# 식별 컬럼: 결과 추적에는 사용하지만 날짜 문자열 자체는 모델에 직접 넣지 않습니다.
ID_COLUMNS = [
    "station_id",  # 대여소 고유 번호
    "station_name",  # 화면 표시용 대여소명
    "datetime",  # 관측 기준 날짜와 시간
]

# 범주형 Feature
CATEGORICAL_FEATURES = [
    "station_id",  # 대여소마다 다른 고유 수요 패턴
    "district",  # 대여소가 위치한 자치구/지역
]

# 수치형 Feature
NUMERIC_FEATURES = [
    "year",  # 장기적인 연도별 증가·감소 추세
    "month",  # 계절 패턴을 나타내는 월
    "hour",  # 하루 중 시간대
    "day_of_week",  # 요일 번호: 월요일 0 ~ 일요일 6
    "is_weekend",  # 주말 여부: 주말 1, 평일 0
    "is_holiday",  # 공휴일 여부: 공휴일 1, 아니면 0
    "is_morning_peak",  # 오전 출근 시간대(07~09시) 여부
    "is_evening_peak",  # 오후 퇴근 시간대(17~19시) 여부
    "hour_sin",  # 0시와 23시가 가깝다는 시간 주기성 표현
    "hour_cos",  # 시간 주기성을 보완하는 코사인 값
    "dow_sin",  # 일요일과 월요일이 가깝다는 요일 주기성 표현
    "dow_cos",  # 요일 주기성을 보완하는 코사인 값
    "temperature",  # 예측 시각의 기온(℃)
    "humidity",  # 예측 시각의 습도(%)
    "rainfall",  # 예측 시각의 강수량(mm)
    "is_raining",  # 비가 오는지 여부: 강수량 > 0이면 1
    "wind_speed",  # 예측 시각의 풍속(m/s)
    "rental_lag_1h",  # 같은 대여소의 1시간 전 대여량
    "rental_lag_2h",  # 같은 대여소의 2시간 전 대여량
    "rental_lag_24h",  # 같은 대여소의 전일 동일 시간대 대여량
    "rental_lag_168h",  # 같은 대여소의 전주 동일 요일·시간 대여량
    "rental_rolling_mean_3h",  # 직전 3시간 평균 대여량
    "rental_rolling_mean_24h",  # 직전 24시간 평균 대여량
    "rental_rolling_mean_7d_same_hour",  # 최근 7일 동일 시간대 평균 대여량
    "rental_rolling_std_24h",  # 직전 24시간 대여량 변동성
    "current_available_bikes",  # 해당 시각 대여 가능한 자전거 수
    "available_bikes_lag_1h",  # 1시간 전 대여 가능한 자전거 수
    "available_bikes_change_1h",  # 최근 1시간 자전거 수 증감
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES

TARGET_COLUMNS = [
    "target_rental_count_1h",  # 다음 1시간의 실제 대여 건수: 회귀 Target
]
