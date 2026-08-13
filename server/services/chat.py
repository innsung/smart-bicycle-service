"""강의 챗봇 구조를 적용한 세션별 대화 기억 및 OpenAI 호출 서비스."""

from __future__ import annotations

from threading import RLock

from openai import OpenAI

from core.config import settings


SYSTEM_PROMPT = """당신은 PEDALUP의 자전거 전문 AI 도우미입니다.
한국어로 친절하고 간결하게 답하세요.
따릉이 이용, 자전거 안전, 라이딩 준비와 PEDALUP 화면 사용법을 우선 안내하세요.
현재 따릉이 수량처럼 실시간 확인이 필요한 질문에는 임의의 숫자를 만들지 말고
'대여소 현황' 또는 'AI 수요예측' 화면에서 확인하도록 안내하세요.
요금·정책·법규처럼 변경될 수 있는 정보는 확정적으로 지어내지 말고 공식 기관 확인을 권장하세요.
모르는 내용은 모른다고 답하고, 의료·안전 문제는 전문가 또는 관계기관 확인을 권장하세요."""

MAX_HISTORY_MESSAGES = 20
_conversation_store: dict[str, list[dict[str, str]]] = {}
_store_lock = RLock()


class ChatServiceUnavailable(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(settings.openai_api_key)


def _get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise ChatServiceUnavailable(
            "OPENAI_API_KEY가 설정되지 않았습니다. server/.env에 키를 추가하고 서버를 다시 시작하세요."
        )
    return OpenAI(api_key=settings.openai_api_key)


def _conversation(session_id: str) -> list[dict[str, str]]:
    return _conversation_store.setdefault(session_id, [])


def _trim(messages: list[dict[str, str]]) -> None:
    if len(messages) > MAX_HISTORY_MESSAGES:
        del messages[:-MAX_HISTORY_MESSAGES]


def ask_chatbot(session_id: str, message: str, temperature: float = 0.4) -> tuple[str, dict]:
    """대화 이력을 Responses API에 전달하고 답변과 토큰 사용량을 반환합니다."""
    client = _get_client()
    with _store_lock:
        history = list(_conversation(session_id))
        history.append({"role": "user", "content": message.strip()})
        _trim(history)

    response = client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM_PROMPT,
        input=history,
        temperature=temperature,
        store=False,
    )
    answer = (response.output_text or "").strip()
    if not answer:
        raise RuntimeError("AI 응답 내용이 비어 있습니다.")

    with _store_lock:
        stored = _conversation(session_id)
        stored.extend([
            {"role": "user", "content": message.strip()},
            {"role": "assistant", "content": answer},
        ])
        _trim(stored)

    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "input_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "output_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens))
    return answer, {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def get_history(session_id: str) -> list[dict[str, str]]:
    with _store_lock:
        return list(_conversation_store.get(session_id, []))


def reset_conversation(session_id: str) -> None:
    with _store_lock:
        _conversation_store.pop(session_id, None)
