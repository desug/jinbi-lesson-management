from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import CamelModel


AiIntent = Literal[
    "subject_hours",
    "all_subjects_summary",
    "class_type",
    "lesson_records",
    "list_by_class_type",
    "low_remaining_hours",
    "total_hours",
    "deducted_hours",
    "unknown",
    "unknown_student",
    "unknown_subject",
]


class AiQueryRequest(CamelModel):
    query: str = Field(min_length=1, max_length=200)


class AiQueryResponse(CamelModel):
    answer: str
    intent: AiIntent | str
    data: dict[str, Any] = Field(default_factory=dict)


class ParsedAiQuery(BaseModel):
    model_config = ConfigDict(extra="ignore")

    intent: AiIntent = "unknown"
    student_name: str = ""
    phone: str = ""
    grade: str = ""
    subject_name: str = ""
    class_type: str = ""
    threshold: Decimal | None = None
