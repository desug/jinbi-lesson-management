from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import TokenPayload
from app.schemas.lesson import LessonRecordResponse
from app.schemas.student import StudentProfileResponse
from app.services.student_service import get_student_profile, list_student_records
from app.utils.deps import get_current_student, get_db


router = APIRouter(prefix="/student", tags=["student"])


@router.get("/profile", response_model=StudentProfileResponse, summary="获取学生个人信息")
def student_profile_endpoint(
    current_student: TokenPayload = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    return get_student_profile(db=db, current_student=current_student)


@router.get("/records", response_model=list[LessonRecordResponse], summary="获取学生课时记录")
def student_records_endpoint(
    current_student: TokenPayload = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> list[LessonRecordResponse]:
    return list_student_records(db=db, current_student=current_student)
