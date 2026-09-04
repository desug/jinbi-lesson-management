from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field, field_validator

from app.schemas import CamelModel
from app.schemas.student import SubjectHours


class LessonRecordResponse(CamelModel):
    id: int
    student_id: int
    student_name: str | None = None
    subject_name: str
    change_type: Literal["add", "deduct"]
    change_type_text: str
    hours: Decimal
    display_hours: str
    amount: Decimal = Decimal("0")
    remaining_hours: Decimal | None = None
    operator_name: str
    remark: str | None = None
    created_at: str
    record_date: str


class AdminLessonRecordsResponse(CamelModel):
    success: bool = True
    data: list[LessonRecordResponse] = Field(default_factory=list)


class LessonChangeRequest(CamelModel):
    student_id: int
    subject_name: str | None = None
    change_type: Literal["add", "deduct"]
    hours: Decimal = Field(gt=0)
    amount: Decimal | None = Field(default=None, ge=0)
    record_date: datetime | None = None
    remark: str | None = None

    @field_validator("change_type", mode="before")
    @classmethod
    def normalize_change_type(cls, value):
        if value in ("增加", "加课", "加课时", "add"):
            return "add"
        if value in ("扣减", "扣课", "扣课时", "deduct"):
            return "deduct"
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value):
        if value in (None, ""):
            return None
        return value

    @field_validator("record_date", mode="before")
    @classmethod
    def parse_record_date(cls, value):
        if value in (None, ""):
            return None
        return value


class LessonChangeResponse(CamelModel):
    success: bool
    ok: bool
    message: str
    record_id: int
    subject: SubjectHours
    record: LessonRecordResponse | None = None
