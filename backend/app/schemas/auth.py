from pydantic import Field

from app.schemas import CamelModel
from app.schemas.student import StudentProfileResponse


class StudentLoginRequest(CamelModel):
    phone: str = Field(min_length=11, max_length=20)
    code: str | None = Field(default=None, max_length=20)


class AdminLoginRequest(CamelModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class TokenPayload(CamelModel):
    sub: str
    role: str
    exp: int | None = None
    user_id: int | None = None
    user_type: str | None = None
    username: str | None = None
    name: str | None = None
    phone: str | None = None


class TokenResponse(CamelModel):
    token: str


class StudentLoginResponse(TokenResponse):
    user: StudentProfileResponse


class AdminInfo(CamelModel):
    id: int
    username: str
    role: str


class AdminLoginResponse(TokenResponse):
    admin: AdminInfo
