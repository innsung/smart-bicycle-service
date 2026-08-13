import { createContext, useContext, useState, useCallback } from "react";
import chatbotService from "../services/chatbotService";
import { CHATBOT_MOCK_ANSWERS } from "../constants/mockData";

const ChatbotContext = createContext(null);

const INITIAL_MESSAGES = [
  { id: "welcome", role: "bot", text: CHATBOT_MOCK_ANSWERS.기본, time: "12:43" },
];

export function ChatbotProvider({ children }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [isSending, setIsSending] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((v) => !v), []);

  const reset = useCallback(async () => {
    try {
      await chatbotService.resetChat();
    } finally {
      setMessages(INITIAL_MESSAGES);
    }
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;
    const userMessage = { id: `u-${Date.now()}`, role: "user", text };
    setMessages((prev) => [...prev, userMessage]);
    setIsSending(true);
    try {
      const result = await chatbotService.sendMessage(text);
      setMessages((prev) => [...prev, { id: `b-${Date.now()}`, role: "bot", text: result.answer }]);
    } catch (error) {
      const detail = error.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "bot",
          text: detail || "AI 챗봇에 연결하지 못했습니다. 잠시 후 다시 시도해주세요.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }, []);

  return (
    <ChatbotContext.Provider value={{ isOpen, open, close, toggle, messages, sendMessage, isSending, reset }}>
      {children}
    </ChatbotContext.Provider>
  );
}

export function useChatbot() {
  const ctx = useContext(ChatbotContext);
  if (!ctx) throw new Error("useChatbot must be used within ChatbotProvider");
  return ctx;
}
