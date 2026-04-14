"""
Database schema migrations.
"""

import logging

logger = logging.getLogger(__name__)

CURRENT_VERSION = 1


class Migrations:
    """Manages database schema migrations."""

    def __init__(self, db):
        self.db = db
        self._ensure_version_table()

    def _ensure_version_table(self):
        """Create schema version table if it doesn't exist."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        row = self.db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        if row is None:
            self.db.execute("INSERT INTO schema_version (version) VALUES (0)")
            self.db.commit()

    def get_version(self) -> int:
        """Get current schema version."""
        row = self.db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        return row["version"] if row else 0

    def migrate(self, target: int = CURRENT_VERSION):
        """Run migrations up to target version."""
        current = self.get_version()
        if current >= target:
            return

        logger.info(f"Migrating schema from v{current} to v{target}")

        if current < 1 <= target:
            self._migration_v1()

        self.db.execute("UPDATE schema_version SET version = ?", (target,))
        self.db.commit()
        logger.info(f"Schema migrated to v{target}")

    def _migration_v1(self):
        """Initial schema (handled by DatabaseManager._create_tables)."""
        pass
