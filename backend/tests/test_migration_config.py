from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

import app.core.migrations  # noqa: F401 - same registration imported by alembic/env.py


def test_mysql_version_table_can_store_every_existing_revision():
    backend = Path(__file__).resolve().parents[1]
    config = Config(str(backend / "alembic.ini"))
    config.set_main_option("script_location", str(backend / "alembic"))
    revisions = list(ScriptDirectory.from_config(config).walk_revisions())
    context = MigrationContext.configure(dialect_name="mysql")
    table = context.impl.version_table_impl(version_table="alembic_version",
                                            version_table_schema=None, version_table_pk=True)
    assert table.c.version_num.type.length >= max(len(revision.revision) for revision in revisions)
