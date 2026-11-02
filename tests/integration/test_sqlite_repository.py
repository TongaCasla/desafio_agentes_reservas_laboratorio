"""Integration tests for SQLite persistence."""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from lab_reservations.domain.models import (
    Reservation,
    ReservationStatus,
)
from lab_reservations.infrastructure.sqlite_repository import SQLiteReservationRepository


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    return tmp_path / "test_reservations.db"


def test_sqlite_save_and_retrieve_by_id(temp_db: Path) -> None:
    repo = SQLiteReservationRepository(db_path=temp_db)
    res = Reservation(
        unit_id="MIC-01",
        requester="Marie Curie",
        start_time=datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc),
    )
    repo.save(res)

    retrieved = repo.get_by_id(res.id)
    assert retrieved is not None
    assert retrieved.id == res.id
    assert retrieved.unit_id == "MIC-01"
    assert retrieved.requester == "Marie Curie"
    assert retrieved.start_time == res.start_time
    assert retrieved.end_time == res.end_time
    assert retrieved.status == ReservationStatus.ACTIVE


def test_sqlite_persistence_survives_restart(temp_db: Path) -> None:
    # Session 1: create and persist
    repo_1 = SQLiteReservationRepository(db_path=temp_db)
    res_active = Reservation(
        unit_id="OSC-01",
        requester="Nikola Tesla",
        start_time=datetime(2026, 11, 1, 14, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 16, 0, tzinfo=timezone.utc),
    )
    res_cancelled = Reservation(
        unit_id="OSC-01",
        requester="Thomas Edison",
        start_time=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
    )
    res_cancelled.cancel()
    repo_1.save(res_active)
    repo_1.save(res_cancelled)

    # Session 2: simulate complete app restart with a fresh repository instance
    repo_2 = SQLiteReservationRepository(db_path=temp_db)
    all_res = repo_2.get_all()
    assert len(all_res) == 2

    active_by_unit = repo_2.get_active_by_unit("OSC-01")
    assert len(active_by_unit) == 1
    assert active_by_unit[0].id == res_active.id
    assert active_by_unit[0].requester == "Nikola Tesla"

    recovered_cancelled = repo_2.get_by_id(res_cancelled.id)
    assert recovered_cancelled is not None
    assert recovered_cancelled.status == ReservationStatus.CANCELLED
