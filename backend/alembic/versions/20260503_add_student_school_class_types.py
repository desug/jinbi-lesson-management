"""add student school and canonical class types"""

from alembic import op
import sqlalchemy as sa


revision = "20260503_add_student_school_class_types"
down_revision = "20260502_student_soft_delete_lesson_amount"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    count = bind.execute(
        sa.text(
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


def upgrade() -> None:
    if not _column_exists("students", "school"):
        op.add_column(
            "students",
            sa.Column("school", sa.String(length=100), nullable=True, comment="学校"),
        )
    op.alter_column(
        "students",
        "grade",
        type_=sa.String(length=50),
        server_default="未分配",
        existing_nullable=False,
    )
    op.alter_column(
        "students",
        "class_type",
        type_=sa.String(length=50),
        server_default="VIP",
        existing_nullable=False,
    )
    op.execute("UPDATE students SET class_type = 'VIP' WHERE class_type IS NULL OR class_type = ''")
    op.execute("UPDATE students SET class_type = 'VIP' WHERE LOWER(class_type) = 'vip' OR class_type = '一对一'")
    op.execute("UPDATE students SET class_type = '小班' WHERE LOWER(class_type) = 'small'")


def downgrade() -> None:
    op.execute("UPDATE students SET class_type = 'vip' WHERE class_type = 'VIP'")
    op.execute("UPDATE students SET class_type = 'small' WHERE class_type = '小班'")
    op.alter_column(
        "students",
        "class_type",
        type_=sa.String(length=20),
        server_default="vip",
        existing_nullable=False,
    )
    op.alter_column(
        "students",
        "grade",
        type_=sa.String(length=20),
        server_default="未分配",
        existing_nullable=False,
    )
    op.drop_column("students", "school")
