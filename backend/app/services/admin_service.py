from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import case, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.lesson_record import LessonRecord
from app.models.payment import Payment
from app.models.student import Student
from app.models.student_subject import StudentSubject
from app.schemas.admin import (
    AdminCreateStudentData,
    AdminCreateStudentRequest,
    AdminCreateStudentResponse,
    AdminDeleteStudentData,
    AdminDeleteStudentResponse,
    AdminUpgradeStudentGradeData,
    AdminUpgradeStudentGradeRequest,
    AdminUpgradeStudentGradeResponse,
    GradeSummaryItem,
)
from app.schemas.auth import TokenPayload
from app.schemas.lesson import LessonChangeRequest, LessonChangeResponse, LessonRecordResponse
from app.schemas.student import StudentProfileResponse
from app.services.class_types import (
    CLASS_TYPE_ONE_TO_TWO,
    CLASS_TYPE_SMALL,
    CLASS_TYPE_SMALL_VIP,
    CLASS_TYPE_VIP,
    CLASS_TYPES,
    class_type_db_values,
    normalize_class_type,
    normalize_class_type_filter,
)
from app.services.common import (
    build_lesson_record,
    build_student_profile,
    build_subject_hours,
    parse_token_subject_id,
)

DEFAULT_GRADE = "未分配"
DEFAULT_NEW_STUDENT_SUBJECT = "综合"
# 年级顺序用于“升级年级”校验，只允许从低年级升到高年级。
UPGRADE_GRADE_ORDER = [
    "初一",
    "初二",
    "初三",
    "高一",
    "高二",
    "高三",
]
UPGRADE_GRADE_RANK = {grade: index for index, grade in enumerate(UPGRADE_GRADE_ORDER)}
GRADE_ORDER = [
    "一年级",
    "二年级",
    "三年级",
    "四年级",
    "五年级",
    "六年级",
    "初一",
    "初二",
    "初三",
    "高一",
    "高二",
    "高三",
    "未分配",
]
GRADE_RANK = {grade: index for index, grade in enumerate(GRADE_ORDER)}
INSUFFICIENT_HOURS_CODE = "INSUFFICIENT_HOURS"
INSUFFICIENT_HOURS_MESSAGE = "尊敬的学员由于您未按时缴纳课时费，将无法为您提供课时服务"


def _normalize_grade(value: str | None) -> str:
    grade = (value or "").strip()
    return grade or DEFAULT_GRADE


def _active_student_filter():
    # 项目采用软删除，查询学生时都要排除 is_deleted=True 的记录。
    return or_(Student.is_deleted.is_(False), Student.is_deleted.is_(None))


def _to_decimal(value) -> Decimal:
    return Decimal(str(value or "0"))


def _normalize_create_class_type(value: str | None) -> str:
    return "".join(str(value or "").split()).replace("＋", "+")


def _raise_insufficient_hours() -> None:
    # 课时不足不是系统异常，而是明确的业务错误；前端会根据 code 弹出固定提示。
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "success": False,
            "code": INSUFFICIENT_HOURS_CODE,
            "message": INSUFFICIENT_HOURS_MESSAGE,
        },
    )


def _student_remaining_total(student: Student) -> Decimal:
    return sum(
        (subject.remaining_hours or Decimal("0") for subject in student.subjects),
        Decimal("0"),
    )


def _student_order_clause():
    return (
        case(
            (Student.class_type.in_(class_type_db_values(CLASS_TYPE_VIP)), 0),
            (Student.class_type.in_(class_type_db_values(CLASS_TYPE_SMALL)), 1),
            (Student.class_type.in_(class_type_db_values(CLASS_TYPE_SMALL_VIP)), 2),
            (Student.class_type.in_(class_type_db_values(CLASS_TYPE_ONE_TO_TWO)), 3),
            else_=4,
        ).asc(),
        Student.name.asc(),
        Student.id.asc(),
    )


