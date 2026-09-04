from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LessonRecord(Base):
    __tablename__ = "lesson_records"
    __table_args__ = (
        Index("ix_lesson_records_student_id_created_at", "student_id", "created_at"),
        Index("ix_lesson_records_student_id_subject_name", "student_id", "subject_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    subject_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0, server_default="0.00")
    remaining_hours: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text(), nullable=True)
    record_date: Mapped[datetime] = mapped_column(
        "recordDate",
        DateTime(),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped["Student"] = relationship(back_populates="lesson_records")
