from __future__ import annotations

import traceback

from sqlalchemy import text

from app.core.database import engine


def column_exists(conn, table_name: str, column_name: str) -> bool:
    count = conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"table_name": table_name, "column_name": column_name},
    ).scalar_one()
    return int(count) > 0


def index_exists(conn, table_name: str, index_name: str) -> bool:
    count = conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
              AND INDEX_NAME = :index_name
            """
        ),
        {"table_name": table_name, "index_name": index_name},
    ).scalar_one()
    return int(count) > 0


def ensure_column(conn, table_name: str, column_name: str, ddl: str) -> None:
    if column_exists(conn, table_name, column_name):
        print(f"[skip] {table_name}.{column_name} already exists")
        return

    print(f"[add] {table_name}.{column_name}")
    conn.execute(text(ddl))


def ensure_index(conn, table_name: str, index_name: str, ddl: str) -> None:
    if index_exists(conn, table_name, index_name):
        print(f"[skip] {table_name}.{index_name} already exists")
        return

    print(f"[add] {table_name}.{index_name}")
    conn.execute(text(ddl))


def backfill_lesson_record_legacy_columns(conn) -> None:
    if column_exists(conn, "lesson_records", "subjectName"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET subject_name = COALESCE(NULLIF(subject_name, ''), subjectName, '综合')"
            )
        )
        print("[ok] lesson_records.subject_name backfilled from subjectName")

    if column_exists(conn, "lesson_records", "type"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET change_type = CASE WHEN `type` IN ('add', '增加', '加课时') THEN 'add' ELSE 'deduct' END "
                "WHERE `type` IS NOT NULL AND `type` <> ''"
            )
        )
        print("[ok] lesson_records.change_type backfilled from type")

    if column_exists(conn, "lesson_records", "action"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET change_type = CASE WHEN action IN ('add', '增加', '加课时') THEN 'add' ELSE 'deduct' END "
                "WHERE action IS NOT NULL AND action <> ''"
            )
        )
        print("[ok] lesson_records.change_type backfilled from action")

    if column_exists(conn, "lesson_records", "changeHours"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET hours = changeHours "
                "WHERE changeHours IS NOT NULL AND (hours IS NULL OR hours = 0)"
            )
        )
        print("[ok] lesson_records.hours backfilled from changeHours")

    if column_exists(conn, "lesson_records", "remainingHours"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET remaining_hours = COALESCE(remaining_hours, remainingHours) "
                "WHERE remainingHours IS NOT NULL"
            )
        )
        print("[ok] lesson_records.remaining_hours backfilled from remainingHours")

    if column_exists(conn, "lesson_records", "remainHours"):
        conn.execute(
            text(
                "UPDATE lesson_records "
                "SET remaining_hours = COALESCE(remaining_hours, remainHours) "
                "WHERE remainHours IS NOT NULL"
            )
        )
        print("[ok] lesson_records.remaining_hours backfilled from remainHours")


def patch_students(conn) -> None:
    # grade 已有时只调整默认值；空值统一归到“未分配”。
    ensure_column(
        conn,
        "students",
        "grade",
        "ALTER TABLE students ADD COLUMN grade VARCHAR(50) NOT NULL DEFAULT '未分配'",
    )
    conn.execute(text("ALTER TABLE students MODIFY COLUMN grade VARCHAR(50) NOT NULL DEFAULT '未分配'"))
    conn.execute(text("UPDATE students SET grade = '未分配' WHERE grade IS NULL OR grade = ''"))
    print("[ok] students.grade default ensured")

    ensure_column(
        conn,
        "students",
        "school",
        "ALTER TABLE students ADD COLUMN school VARCHAR(100) NULL AFTER grade",
    )
    print("[ok] students.school ensured")

    # 现有项目数据库列名是 class_type，API 通过 Pydantic 输出 classType。
    ensure_column(
        conn,
        "students",
        "class_type",
        "ALTER TABLE students ADD COLUMN class_type VARCHAR(50) NOT NULL DEFAULT 'VIP'",
    )
    conn.execute(text("ALTER TABLE students MODIFY COLUMN class_type VARCHAR(50) NOT NULL DEFAULT 'VIP'"))
    conn.execute(text("UPDATE students SET class_type = 'VIP' WHERE class_type IS NULL OR class_type = ''"))
    conn.execute(text("UPDATE students SET class_type = 'VIP' WHERE LOWER(class_type) = 'vip' OR class_type = '一对一'"))
    conn.execute(text("UPDATE students SET class_type = '小班' WHERE LOWER(class_type) = 'small'"))
    print("[ok] students.class_type default ensured")

    # 新软删除列按需求使用 camelCase 数据库列名，SQLAlchemy 通过 Column('isDeleted') 映射。
    ensure_column(
        conn,
        "students",
        "isDeleted",
        "ALTER TABLE students ADD COLUMN isDeleted TINYINT(1) NOT NULL DEFAULT 0",
    )
    ensure_column(
        conn,
        "students",
        "deletedAt",
        "ALTER TABLE students ADD COLUMN deletedAt DATETIME NULL",
    )
    ensure_index(
        conn,
        "students",
        "ix_students_isDeleted",
        "CREATE INDEX ix_students_isDeleted ON students (isDeleted)",
    )


def patch_student_subjects(conn) -> None:
    ensure_column(
        conn,
        "student_subjects",
        "subject_name",
        "ALTER TABLE student_subjects ADD COLUMN subject_name VARCHAR(100) NOT NULL DEFAULT '综合'",
    )
    ensure_column(
        conn,
        "student_subjects",
        "total_hours",
        "ALTER TABLE student_subjects ADD COLUMN total_hours DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    ensure_column(
        conn,
        "student_subjects",
        "remaining_hours",
        "ALTER TABLE student_subjects ADD COLUMN remaining_hours DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    ensure_column(
        conn,
        "student_subjects",
        "deducted_hours",
        "ALTER TABLE student_subjects ADD COLUMN deducted_hours DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    print("[ok] student_subjects hour fields ensured")


def patch_lesson_records(conn) -> None:
    ensure_column(
        conn,
        "lesson_records",
        "subject_name",
        "ALTER TABLE lesson_records ADD COLUMN subject_name VARCHAR(100) NOT NULL DEFAULT '综合'",
    )
    ensure_column(
        conn,
        "lesson_records",
        "change_type",
        "ALTER TABLE lesson_records ADD COLUMN change_type VARCHAR(20) NOT NULL DEFAULT 'add'",
    )
    ensure_column(
        conn,
        "lesson_records",
        "hours",
        "ALTER TABLE lesson_records ADD COLUMN hours DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    ensure_column(
        conn,
        "lesson_records",
        "amount",
        "ALTER TABLE lesson_records ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    ensure_column(
        conn,
        "lesson_records",
        "remaining_hours",
        "ALTER TABLE lesson_records ADD COLUMN remaining_hours DECIMAL(10,2) NULL",
    )
    # recordDate 按需求使用 camelCase 数据库列名，旧数据用 created_at 回填。
    ensure_column(
        conn,
        "lesson_records",
        "recordDate",
        "ALTER TABLE lesson_records ADD COLUMN recordDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    ensure_column(
        conn,
        "lesson_records",
        "operator_name",
        "ALTER TABLE lesson_records ADD COLUMN operator_name VARCHAR(100) NOT NULL DEFAULT '系统'",
    )
    ensure_column(
        conn,
        "lesson_records",
        "remark",
        "ALTER TABLE lesson_records ADD COLUMN remark TEXT NULL",
    )
    ensure_column(
        conn,
        "lesson_records",
        "created_at",
        "ALTER TABLE lesson_records ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    backfill_lesson_record_legacy_columns(conn)
    conn.execute(text("UPDATE lesson_records SET recordDate = COALESCE(recordDate, created_at, NOW())"))
    print("[ok] lesson_records.recordDate backfilled")


def patch_payments(conn) -> None:
    ensure_column(
        conn,
        "payments",
        "amount",
        "ALTER TABLE payments ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0.00",
    )
    ensure_column(
        conn,
        "payments",
        "remark",
        "ALTER TABLE payments ADD COLUMN remark VARCHAR(255) NULL",
    )
    ensure_column(
        conn,
        "payments",
        "created_at",
        "ALTER TABLE payments ADD COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    )
    print("[ok] payments fields ensured")


def main() -> None:
    try:
        with engine.begin() as conn:
            print("[db]", conn.execute(text("SELECT DATABASE()")).scalar_one())
            patch_students(conn)
            patch_student_subjects(conn)
            patch_lesson_records(conn)
            patch_payments(conn)
        print("[done] database schema patch completed")
    except Exception:
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
