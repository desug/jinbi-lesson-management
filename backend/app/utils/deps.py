from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.schemas.auth import TokenPayload


bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未登录或登录已失效",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    if credentials is None or not credentials.credentials:
        raise _unauthorized_exception()

    try:
        payload = decode_access_token(credentials.credentials)
        return TokenPayload.model_validate(payload)
    except (ValueError, ValidationError) as exc:
        raise _unauthorized_exception() from exc


def get_current_student(
    token_payload: TokenPayload = Depends(get_current_token_payload),
) -> TokenPayload:
    if token_payload.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问",
        )
    return token_payload


def get_current_admin(
    token_payload: TokenPayload = Depends(get_current_token_payload),
) -> TokenPayload:
    if token_payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问",
        )
    return token_payload