def _generate_student_no(db: Session) -> str:
    # 学号按年份生成，例如 S20260001；如果冲突就递增重试。
    year_prefix = f"S{datetime.now().year}"
    existing_numbers = db.scalars(
        select(Student.student_no).where(Student.student_no.like(f"{year_prefix}%"))
    ).all()

    max_sequence = 0
    for student_no in existing_numbers:
        suffix = str(student_no or "")[len(year_prefix):]
        if suffix.isdigit():
            max_sequence = max(max_sequence, int(suffix))

    for sequence in range(max_sequence + 1, max_sequence + 10000):
        candidate = f"{year_prefix}{sequence:04d}"
        if db.scalar(select(Student.id).where(Student.student_no == candidate)) is None:
            return candidate

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="学号生成失败，请稍后重试",
    )


def create_student(
    db: Session,
    current_admin: TokenPayload,
    payload: AdminCreateStudentRequest,
) -> AdminCreateStudentResponse:
    # parse_token_subject_id 用于确认 token 合法；管理员 token 里通常 user_id 或 sub 可转换为 ID。
    parse_token_subject_id(current_admin)
    operator_name = current_admin.username or current_admin.name or "管理员"
    name = payload.name.strip()
    phone = payload.phone.strip()
    total_hours = _to_decimal(payload.total_hours)
    total_price = _to_decimal(payload.total_price)
    grade = (payload.grade or "").strip()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "请先选择年级后再添加学生",
            },
        )

    school = (payload.school or "").strip() or None
    class_type = _normalize_create_class_type(payload.class_type)
    if not class_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "请选择班型",
            },
        )
    if class_type not in CLASS_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "班型不合法",
            },
        )

    existing_student = db.scalar(select(Student.id).where(Student.phone == phone))
    if existing_student is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已存在，请更换手机号",
        )

    now = datetime.now()

    try:
        # 1. 创建学生主表记录。
        student = Student(
            name=name,
            phone=phone,
            student_no=_generate_student_no(db),
            grade=grade,
            school=school,
            avatar="",
            class_type=class_type,
            status="normal",
            is_deleted=False,
        )
        db.add(student)
        # flush 会先把 student 写入数据库但不提交，这样下面可以拿到 student.id。
        db.flush()

        # 2. 给新学生创建默认科目“综合”，初始总课时和剩余课时相同。
        subject = StudentSubject(
            student_id=student.id,
            subject_name=DEFAULT_NEW_STUDENT_SUBJECT,
            total_hours=total_hours,
            remaining_hours=total_hours,
            deducted_hours=Decimal("0"),
        )
        db.add(subject)

        # 3. 如果新建学生时收了总价，就记录一条缴费记录。
        payment = Payment(
            student_id=student.id,
            amount=total_price,
            pay_type="new_student",
            remark="新建学生初始化付款",
            created_at=now,
        )
        db.add(payment)

        # 4. 同步写入一条“加课时”流水，方便后续查看历史来源。
        record = LessonRecord(
            student_id=student.id,
            subject_name=DEFAULT_NEW_STUDENT_SUBJECT,
            change_type="add",
            hours=total_hours,
            amount=total_price,
            remaining_hours=total_hours,
            operator_name=operator_name,
            remark="新建学生初始化课时",
            record_date=now,
            created_at=now,
        )
        db.add(record)
        # commit 前以上四类数据都在同一个事务里；任何一步失败都会 rollback。
        db.commit()
        db.refresh(student)

        return AdminCreateStudentResponse(
            success=True,
            message="学生添加成功",
            data=AdminCreateStudentData(
                id=student.id,
                name=student.name,
                phone=student.phone,
                student_no=student.student_no,
                class_type=student.class_type,
                grade=student.grade,
                school=student.school,
                total_hours=total_hours,
                remaining_hours=total_hours,
                total_price=total_price,
            ),
        )
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号或学号已存在，请检查后重试",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学生添加失败：{exc}",
        ) from exc


