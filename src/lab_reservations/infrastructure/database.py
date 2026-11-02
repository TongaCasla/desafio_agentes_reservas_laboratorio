"""SQLite database connection and initialization."""

from pathlib import Path
import sqlite3


def get_db_connection(db_path: str | Path) -> sqlite3.Connection:
    """Create a connection to SQLite database configured with row factory."""
    if isinstance(db_path, str) and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path) -> None:
    """Initialize database tables and indexes."""
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                unit_id TEXT NOT NULL,
                requester TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reservations_unit_status
            ON reservations(unit_id, status);
        """)
        conn.commit()
