"""Dependency injection for FastAPI endpoints."""

import os
from functools import lru_cache

from lab_reservations.domain.service import ReservationService
from lab_reservations.infrastructure.sqlite_repository import SQLiteReservationRepository


@lru_cache
def get_service() -> ReservationService:
    """Provide the default ReservationService backed by SQLite."""
    db_path = os.getenv("DATABASE_PATH", "data/reservations.db")
    repository = SQLiteReservationRepository(db_path=db_path)
    return ReservationService(repository=repository)
