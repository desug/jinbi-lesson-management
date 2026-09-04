from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.lesson_record import LessonRecord
from app.models.student import Student
from app.schemas.auth import TokenPayload
from app.schemas.lesson import LessonRecordResponse
from app.schemas.student import StudentProfileResponse
from app.services.common import build_lesson_record, build_student_profile, parse_token_subject_id


def _active_student_filter():
    return or_(Student.is_deleted.is_(False), Student.is_deleted.is_(None))


def get_student_profile(db: Session, current_student: TokenPayload) -> StudentProfileResponse:
    student_id = parse_token_subject_id(current_student)
    student = db.scalar(
        select(Student)
        .options(selectinload(Student.subjects))
        .where(Student.id == student_id, _active_student_filter())
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效",
        )
    return build_student_profile(student)


def list_student_records(db: Session, current_student: TokenPayload) -> list[LessonRecordResponse]:
    student_id = parse_token_subject_id(current_student)
    student = db.scalar(select(Student.id).where(Student.id == student_id, _active_student_filter()))
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或登录已失效",
        )

    records = db.scalars(
        select(LessonRecord)
        .where(LessonRecord.student_id == student_id)
        .options(selectinload(LessonRecord.student))
        .order_by(LessonRecord.record_date.desc(), LessonRecord.id.desc())
    ).all()
    return [build_lesson_record(record) for record in records]