def delete_student(
    db: Session,
    current_admin: TokenPayload,
    student_id: int,
) -> AdminDeleteStudentResponse:
    parse_token_subject_id(current_admin)

    try:
        student = db.scalar(
            select(Student)
            .where(Student.id == student_id, _active_student_filter())
            .with_for_update()
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该学员",
            )

        # 软删除：不真正 delete 行，只打标记，避免历史流水丢失。
        student.is_deleted = True
        student.deleted_at = datetime.now()
        student.status = "deleted"
        db.commit()

        return AdminDeleteStudentResponse(
            success=True,
            message="学生删除成功",
            data=AdminDeleteStudentData(id=student_id, is_deleted=True),
        )
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学生删除失败：{exc}",
        ) from exc


def upgrade_student_grade(
    db: Session,
    current_admin: TokenPayload,
    student_id: int,
    payload: AdminUpgradeStudentGradeRequest,
) -> AdminUpgradeStudentGradeResponse:
    parse_token_subject_id(current_admin)
    target_grade = (payload.target_grade or "").strip()

    if not target_grade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "请选择目标年级",
            },
        )

    if target_grade not in UPGRADE_GRADE_RANK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "目标年级必须高于当前年级",
            },
        )

    try:
        # with_for_update 会锁住当前学生行，避免两个管理员同时升级同一个学生造成并发问题。
        student = db.scalar(select(Student).where(Student.id == student_id).with_for_update())
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该学员",
            )

        if student.is_deleted or student.status == "deleted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已删除学生不能升级",
            )

        old_grade = _normalize_grade(student.grade)
        old_rank = UPGRADE_GRADE_RANK.get(old_grade)
        target_rank = UPGRADE_GRADE_RANK[target_grade]
        if old_rank is not None and target_rank <= old_rank:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "目标年级必须高于当前年级",
                },
            )

        student.grade = target_grade
        db.commit()

        return AdminUpgradeStudentGradeResponse(
            success=True,
            message="学员年级升级成功",
            data=AdminUpgradeStudentGradeData(
                id=student.id,
                name=student.name,
                old_grade=old_grade,
                new_grade=target_grade,
            ),
        )
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"学员年级升级失败：{exc}",
        ) from exc


def list_students(
    db: Session,
    current_admin: TokenPayload,
    keyword: str | None = None,
    class_type: str | None = None,
) -> list[StudentProfileResponse]:
    parse_token_subject_id(current_admin)
    normalized_keyword = (keyword or "").strip()
    normalized_class_type = normalize_class_type_filter(class_type)

    # selectinload 预加载科目，避免循环学生时每个学生再单独查一次科目。
    stmt = select(Student).options(selectinload(Student.subjects)).where(_active_student_filter())

    if normalized_keyword:
        like_keyword = f"%{normalized_keyword}%"
        stmt = stmt.where(
            or_(
                Student.name.like(like_keyword),
                Student.phone.like(like_keyword),
                Student.student_no.like(like_keyword),
            )
        )

    if normalized_class_type and normalized_class_type != "all":
        if normalized_class_type not in CLASS_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="班型参数错误",
            )
        stmt = stmt.where(Student.class_type.in_(class_type_db_values(normalized_class_type)))

    students = db.scalars(stmt.order_by(*_student_order_clause())).all()
    return [build_student_profile(student) for student in students]


