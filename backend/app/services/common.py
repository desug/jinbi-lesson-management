from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status

from app.models.admin import Admin
from app.models.lesson_record import LessonRecord
from app.models.student import Student
from app.models.student_subject import StudentSubject
from app.schemas.admin import AdminBasicInfo
from app.schemas.auth import TokenPayload
from app.schemas.lesson import LessonRecordResponse
from app.schemas.student import StudentProfileResponse, SubjectHours


def parse_token_subject_id(token_payload: TokenPayload) -> int:
    """把 JWT 中的 user_id 或 sub 安全转换成主键 ID。"""
    subject_id = token_payload.user_id if token_payload.user_id is not None else token_payload.sub
    try:
        return int(subject_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效",
        ) from exc


def build_subject_hours(subject: StudentSubject) -> SubjectHours:
    return SubjectHours(
        subject_name=subject.subject_name,
        total_hours=subject.total_hours,
        remaining_hours=subject.remaining_hours,
        deducted_hours=subject.deducted_hours,
    )


def build_student_profile(student: Student) -> StudentProfileResponse:
    # 统一在服务层输出前端需要的 camelCase 字段结构。
    ordered_subjects = sorted(student.subjects, key=lambda item: item.id)
    total_remaining_hours = sum(
        (subject.remaining_hours or Decimal("0") for subject in ordered_subjects),
        Decimal("0"),
    )
    return StudentProfileResponse(
        id=student.id,
        name=student.name,
        phone=student.phone,
        student_no=student.student_no,
        grade=student.grade or "未分配",
        school=student.school,
        avatar=student.avatar or "",
        class_type=student.class_type,
        total_remaining_hours=total_remaining_hours,
        subjects=[build_subject_hours(subject) for subject in ordered_subjects],
    )


def format_datetime(value) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def build_lesson_record(record: LessonRecord) -> LessonRecordResponse:
    # 对外统一使用 recordDate；createdAt 保留给旧前端，值与 recordDate 保持一致。
    record_datetime = record.record_date or record.created_at
    record_date = format_datetime(record_datetime)
    raw_change_type = (record.change_type or "").strip()
    change_type = "add" if raw_change_type in {"add", "增加", "加课时"} else "deduct"
    hours = record.hours or Decimal("0")
    remaining_hours = record.remaining_hours if record.remaining_hours is not None else Decimal("0")
    remark = (record.remark or "").strip() or "-"
    return LessonRecordResponse(
        id=record.id,
        student_id=record.student_id,
        student_name=record.student.name if getattr(record, "student", None) is not None else None,
        subject_name=record.subject_name,
        change_type=change_type,
        change_type_text="加课时" if change_type == "add" else "扣课时",
        hours=hours,
        display_hours=("+" if change_type == "add" else "-") + str(int(hours) if hours == hours.to_integral_value() else hours),
        amount=record.amount or Decimal("0"),
        remaining_hours=remaining_hours,
        operator_name=record.operator_name,
        remark=remark,
        created_at=record_date,
        record_date=record_date,
    )


def build_admin_basic(admin: Admin) -> AdminBasicInfo:
    return AdminBasicInfo(
        id=admin.id,
        username=admin.username,
        role=admin.role,
    )
