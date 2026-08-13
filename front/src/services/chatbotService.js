import api from "../api/axios";

const SESSION_KEY = "pedalup_chat_session_id";

function getSessionId() {
  let sessionId = sessionStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = globalThis.crypto?.randomUUID?.() ?? `chat-${Date.now()}`;
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}

async function sendMessage(message) {
  const { data } = await api.post("/chat", {
    session_id: getSessionId(),
    message,
    temperature: 0.4,
  });
  return data;
}

async function resetChat() {
  const sessionId = getSessionId();
  await api.post("/chat/reset", null, { params: { session_id: sessionId } });
}

const chatbotService = { sendMessage, resetChat, getSessionId };
export default chatbotService;
