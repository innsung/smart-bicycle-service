"""bike_member 회원가입·로그인·JWT 인증 흐름을 임시 SQLite DB로 검증합니다."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def run() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database_path = Path(directory) / "member_test.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
        os.environ["ACCESS_SECRET"] = "member-test-access-secret"
        os.environ["REFRESH_SECRET"] = "member-test-refresh-secret"

        from fastapi.testclient import TestClient
        from database.connection import engine
        from main import app
        from database.connection import SessionLocal
        from models.member import BikeMember
        from models.prediction import BikePredictionHistory
        from sqlalchemy import select

        with TestClient(app) as client:
            signup_payload = {
                "nickname": "테스트라이더",
                "email": "rider@example.com",
                "password": "test-password-123",
                "passwordConfirm": "test-password-123",
                "ridingStyles": ["로드", "도심 라이딩"],
                "agreeRequired": True,
                "agreeMarketing": False,
            }
            signup = client.post("/api/auth/signup", json=signup_payload)
            assert signup.status_code == 201, signup.text
            session = signup.json()
            assert session["user"]["email"] == "rider@example.com"
            assert session["user"]["marketingConsent"] is False
            assert session["accessToken"]

            with SessionLocal() as db:
                saved_member = db.scalar(
                    select(BikeMember).where(BikeMember.email == "rider@example.com")
                )
                assert saved_member.marketing_consent is False  # 체크 해제 → DB 0

            consent_payload = {
                **signup_payload,
                "nickname": "마케팅동의라이더",
                "email": "marketing@example.com",
                "agreeMarketing": True,
            }
            consent_signup = client.post("/api/auth/signup", json=consent_payload)
            assert consent_signup.status_code == 201, consent_signup.text
            assert consent_signup.json()["user"]["marketingConsent"] is True

            with SessionLocal() as db:
                consent_member = db.scalar(
                    select(BikeMember).where(BikeMember.email == "marketing@example.com")
                )
                assert consent_member.marketing_consent is True  # 체크 → DB 1

            duplicate = client.post("/api/auth/signup", json=signup_payload)
            assert duplicate.status_code == 409

            failed_login = client.post(
                "/api/auth/login",
                json={"email": "rider@example.com", "password": "wrong-password"},
            )
            assert failed_login.status_code == 401

            login = client.post(
                "/api/auth/login",
                json={"email": "rider@example.com", "password": "test-password-123"},
            )
            assert login.status_code == 200, login.text
            access_token = login.json()["accessToken"]

            me = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert me.status_code == 200
            assert me.json()["nickname"] == "테스트라이더"

            update = client.patch(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "nickname": "수정된라이더",
                    "ridingStyles": ["MTB"],
                    "marketingConsent": True,
                },
            )
            assert update.status_code == 200, update.text
            assert update.json()["nickname"] == "수정된라이더"
            assert update.json()["ridingStyles"] == ["MTB"]
            assert update.json()["marketingConsent"] is True

            with SessionLocal() as db:
                db.add(BikePredictionHistory(
                    member_id=session["user"]["id"],
                    station_id="207",
                    station_name="여의나루역 1번출구",
                    prediction_datetime=datetime.now(timezone.utc),
                    predicted_demand=29,
                    available_bikes=20,
                    shortage_count=9,
                    shortage_risk_percent=100.0,
                    risk_level="매우 높음",
                ))
                db.commit()

            history = client.get(
                "/api/ai/bike/forecast/history",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert history.status_code == 200, history.text
            assert history.json()[0]["station_name"] == "여의나루역 1번출구"

            refresh = client.post("/api/auth/refresh")
            assert refresh.status_code == 200, refresh.text
            assert refresh.json()["accessToken"]

            logout = client.post("/api/auth/logout")
            assert logout.json() == {"isLogout": True}

            delete = client.request(
                "DELETE",
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"password": "test-password-123"},
            )
            assert delete.status_code == 200, delete.text
            assert delete.json() == {"isDeleted": True}

            after_delete = client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            assert after_delete.status_code == 404

        # Windows에서는 SQLite connection pool을 닫아야 임시 DB 파일을 삭제할 수 있습니다.
        engine.dispose()

    print("member auth test passed")


if __name__ == "__main__":
    run()
