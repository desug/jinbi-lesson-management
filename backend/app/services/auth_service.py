import traceback

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.models.student import Student
from app.schemas.auth import (
    AdminInfo,
    AdminLoginRequest,
    AdminLoginResponse,
    StudentLoginRequest,
    StudentLoginResponse,
)
from app.services.common import build_student_profile


def _should_check_student_code() -> bool:
    return settings.app_env.strip().lower() in {"dev", "development", "local", "test", "testing"}


def _active_student_filter():
    return or_(Student.is_deleted.is_(False), Student.is_deleted.is_(None))


def student_login(db: Session, payload: StudentLoginRequest) -> StudentLoginResponse:
    if payload.code is not None and _should_check_student_code() and payload.code != "1234":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误，内部测试验证码为 1234",
        )

    student = db.scalar(
        select(Student)
        .options(selectinload(Student.subjects))
        .where(Student.phone == payload.phone, _active_student_filter())
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到对应学员，请检查手机号",
        )

    token = create_access_token(
        subject=str(student.id),
        role="student",
        extra_claims={
            "name": student.name,
            "phone": student.phone,
        },
    )
    return StudentLoginResponse(
        token=token,
        user=build_student_profile(student),
    )


def admin_login(db: Session, payload: AdminLoginRequest) -> AdminLoginResponse:
    print("admin login username:", payload.username)
    admin = db.scalar(select(Admin).where(Admin.username == payload.username))
    print("admin found:", admin is not None)

    if admin is None:
        print("password verified:", False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    try:
        verified = verify_password(payload.password, admin.password_hash)
    except Exception as exc:
        print("admin password verify error:", repr(exc))
        traceback.print_exc()
        verified = False

    print("password verified:", verified)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账号或密码错误",
        )

    try:
        token = create_access_token(
            subject=admin.username,
            role=admin.role,
            extra_claims={
                "user_id": admin.id,
                "user_type": "admin",
                "username": admin.username,
            },
        )
    except RuntimeError as exc:
        print("admin token create error:", repr(exc))
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务端 JWT 配置错误，请检查 JWT_SECRET_KEY 或 SECRET_KEY",
        ) from exc

    return AdminLoginResponse(
        token=token,
        admin=AdminInfo(
            id=admin.id,
            username=admin.username,
            role=admin.role,
        ),
    )
