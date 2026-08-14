#!/bin/sh
set -eu

echo "PEDALUP FastAPI 서버 시작 준비"

if [ ! -f /app/models/artifacts/demand_model.joblib ]; then
  echo "[경고] demand_model.joblib이 없습니다. AI 수요예측 API는 사용할 수 없습니다."
fi

if [ ! -f /app/models/artifacts/inference_features.csv ]; then
  echo "[경고] inference_features.csv가 없습니다. AI 수요예측 API는 사용할 수 없습니다."
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "[경고] OPENAI_API_KEY가 없습니다. 챗봇 API는 503을 반환합니다."
fi

echo "FastAPI를 0.0.0.0:8000에서 시작합니다."
exec uvicorn main:app --host 0.0.0.0 --port 8000
