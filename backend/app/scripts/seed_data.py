from __future__ import annotations

import os
import traceback
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash, verify_password
from app.models import Admin, LessonRecord, Student, StudentSubject


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "")
ADMIN_NAME = "系统管理员"

STUDENTS = [{'name': '演示学员01',
  'phone': '19900000001',
  'student_no': 'DEMO001',
  'grade': '初一',
  'avatar': '',
  'class_type': 'VIP',
  'subjects': [{'subject_name': '数学',
                'total_hours': '20.00',
                'remaining_hours': '18.00',
                'deducted_hours': '2.00'}]},
 {'name': '演示学员02',
  'phone': '19900000002',
  'student_no': 'DEMO002',
  'grade': '初一',
  'avatar': '',
  'class_type': '小班',
  'subjects': [{'subject_name': '数学',
                'total_hours': '20.00',
                'remaining_hours': '18.00',
                'deducted_hours': '2.00'}]},
 {'name': '演示学员03',
  'phone': '19900000003',
  'student_no': 'DEMO003',
  'grade': '初一',
  'avatar': '',
  'class_type': '小班',
  'subjects': [{'subject_name': '数学',
                'total_hours': '20.00',
                'remaining_hours': '18.00',
                'deducted_hours': '2.00'}]}]


def to_decimal(value: str) -> Decimal:
    return Decimal(value).quantize(Decimal("0.00"))


