"""날짜에서 주말·공휴일 Feature를 생성하는 보조 파일.

현재는 양력 고정 공휴일만 포함합니다. 설날·추석·대체공휴일은 추후 공식 공휴일
CSV 또는 API를 병합해야 정확히 반영됩니다.
"""

FIXED_HOLIDAYS_MM_DD = {"01-01", "03-01", "05-05", "06-06", "08-15", "10-03", "10-09", "12-25"}


def is_fixed_holiday(datetime_series):
    return datetime_series.dt.strftime("%m-%d").isin(FIXED_HOLIDAYS_MM_DD).astype("int8")
