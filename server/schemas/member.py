"""회원가입·로그인·회원 응답에 사용하는 Pydantic 스키마."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    nickname: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    passwordConfirm: str = Field(min_length=8, max_length=72)
    ridingStyles: list[str] = Field(default_factory=list, max_length=10)
    agreeRequired: bool
    agreeMarketing: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class MemberResponse(BaseModel):
    id: int
    email: str
    nickname: str
    role: str
    ridingStyles: list[str]
    marketingConsent: bool
    createdAt: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: MemberResponse
