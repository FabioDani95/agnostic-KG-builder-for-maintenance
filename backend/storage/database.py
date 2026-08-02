"""SQLite bootstrap, migrations and transaction boundaries."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from backend.domain.ids import utc_now
from backend.services.ontology_schema_service import ontology_contract

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def operational_db_path() -> Path:
    configured = str(os.environ.get("KG_OPERATIONAL_DB", "") or "").strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else (_REPO_ROOT / path).resolve()
    return _REPO_ROOT / "data" / "operational.db"


class Database:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else operational_db_path()

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def migrate(self) -> list[str]:
        applied: list[str] = []
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    sha256 TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            existing = {
                row["version"]: row["sha256"]
                for row in connection.execute("SELECT version, sha256 FROM schema_migrations")
            }
            for migration in sorted(_MIGRATIONS.glob("*.sql")):
                version = migration.stem
                sql = migration.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
                if version in existing:
                    if existing[version] != checksum:
                        raise RuntimeError(f"Applied migration changed: {version}")
                    continue
                escaped_version = version.replace("'", "''")
                escaped_checksum = checksum.replace("'", "''")
                applied_at = utc_now().replace("'", "''")
                connection.executescript(
                    "BEGIN IMMEDIATE;\n"
                    f"{sql}\n"
                    "INSERT INTO schema_migrations(version, sha256, applied_at) "
                    f"VALUES ('{escaped_version}', '{escaped_checksum}', '{applied_at}');\n"
                    "COMMIT;"
                )
                applied.append(version)
        return applied

    def bootstrap(self) -> None:
        contract = ontology_contract()
        self.migrate()
        with self.transaction() as connection:
            current = connection.execute(
                "SELECT value FROM operational_metadata WHERE key = 'ontology_sha256'"
            ).fetchone()
            if current is not None and current["value"] != contract.sha256:
                raise RuntimeError("Operational store ontology checksum does not match the approved contract")
            now = utc_now()
            connection.execute(
                """
                INSERT INTO operational_metadata(key, value, updated_at)
                VALUES ('ontology_sha256', ?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (contract.sha256, now),
            )
            connection.execute(
                """
                INSERT INTO operational_metadata(key, value, updated_at)
                VALUES ('ontology_version', ?, ?)
                ON CONFLICT(key) DO NOTHING
                """,
                (contract.version, now),
            )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()


def get_database() -> Database:
    database = Database()
    database.bootstrap()
    return database

