
import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "investigations.db")


def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()

    try:
        table_exists = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'investigations'
            """
        ).fetchone()

        if not table_exists:
            conn.execute(
                """
                CREATE TABLE investigations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    event_id TEXT,
                    host TEXT,
                    problem TEXT,
                    severity TEXT,
                    trigger_id TEXT,
                    status TEXT NOT NULL,
                    analysis TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    duration_ms INTEGER
                )
                """
            )
        else:
            existing_columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(investigations)"
                ).fetchall()
            }

            migrations = {
                "started_at": (
                    "ALTER TABLE investigations "
                    "ADD COLUMN started_at TEXT"
                ),
                "completed_at": (
                    "ALTER TABLE investigations "
                    "ADD COLUMN completed_at TEXT"
                ),
                "duration_ms": (
                    "ALTER TABLE investigations "
                    "ADD COLUMN duration_ms INTEGER"
                ),
            }

            for column, statement in migrations.items():
                if column not in existing_columns:
                    conn.execute(statement)

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_investigations_event_id
            ON investigations(event_id)
            """
        )

        conn.commit()

    finally:
        conn.close()


def save_investigation(
    event_id=None,
    host=None,
    problem=None,
    severity=None,
    trigger_id=None,
    status="processing",
    analysis="",
    started_at=None,
    completed_at=None,
    duration_ms=None,
):
    if started_at is None:
        started_at = datetime.now(
            timezone.utc
        ).isoformat()

    conn = _connect()

    try:
        cursor = conn.execute(
            """
            INSERT INTO investigations (
                created_at,
                event_id,
                host,
                problem,
                severity,
                trigger_id,
                status,
                analysis,
                started_at,
                completed_at,
                duration_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                None if event_id is None else str(event_id),
                host,
                problem,
                severity,
                None if trigger_id is None else str(trigger_id),
                status,
                analysis or "",
                started_at,
                completed_at,
                duration_ms,
            ),
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def find_investigation_by_event(event_id):
    if event_id is None:
        return None

    conn = _connect()

    try:
        row = conn.execute(
            """
            SELECT
                id,
                created_at,
                event_id,
                host,
                problem,
                severity,
                trigger_id,
                status,
                analysis,
                started_at,
                completed_at,
                duration_ms
            FROM investigations
            WHERE event_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (str(event_id),),
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def update_investigation(
    investigation_id,
    status,
    analysis="",
    completed_at=None,
    duration_ms=None,
):
    if completed_at is None:
        completed_at = datetime.now(
            timezone.utc
        ).isoformat()

    conn = _connect()

    try:
        cursor = conn.execute(
            """
            UPDATE investigations
            SET
                status = ?,
                analysis = ?,
                completed_at = ?,
                duration_ms = ?
            WHERE id = ?
            """,
            (
                status,
                analysis or "",
                completed_at,
                duration_ms,
                investigation_id,
            ),
        )

        conn.commit()
        return cursor.rowcount

    finally:
        conn.close()


def get_investigations(limit=50):
    limit = max(1, min(int(limit), 200))

    conn = _connect()

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                event_id,
                host,
                problem,
                severity,
                trigger_id,
                status,
                analysis,
                started_at,
                completed_at,
                duration_ms
            FROM investigations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(
        f"Investigation database ready: {DB_PATH}"
    )