def list_grade_summaries(
    db: Session,
    current_admin: TokenPayload,
) -> list[GradeSummaryItem]:
    parse_token_subject_id(current_admin)

    # 年级汇总需要遍历学生和科目余额，所以一次性加载学生及 subjects。
    students = db.scalars(
        select(Student)
        .options(selectinload(Student.subjects))
        .where(_active_student_filter())
        .order_by(Student.id.asc())
    ).all()

    grouped: dict[str, dict[str, Decimal | int | str]] = {}
    for student in students:
        # 按 grade 分组统计人数、班型人数和剩余课时总数。
        grade = _normalize_grade(student.grade)
        item = grouped.setdefault(
            grade,
            {
                "grade": grade,
                "student_count": 0,
                "vip_count": 0,
                "small_count": 0,
                "small_vip_count": 0,
                "one_to_two_count": 0,
                "total_remaining_hours": Decimal("0"),
            },
        )
        item["student_count"] = int(item["student_count"]) + 1
        normalized_student_class_type = normalize_class_type(student.class_type)
        if normalized_student_class_type == CLASS_TYPE_VIP:
            item["vip_count"] = int(item["vip_count"]) + 1
        elif normalized_student_class_type == CLASS_TYPE_SMALL:
            item["small_count"] = int(item["small_count"]) + 1
        elif normalized_student_class_type == CLASS_TYPE_SMALL_VIP:
            item["small_vip_count"] = int(item["small_vip_count"]) + 1
        elif normalized_student_class_type == CLASS_TYPE_ONE_TO_TWO:
            item["one_to_two_count"] = int(item["one_to_two_count"]) + 1
        item["total_remaining_hours"] = Decimal(item["total_remaining_hours"]) + _student_remaining_total(student)

    summaries = [
        GradeSummaryItem(
            grade=str(item["grade"]),
            student_count=int(item["student_count"]),
            vip_count=int(item["vip_count"]),
            small_count=int(item["small_count"]),
            small_vip_count=int(item["small_vip_count"]),
            one_to_two_count=int(item["one_to_two_count"]),
            total_remaining_hours=Decimal(item["total_remaining_hours"]),
        )
        for item in grouped.values()
    ]
    return sorted(
        summaries,
        key=lambda item: (GRADE_RANK.get(item.grade, len(GRADE_RANK)), item.grade),
    )


def list_students_by_grade(
    db: Session,
    current_admin: TokenPayload,
    grade: str,
    keyword: str | None = None,
    class_type: str | None = None,
) -> list[StudentProfileResponse]:
    parse_token_subject_id(current_admin)
    normalized_grade = _normalize_grade(grade)
    normalized_keyword = (keyword or "").strip()
    normalized_class_type = normalize_class_type_filter(class_type)

    # 先限定“未删除学生”，再叠加年级、关键词、班型三个筛选条件。
    stmt = select(Student).options(selectinload(Student.subjects)).where(_active_student_filter())
    if normalized_grade == DEFAULT_GRADE:
        stmt = stmt.where(
            or_(
                Student.grade == normalized_grade,
                Student.grade.is_(None),
                Student.grade == "",
            )
        )
    else:
        stmt = stmt.where(Student.grade == normalized_grade)

    if normalized_keyword:
        like_keyword = f"%{normalized_keyword}%"
        stmt = stmt.where(
            or_(
                Student.name.like(like_keyword),
                Student.phone.like(like_keyword),
                Student.student_no.like(like_keyword),
            )
        )

    if normalized_class_type and normalized_class_type != "all":
        if normalized_class_type not in CLASS_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="班型参数错误",
            )
        stmt = stmt.where(Student.class_type.in_(class_type_db_values(normalized_class_type)))

    students = db.scalars(stmt.order_by(*_student_order_clause())).all()
    return [build_student_profile(student) for student in students]


def get_student_detail(
    db: Session,
    current_admin: TokenPayload,
    student_id: int,
) -> StudentProfileResponse:
    parse_token_subject_id(current_admin)
    # 详情页需要展示科目课时，所以这里也预加载 subjects。
    student = db.scalar(
        select(Student)
        .options(selectinload(Student.subjects))
        .where(Student.id == student_id, _active_student_filter())
    )
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该学员",
        )
    return build_student_profile(student)


