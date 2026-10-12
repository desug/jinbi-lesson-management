"""Run only against the explicit local lesson_test database."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.student_subject import StudentSubject
from app.models.lesson_record import LessonRecord
from app.schemas.auth import TokenPayload
from app.schemas.lesson import LessonChangeRequest
from app.services.admin_service import change_lesson_hours

pytestmark = pytest.mark.mysql


def require_mysql(engine):
    if engine is None:
        pytest.skip("JINBI_TEST_DATABASE_URL is not set; MySQL is covered by CI")


def test_migrations_reach_head_and_match_models(mysql_engine):
    require_mysql(mysql_engine)
    inspector = inspect(mysql_engine)
    assert set(Student.__table__.columns.keys()) == {
        column["name"] for column in inspector.get_columns("students")}
    assert set(LessonRecord.__table__.columns.keys()) == {
        column["name"] for column in inspector.get_columns("lesson_records")}
    with mysql_engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "20260503_add_student_school_class_types"


def test_concurrent_deductions_do_not_overdraw(mysql_engine):
    require_mysql(mysql_engine)
    suffix = uuid4().hex[:12]
    with Session(mysql_engine) as session:
        student = Student(name="并发演示学员", phone="TEST-" + suffix, student_no="TEST-" + suffix,
                          grade="初一", class_type="VIP", status="normal", avatar="")
        student.subjects = [StudentSubject(subject_name="数学", total_hours=10,
                                          remaining_hours=10, deducted_hours=0)]
        session.add(student)
        session.commit()
        student_id = student.id
    barrier = Barrier(2)
    def deduct():
        with Session(mysql_engine) as session:
            barrier.wait(timeout=10)
            try:
                change_lesson_hours(session, TokenPayload(sub="1", role="admin"),
                                    LessonChangeRequest(student_id=student_id, subject_name="数学",
                                                        change_type="deduct", hours=6))
                return 200
            except HTTPException as exc:
                return exc.status_code
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda _: deduct(), range(2)))
        assert sorted(outcomes) == [200, 400]
        with Session(mysql_engine) as session:
            subject = session.scalar(select(StudentSubject).where(StudentSubject.student_id == student_id))
            assert subject.remaining_hours == 4
            assert subject.deducted_hours == 6
            assert len(session.scalars(select(LessonRecord).where(LessonRecord.student_id == student_id)).all()) == 1
    finally:
        with Session(mysql_engine) as session:
            session.delete(session.get(Student, student_id))
            session.commit()
