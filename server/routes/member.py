"""강의 프로젝트의 member 라우터 흐름을 적용한 회원 인증 API."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_member_id,
    hash_password,
    verify_password,
)
from database.connection import get_db
from models.member import BikeMember
from schemas.member import AuthResponse, LoginRequest, MemberResponse, SignupRequest


router = APIRouter(tags=["member"])
REFRESH_COOKIE_NAME = "pedalup_refresh_token"


def member_response(member: BikeMember) -> MemberResponse:
    return MemberResponse(
        id=member.member_id,
        email=member.email,
        nickname=member.nickname,
        role=member.role,
        ridingStyles=json.loads(member.riding_styles or "[]"),
        marketingConsent=member.marketing_consent,
        createdAt=member.created_at,
    )


def create_session(member: BikeMember, response: Response) -> AuthResponse:
    access_token = create_access_token(member.member_id, member.role)
    refresh_token = create_refresh_token(member.member_id, member.role)
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/auth",
    )
    return AuthResponse(accessToken=access_token, user=member_response(member))


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    if payload.password != payload.passwordConfirm:
        raise HTTPException(status_code=422, detail="비밀번호 확인이 일치하지 않습니다.")
    if not payload.agreeRequired:
        raise HTTPException(status_code=422, detail="필수 약관에 동의해야 합니다.")
    if db.scalar(select(BikeMember).where(BikeMember.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    if db.scalar(select(BikeMember).where(BikeMember.nickname == payload.nickname.strip())):
        raise HTTPException(status_code=409, detail="이미 사용 중인 닉네임입니다.")

    member = BikeMember(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        nickname=payload.nickname.strip(),
        riding_styles=json.dumps(payload.ridingStyles, ensure_ascii=False),
        # MySQL Boolean(TINYINT(1)): false=0(미동의), true=1(동의)
        marketing_consent=bool(payload.agreeMarketing),
        terms_accepted_at=datetime.now(timezone.utc),
    )
    try:
        db.add(member)
        db.commit()
        db.refresh(member)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="이미 등록된 회원 정보입니다.") from exc
    return create_session(member, response)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    member = db.scalar(select(BikeMember).where(BikeMember.email == payload.email.lower()))
    if member is None or not verify_password(payload.password, member.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    if not member.is_active:
        raise HTTPException(status_code=403, detail="비활성화된 계정입니다.")
    return create_session(member, response)


@router.get("/me", response_model=MemberResponse)
def me(member_id: int = Depends(get_current_member_id), db: Session = Depends(get_db)):
    member = db.get(BikeMember, member_id)
    if member is None or not member.is_active:
        raise HTTPException(status_code=404, detail="회원 정보를 찾을 수 없습니다.")
    return member_response(member)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    response: Response,
    pedalup_refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not pedalup_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh Token이 없습니다.")
    payload = decode_token(pedalup_refresh_token, refresh=True)
    member = db.get(BikeMember, int(payload["sub"]))
    if member is None or not member.is_active:
        raise HTTPException(status_code=401, detail="유효한 회원을 찾을 수 없습니다.")
    return create_session(member, response)


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/api/auth")
    return {"isLogout": True}
