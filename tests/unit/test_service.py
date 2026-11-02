"""Unit tests for ReservationService business rules and use cases."""

from datetime import datetime, timezone
import pytest

from lab_reservations.domain.exceptions import (
    InvalidTimeRangeError,
    ReservationAlreadyCancelledError,
    ReservationNotFoundError,
    ReservationOverlapError,
    UnitNotFoundError,
)
from lab_reservations.domain.models import (
    Reservation,
    ReservationStatus,
)
from lab_reservations.domain.repository import ReservationRepository
from lab_reservations.domain.service import ReservationService


class InMemoryReservationRepository(ReservationRepository):
    """In-memory test double for repository."""

    def __init__(self) -> None:
        self.reservations: dict[str, Reservation] = {}

    def save(self, reservation: Reservation) -> Reservation:
        self.reservations[reservation.id] = reservation
        return reservation

    def get_by_id(self, reservation_id: str) -> Reservation | None:
        return self.reservations.get(reservation_id)

    def get_active_by_unit(self, unit_id: str) -> list[Reservation]:
        return [
            r for r in self.reservations.values()
            if r.unit_id == unit_id and r.is_active
        ]

    def get_all(self) -> list[Reservation]:
        return list(self.reservations.values())


@pytest.fixture
def service() -> ReservationService:
    repo = InMemoryReservationRepository()
    return ReservationService(repository=repo)


def test_list_inventory(service: ReservationService) -> None:
    inventory = service.list_inventory()
    assert len(inventory) == 5
    unit_ids = {u.unit_id for u in inventory}
    assert unit_ids == {"MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"}


def test_create_reservation_success(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)
    res = service.create_reservation("MIC-01", "Dr. House", start, end)

    assert res.id is not None
    assert res.unit_id == "MIC-01"
    assert res.requester == "Dr. House"
    assert res.status == ReservationStatus.ACTIVE


def test_create_reservation_fails_for_unknown_unit(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)

    with pytest.raises(UnitNotFoundError):
        service.create_reservation("NON-EXISTENT", "Dr. House", start, end)


def test_create_reservation_rejects_overlap_on_same_unit(service: ReservationService) -> None:
    start_a = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end_a = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    service.create_reservation("MIC-01", "Alice", start_a, end_a)

    # Attempt overlapping reservation on same unit MIC-01
    start_b = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)
    end_b = datetime(2026, 11, 1, 13, 0, tzinfo=timezone.utc)

    with pytest.raises(ReservationOverlapError) as exc_info:
        service.create_reservation("MIC-01", "Bob", start_b, end_b)
    assert "MIC-01" in str(exc_info.value)


def test_consecutive_reservations_on_same_unit_allowed(service: ReservationService) -> None:
    # Reservation A: 10:00 to 11:00 on MIC-01
    start_a = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end_a = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)
    res_a = service.create_reservation("MIC-01", "Alice", start_a, end_a)

    # Reservation B: 11:00 to 12:00 on same unit MIC-01
    start_b = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)
    end_b = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    res_b = service.create_reservation("MIC-01", "Bob", start_b, end_b)

    assert res_a.id != res_b.id
    assert res_a.is_active is True
    assert res_b.is_active is True


def test_different_units_can_be_reserved_at_exact_same_time(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)

    res_mic1 = service.create_reservation("MIC-01", "Alice", start, end)
    res_mic2 = service.create_reservation("MIC-02", "Bob", start, end)

    assert res_mic1.unit_id == "MIC-01"
    assert res_mic2.unit_id == "MIC-02"
    assert res_mic1.is_active is True
    assert res_mic2.is_active is True


def test_cancel_reservation_releases_slot_and_preserves_history(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    res = service.create_reservation("OSC-01", "Alice", start, end)

    cancelled = service.cancel_reservation(res.id)
    assert cancelled.id == res.id
    assert cancelled.status == ReservationStatus.CANCELLED
    assert cancelled.requester == "Alice"
    assert cancelled.unit_id == "OSC-01"

    # Now another reservation in the same slot must succeed
    new_res = service.create_reservation("OSC-01", "Bob", start, end)
    assert new_res.is_active is True
    assert new_res.id != res.id


def test_cancel_non_existent_reservation_raises(service: ReservationService) -> None:
    with pytest.raises(ReservationNotFoundError):
        service.cancel_reservation("non-existent-id")


def test_cancel_already_cancelled_reservation_raises(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    res = service.create_reservation("MUL-01", "Alice", start, end)

    service.cancel_reservation(res.id)
    with pytest.raises(ReservationAlreadyCancelledError):
        service.cancel_reservation(res.id)


def test_availability_query_respects_rules(service: ReservationService) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    # Initial state: all units available
    available = service.get_available_units(start, end)
    assert len(available) == 5

    # Reserve FUE-01
    service.create_reservation("FUE-01", "Alice", start, end)

    # FUE-01 should no longer be available in that window
    assert service.check_unit_availability("FUE-01", start, end) is False
    available_now = service.get_available_units(start, end)
    assert len(available_now) == 4
    assert "FUE-01" not in {u.unit_id for u in available_now}

    # Consecutive window: 12:00 to 14:00 should still be available for FUE-01
    assert service.check_unit_availability(
        "FUE-01",
        datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 14, 0, tzinfo=timezone.utc),
    ) is True
