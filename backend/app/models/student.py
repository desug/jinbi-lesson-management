from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    student_no: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    grade: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="未分配", server_default="未分配")
    school: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    class_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="VIP", server_default="VIP")
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="normal")
    is_deleted: Mapped[bool] = mapped_column(
        "isDeleted",
        Boolean(),
        index=True,
        nullable=False,
        default=False,
        server_default="0",
    )
    deleted_at: Mapped[datetime | None] = mapped_column("deletedAt", DateTime(), nullable=True)
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

    subjects: Mapped[list["StudentSubject"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    lesson_records: Mapped[list["LessonRecord"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