def list_student_records_by_admin(
    db: Session,
    current_admin: TokenPayload,
    student_id: int,
) -> list[LessonRecordResponse]:
    parse_token_subject_id(current_admin)
    # 先确认学生存在且未被删除，再查询他的课时流水。
    student = db.scalar(select(Student.id).where(Student.id == student_id, _active_student_filter()))
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该学员",
        )

    records = db.scalars(
        select(LessonRecord)
        .where(LessonRecord.student_id == student_id)
        .options(selectinload(LessonRecord.student))
        .order_by(LessonRecord.record_date.desc(), LessonRecord.id.desc())
    ).all()
    return [build_lesson_record(record) for record in records]


def change_lesson_hours(
    db: Session,
    current_admin: TokenPayload,
    payload: LessonChangeRequest,
) -> LessonChangeResponse:
    parse_token_subject_id(current_admin)
    operator_name = current_admin.username or current_admin.name or "管理员"
    change_hours = _to_decimal(payload.hours)
    subject_name = (payload.subject_name or "").strip() or DEFAULT_NEW_STUDENT_SUBJECT
    amount = _to_decimal(payload.amount)
    record_date = payload.record_date or datetime.now()
    default_remark = "管理员手动加课" if payload.change_type == "add" else "管理员手动扣课"

    try:
        # 锁住学生行，防止两个课时调整请求同时修改同一学生数据。
        student = db.scalar(
            select(Student).where(Student.id == payload.student_id, _active_student_filter()).with_for_update()
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到该学员",
            )

        # 再锁住具体科目行，保证剩余课时计算不会被并发请求打乱。
        subject = db.scalar(
            select(StudentSubject)
            .where(
                StudentSubject.student_id == payload.student_id,
                StudentSubject.subject_name == subject_name,
            )
            .with_for_update()
        )
        if subject is None:
            if payload.change_type == "deduct":
                _raise_insufficient_hours()
            # 加课时允许给学生新增一个原本不存在的科目。
            subject = StudentSubject(
                student_id=payload.student_id,
                subject_name=subject_name,
                total_hours=Decimal("0"),
                remaining_hours=Decimal("0"),
                deducted_hours=Decimal("0"),
            )
            db.add(subject)
            db.flush()

        # 加课时增加总课时和剩余课时；扣课时只减少剩余并累计已扣课时。
        if payload.change_type == "add":
            # 加课：总课时和剩余课时一起增加。
            subject.total_hours = (subject.total_hours or Decimal("0")) + change_hours
            subject.remaining_hours = (subject.remaining_hours or Decimal("0")) + change_hours
            if amount > Decimal("0"):
                # 只有加课并且金额大于 0 时，才新增缴费记录。
                db.add(
                    Payment(
                        student_id=payload.student_id,
                        amount=amount,
                        pay_type="lesson_add",
                        remark=(payload.remark or "").strip() or default_remark,
                        created_at=record_date,
                    )
                )
        else:
            # 扣课：只减少剩余课时，并累计已扣课时。
            current_remaining_hours = subject.remaining_hours or Decimal("0")
            if current_remaining_hours - change_hours < Decimal("0"):
                _raise_insufficient_hours()
            subject.remaining_hours = current_remaining_hours - change_hours
            subject.deducted_hours = (subject.deducted_hours or Decimal("0")) + change_hours

        # 每次加课/扣课都必须写流水，便于学生和管理员回看历史。
        record = LessonRecord(
            student_id=payload.student_id,
            subject_name=subject_name,
            change_type=payload.change_type,
            hours=change_hours,
            amount=amount,
            remaining_hours=subject.remaining_hours,
            operator_name=operator_name,
            remark=(payload.remark or "").strip() or default_remark,
            record_date=record_date,
            created_at=record_date,
        )
        db.add(record)
        db.flush()
        # 科目余额、缴费记录、课时流水在一个事务中提交，保证数据一致。
        db.commit()
        db.refresh(subject)
        db.refresh(record)

        return LessonChangeResponse(
            success=True,
            ok=True,
            message="加课成功" if payload.change_type == "add" else "扣课成功",
            record_id=record.id,
            subject=build_subject_hours(subject),
            record=build_lesson_record(record),
        )
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"课时调整失败：{exc}",
        ) from exc
