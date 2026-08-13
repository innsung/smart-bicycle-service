"""OpenAI 호출을 가짜 응답으로 교체해 세션 기억·초기화와 API 형식을 검증합니다."""

import os


class FakeUsage:
    input_tokens = 12
    output_tokens = 8
    total_tokens = 20


class FakeResponse:
    output_text = "안전모를 착용하고 출발 전 브레이크와 타이어를 확인하세요."
    usage = FakeUsage()


class FakeResponses:
    def __init__(self):
        self.last_input = None

    def create(self, **kwargs):
        self.last_input = kwargs["input"]
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def run() -> None:
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    from fastapi.testclient import TestClient
    from main import app
    from services import chat as chat_service

    fake_client = FakeClient()
    original_get_client = chat_service._get_client
    original_is_configured = chat_service.is_configured
    chat_service._get_client = lambda: fake_client
    chat_service.is_configured = lambda: True

    try:
        with TestClient(app) as client:
            payload = {"session_id": "test-session", "message": "안전 팁 알려줘", "temperature": 0.4}
            response = client.post("/api/chat", json=payload)
            assert response.status_code == 200, response.text
            assert response.json()["answer"].startswith("안전모")
            assert response.json()["total_tokens"] == 20

            history = client.get("/api/chat/history", params={"session_id": "test-session"})
            assert [item["role"] for item in history.json()["messages"]] == ["user", "assistant"]

            reset = client.post("/api/chat/reset", params={"session_id": "test-session"})
            assert reset.status_code == 200
            empty_history = client.get("/api/chat/history", params={"session_id": "test-session"})
            assert empty_history.json()["messages"] == []
    finally:
        chat_service._get_client = original_get_client
        chat_service.is_configured = original_is_configured

    print("chat service test passed")


if __name__ == "__main__":
    run()
