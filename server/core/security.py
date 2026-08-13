"""bcrypt 비밀번호 해시와 JWT Access·Refresh Token을 처리합니다."""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from core.config import settings


ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("비밀번호는 UTF-8 기준 72바이트 이하여야 합니다.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(member_id: int, role: str, token_type: str, secret: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(member_id), "role": role, "type": token_type, "iat": now, "exp": now + expires},
        secret,
        algorithm=ALGORITHM,
    )


def create_access_token(member_id: int, role: str) -> str:
    return _create_token(
        member_id, role, "access", settings.access_secret,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(member_id: int, role: str) -> str:
    return _create_token(
        member_id, role, "refresh", settings.refresh_secret,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str, *, refresh: bool = False) -> dict:
    secret = settings.refresh_secret if refresh else settings.access_secret
    expected_type = "refresh" if refresh else "access"
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type or not payload.get("sub"):
            raise JWTError("invalid token type")
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 유효하지 않거나 만료되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_member_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    payload = decode_token(credentials.credentials)
    return int(payload["sub"])
