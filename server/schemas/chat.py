"""PEDALUP AI 챗봇 요청·응답 스키마."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatHistoryMessage(BaseModel):
    role: str
    content: str
