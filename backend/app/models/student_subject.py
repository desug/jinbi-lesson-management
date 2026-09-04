from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StudentSubject(Base):
    __tablename__ = "student_subjects"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_name", name="uq_student_subjects_student_subject"),
        Index("ix_student_subjects_student_id_subject_name", "student_id", "subject_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    subject_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    total_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    remaining_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    deducted_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student: Mapped["Student"] = relationship(back_populates="subjects")
