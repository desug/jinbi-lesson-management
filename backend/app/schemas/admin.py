from decimal import Decimal

from pydantic import Field, field_validator

from app.schemas import CamelModel
from app.schemas.student import StudentProfileResponse, SubjectHours


class AdminBasicInfo(CamelModel):
    id: int
    username: str
    role: str


class LessonChangeResult(CamelModel):
    ok: bool
    message: str
    record_id: int
    subject: SubjectHours


class AdminStudentListResponse(CamelModel):
    items: list[StudentProfileResponse]
    total: int


class GradeSummaryItem(CamelModel):
    grade: str
    student_count: int
    vip_count: int
    small_count: int
    small_vip_count: int = 0
    one_to_two_count: int = 0
    total_remaining_hours: Decimal


class AdminGradeListResponse(CamelModel):
    success: bool = True
    data: list[GradeSummaryItem]
    items: list[GradeSummaryItem]


class AdminCreateStudentRequest(CamelModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)
    total_hours: Decimal = Field(ge=0)
    total_price: Decimal = Field(ge=0)
    grade: str = Field(default="", max_length=50)
    school: str | None = Field(default=None, max_length=100)
    class_type: str | None = Field(default=None, max_length=50)

    @field_validator("name", "phone")
    @classmethod
    def not_blank(cls, value: str) -> str:
        text = (value or "").strip()
        if not text:
            raise ValueError("不能为空")
        return text


class AdminCreateStudentData(CamelModel):
    id: int
    name: str
    phone: str
    student_no: str
    class_type: str
    grade: str
    school: str | None = None
    total_hours: Decimal
    remaining_hours: Decimal
    total_price: Decimal


class AdminCreateStudentResponse(CamelModel):
    success: bool
    message: str
    data: AdminCreateStudentData


class AdminUpgradeStudentGradeRequest(CamelModel):
    target_grade: str = Field(default="", max_length=20)


class AdminUpgradeStudentGradeData(CamelModel):
    id: int
    name: str
    old_grade: str
    new_grade: str


class AdminUpgradeStudentGradeResponse(CamelModel):
    success: bool
    message: str
    data: AdminUpgradeStudentGradeData


class AdminDeleteStudentData(CamelModel):
    id: int
    is_deleted: bool


class AdminDeleteStudentResponse(CamelModel):
    success: bool
    message: str
    data: AdminDeleteStudentData
