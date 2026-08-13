"""PEDALUP AI 챗봇의 메시지·기록·초기화 API."""

from fastapi import APIRouter, HTTPException, Query

from schemas.chat import ChatHistoryMessage, ChatRequest, ChatResponse
from services.chat import ChatServiceUnavailable, ask_chatbot, get_history, is_configured, reset_conversation


router = APIRouter(prefix="/chat", tags=["chatbot"])


@router.get("/status")
def chat_status() -> dict:
    return {"status": "ready" if is_configured() else "configuration_required"}


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        answer, usage = ask_chatbot(payload.session_id, payload.message, payload.temperature)
        return ChatResponse(session_id=payload.session_id, answer=answer, **usage)
    except ChatServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="AI 응답을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.") from exc


@router.get("/history")
def chat_history(session_id: str = Query(min_length=1, max_length=100)) -> dict:
    messages = [ChatHistoryMessage(**item) for item in get_history(session_id)]
    return {"session_id": session_id, "messages": messages}


@router.post("/reset")
def chat_reset(session_id: str = Query(min_length=1, max_length=100)) -> dict:
    reset_conversation(session_id)
    return {"session_id": session_id, "message": "대화 기록이 초기화되었습니다."}
