"""student soft delete and lesson amount"""

from alembic import op
import sqlalchemy as sa


revision = "20260502_student_soft_delete_lesson_amount"
down_revision = "20260429_add_grade_to_students"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("isDeleted", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column("students", sa.Column("deletedAt", sa.DateTime(), nullable=True))
    op.create_index("ix_students_isDeleted", "students", ["isDeleted"], unique=False)
    op.alter_column(
        "students",
        "grade",
        server_default="未分配",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "students",
        "class_type",
        server_default="vip",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )

    op.add_column(
        "lesson_records",
        sa.Column("amount", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
    )
    op.add_column(
        "lesson_records",
        sa.Column("remaining_hours", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "lesson_records",
        sa.Column("recordDate", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("lesson_records", "recordDate")
    op.drop_column("lesson_records", "remaining_hours")
    op.drop_column("lesson_records", "amount")
    op.alter_column(
        "students",
        "class_type",
        server_default=None,
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "students",
        "grade",
        server_default="初一",
        existing_type=sa.String(length=20),
        existing_nullable=False,
    )

    op.drop_index("ix_students_isDeleted", table_name="students")
    op.drop_column("students", "deletedAt")
    op.drop_column("students", "isDeleted")
