import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  // 최초 실행 시 공식 CSV 집계 캐시 생성 시간이 필요할 수 있습니다.
  timeout: 60000,
});

// 향후 FastAPI JWT 인증 연동 지점 — localStorage에 저장된 accessToken을 자동 첨부
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pedalup_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