def ensure_admin(db: Session) -> Admin:
    admin = db.scalar(select(Admin).where(Admin.username == ADMIN_USERNAME))
    if admin is None:
        admin = Admin(
            username=ADMIN_USERNAME,
            password_hash=get_password_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.add(admin)
        db.flush()
        return admin

    # 保证重复执行后仍然可以使用固定管理员账号和当前默认密码登录。
    admin.role = "admin"
    if hasattr(admin, "name"):
        admin.name = admin.name or ADMIN_NAME

    try:
        password_ok = verify_password(ADMIN_PASSWORD, admin.password_hash)
    except Exception as exc:
        print("seed admin password verify error:", repr(exc))
        traceback.print_exc()
        password_ok = False

    if not password_ok:
        admin.password_hash = get_password_hash(ADMIN_PASSWORD)
    return admin


def ensure_student(db: Session, data: dict[str, object]) -> Student:
    student = db.scalar(select(Student).where(Student.phone == data["phone"]))
    if student is None:
        student = Student(
            name=str(data["name"]),
            phone=str(data["phone"]),
            student_no=str(data["student_no"]),
            grade=str(data.get("grade") or "未分配"),
            avatar=str(data["avatar"]),
            class_type=str(data["class_type"]),
            status="normal",
            is_deleted=False,
            deleted_at=None,
        )
        db.add(student)
        db.flush()
        return student

    # 已存在的 seed 学生只补齐稳定基础字段，不重复创建。
    student.name = str(data["name"])
    student.student_no = str(data["student_no"])
    student.grade = str(data.get("grade") or student.grade or "未分配")
    student.avatar = str(data["avatar"])
    student.class_type = str(data["class_type"])
    student.status = "normal"
    student.is_deleted = False
    student.deleted_at = None
    return student


def ensure_legacy_student_grades(db: Session) -> None:
    students = db.scalars(
        select(Student).where(or_(Student.grade.is_(None), Student.grade == ""))
    ).all()
    for student in students:
        student.grade = "未分配"


def ensure_subject(db: Session, student: Student, data: dict[str, str]) -> StudentSubject:
    total_hours = to_decimal(data["total_hours"])
    remaining_hours = to_decimal(data["remaining_hours"])
    deducted_hours = to_decimal(data["deducted_hours"])
    subject = db.scalar(
        select(StudentSubject).where(
            StudentSubject.student_id == student.id,
            StudentSubject.subject_name == data["subject_name"],
        )
    )
    if subject is not None:
        subject.total_hours = total_hours
        subject.remaining_hours = remaining_hours
        subject.deducted_hours = deducted_hours
        return subject

    subject = StudentSubject(
        student_id=student.id,
        subject_name=data["subject_name"],
        total_hours=total_hours,
        remaining_hours=remaining_hours,
        deducted_hours=deducted_hours,
    )
    db.add(subject)
    db.flush()
    return subject


def sync_seed_subjects(db: Session, student: Student, subject_names: list[str]) -> None:
    expected_names = set(subject_names)
    stale_subjects = db.scalars(
        select(StudentSubject).where(
            StudentSubject.student_id == student.id,
            StudentSubject.subject_name.not_in(expected_names),
        )
    ).all()

    for stale_subject in stale_subjects:
        seed_records = db.scalars(
            select(LessonRecord).where(
                LessonRecord.student_id == student.id,
                LessonRecord.subject_name == stale_subject.subject_name,
                LessonRecord.remark.in_(["seed初始化加课", "seed日常上课扣课"]),
            )
        ).all()
        for record in seed_records:
            db.delete(record)
        db.delete(stale_subject)


def get_seed_lesson_record(
    db: Session,
    student_id: int,
    subject_name: str,
    change_type: str,
    remark: str,
) -> LessonRecord | None:
    return db.scalar(
        select(LessonRecord).where(
            LessonRecord.student_id == student_id,
            LessonRecord.subject_name == subject_name,
            LessonRecord.change_type == change_type,
            LessonRecord.remark == remark,
        )
    )


def ensure_lesson_records(db: Session, student: Student, subject: StudentSubject, index: int) -> None:
    now = datetime.now()
    base_days = 28 - (index % 12)
    add_remark = "seed初始化加课"
    deduct_remark = "seed日常上课扣课"

    add_record = get_seed_lesson_record(db, student.id, subject.subject_name, "add", add_remark)
    if add_record is None:
        add_record = LessonRecord(
            student_id=student.id,
            subject_name=subject.subject_name,
            change_type="add",
            hours=subject.total_hours,
            amount=Decimal("0"),
            remaining_hours=subject.total_hours,
            operator_name=ADMIN_NAME,
            remark=add_remark,
            record_date=now - timedelta(days=base_days),
            created_at=now - timedelta(days=base_days),
        )
        db.add(add_record)
    else:
        add_record.hours = subject.total_hours
        add_record.amount = add_record.amount or Decimal("0")
        add_record.remaining_hours = subject.total_hours
        add_record.record_date = add_record.record_date or add_record.created_at
        add_record.operator_name = ADMIN_NAME

    if subject.deducted_hours > 0:
        deduct_record = get_seed_lesson_record(db, student.id, subject.subject_name, "deduct", deduct_remark)
        if deduct_record is None:
            deduct_record = LessonRecord(
                student_id=student.id,
                subject_name=subject.subject_name,
                change_type="deduct",
                hours=subject.deducted_hours,
                amount=Decimal("0"),
                remaining_hours=subject.remaining_hours,
                operator_name=ADMIN_NAME,
                remark=deduct_remark,
                record_date=now - timedelta(days=max(base_days - 10, 1)),
                created_at=now - timedelta(days=max(base_days - 10, 1)),
            )
            db.add(deduct_record)
        else:
            deduct_record.hours = subject.deducted_hours
            deduct_record.amount = deduct_record.amount or Decimal("0")
            deduct_record.remaining_hours = subject.remaining_hours
            deduct_record.record_date = deduct_record.record_date or deduct_record.created_at
            deduct_record.operator_name = ADMIN_NAME


def seed_data() -> None:
    if not ADMIN_PASSWORD:
        raise RuntimeError("Set SEED_ADMIN_PASSWORD before explicitly seeding a development database")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_admin(db)
        ensure_legacy_student_grades(db)

        record_index = 0
        for student_data in STUDENTS:
            student = ensure_student(db, student_data)
            sync_seed_subjects(
                db,
                student,
                [str(subject_data["subject_name"]) for subject_data in student_data["subjects"]],
            )
            for subject_data in student_data["subjects"]:
                subject = ensure_subject(db, student, subject_data)
                # 课时记录按固定 remark 查重，重复执行不会插入重复记录。
                ensure_lesson_records(db, student, subject, record_index)
                record_index += 1

        db.commit()
        print("初始化数据完成，可重复执行。")
        print("管理员已初始化；密码由 SEED_ADMIN_PASSWORD 提供。")
        print("演示数据已写入；手机号仅为虚构标识，不可拨打。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
