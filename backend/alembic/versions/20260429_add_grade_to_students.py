"""add grade to students"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_add_grade_to_students"
down_revision = "72070fbb0218"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "students",
        sa.Column("grade", sa.String(length=20), server_default="初一", nullable=False),
    )
    op.create_index(op.f("ix_students_grade"), "students", ["grade"], unique=False)
    op.execute("UPDATE students SET grade = '初一' WHERE grade IS NULL OR grade = ''")


def downgrade() -> None:
    op.drop_index(op.f("ix_students_grade"), table_name="students")
    op.drop_column("students", "grade")
