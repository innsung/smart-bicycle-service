import axios from "axios";

const api = axios.create({
  // 운영(Nginx)은 같은 도메인의 /api, 로컬은 Vite proxy를 사용합니다.
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  withCredentials: true,
  // 최초 실행 시 공식 CSV 집계 캐시 생성 시간이 필요할 수 있습니다.
  timeout: 60000,
});

// 로그인 후 저장된 JWT Access Token을 모든 인증 요청에 자동 첨부합니다.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pedalup_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Access Token이 만료되면 HttpOnly Refresh Token 쿠키로 한 번 재발급합니다.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const isAuthRequest = original?.url?.startsWith("/auth/");
    if (error.response?.status === 401 && !original?._retry && !isAuthRequest) {
      original._retry = true;
      try {
        const { data } = await api.post("/auth/refresh");
        localStorage.setItem("pedalup_access_token", data.accessToken);
        original.headers.Authorization = `Bearer ${data.accessToken}`;
        return api(original);
      } catch {
        localStorage.removeItem("pedalup_access_token");
      }
    }
    return Promise.reject(error);
  }
);

export default api;
