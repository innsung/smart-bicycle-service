import api from "../api/axios";

async function login({ email, password }) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

async function signup(payload) {
  // false = 마케팅 미동의(DB 0), true = 마케팅 동의(DB 1)
  const signupPayload = {
    ...payload,
    agreeRequired: Boolean(payload.agreeRequired),
    agreeMarketing: Boolean(payload.agreeMarketing),
  };
  const { data } = await api.post("/auth/signup", signupPayload);
  return data;
}

async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

async function updateMe(payload) {
  const { data } = await api.patch("/auth/me", payload);
  return data;
}

async function deleteMe(password) {
  const { data } = await api.delete("/auth/me", { data: { password } });
  localStorage.removeItem("pedalup_access_token");
  return data;
}

async function socialLoginNotConfigured() {
  throw new Error("소셜 로그인은 OAuth 인증키 설정 후 사용할 수 있습니다.");
}

async function logout() {
  try {
    await api.post("/auth/logout");
  } finally {
    localStorage.removeItem("pedalup_access_token");
  }
}

function clearLocalSession() {
  localStorage.removeItem("pedalup_access_token");
}

const authService = {
  login,
  signup,
  getMe,
  updateMe,
  deleteMe,
  logout,
  clearLocalSession,
  loginWithGoogle: socialLoginNotConfigured,
  loginWithKakao: socialLoginNotConfigured,
};
export default authService;
