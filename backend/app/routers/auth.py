from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import (
    AdminLoginRequest,
    AdminLoginResponse,
    StudentLoginRequest,
    StudentLoginResponse,
)
from app.services.auth_service import admin_login, student_login
from app.utils.deps import get_db


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/student-login", response_model=StudentLoginResponse, summary="学生登录")
def student_login_endpoint(
    payload: StudentLoginRequest,
    db: Session = Depends(get_db),
) -> StudentLoginResponse:
    return student_login(db=db, payload=payload)


@router.post("/admin-login", response_model=AdminLoginResponse, summary="管理员登录")
def admin_login_endpoint(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> AdminLoginResponse:
    return admin_login(db=db, payload=payload)
