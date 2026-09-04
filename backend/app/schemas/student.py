from decimal import Decimal

from pydantic import Field

from app.schemas import CamelModel


class SubjectHours(CamelModel):
    subject_name: str
    total_hours: Decimal
    remaining_hours: Decimal
    deducted_hours: Decimal


class StudentBasicInfo(CamelModel):
    id: int
    name: str
    phone: str | None = None
    student_no: str
    grade: str = "未分配"
    school: str | None = None
    avatar: str = ""
    class_type: str


class StudentProfileResponse(StudentBasicInfo):
    total_remaining_hours: Decimal = Decimal("0")
    subjects: list[SubjectHours] = Field(default_factory=list)
