"""SQLite implementation of the ReservationRepository interface."""

from datetime import datetime
from pathlib import Path
import sqlite3

from lab_reservations.domain.models import (
    Reservation,
    ReservationStatus,
)
from lab_reservations.domain.repository import ReservationRepository
from lab_reservations.infrastructure.database import get_db_connection, init_db


class SQLiteReservationRepository(ReservationRepository):
    """Persists reservations to a local SQLite database."""

    def __init__(self, db_path: str | Path = "data/reservations.db") -> None:
        self.db_path = db_path
        init_db(self.db_path)

    def _row_to_reservation(self, row: sqlite3.Row) -> Reservation:
        return Reservation(
            id=row["id"],
            unit_id=row["unit_id"],
            requester=row["requester"],
            start_time=datetime.fromisoformat(row["start_time"]),
            end_time=datetime.fromisoformat(row["end_time"]),
            status=ReservationStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def save(self, reservation: Reservation) -> Reservation:
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO reservations (id, unit_id, requester, start_time, end_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    unit_id = excluded.unit_id,
                    requester = excluded.requester,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    status = excluded.status;
                """,
                (
                    reservation.id,
                    reservation.unit_id,
                    reservation.requester,
                    reservation.start_time.isoformat(),
                    reservation.end_time.isoformat(),
                    reservation.status.value,
                    reservation.created_at.isoformat(),
                ),
            )
            conn.commit()
        return reservation

    def get_by_id(self, reservation_id: str) -> Reservation | None:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM reservations WHERE id = ?;",
                (reservation_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_reservation(row)

    def get_active_by_unit(self, unit_id: str) -> list[Reservation]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM reservations
                WHERE unit_id = ? AND status = ?
                ORDER BY start_time ASC;
                """,
                (unit_id, ReservationStatus.ACTIVE.value),
            )
            rows = cursor.fetchall()
            return [self._row_to_reservation(r) for r in rows]

    def get_all(self) -> list[Reservation]:
        with get_db_connection(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM reservations ORDER BY start_time ASC;"
            )
            rows = cursor.fetchall()
            return [self._row_to_reservation(r) for r in rows]
