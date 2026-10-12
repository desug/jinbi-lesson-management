"""Preserve existing descriptive revisions without MySQL VARCHAR(32) truncation."""
from alembic.ddl.mysql import MySQLImpl
from sqlalchemy import String


class LongRevisionMySQLImpl(MySQLImpl):
    __dialect__ = "mysql"

    def version_table_impl(self, **kwargs):
        table = super().version_table_impl(**kwargs)
        table.c.version_num.type = String(128)
        return table
