"""Unit tests for domain entities and validation rules."""

from datetime import datetime, timezone
import pytest

from lab_reservations.domain.exceptions import (
    EmptyRequesterError,
    InvalidTimeRangeError,
    UnitNotFoundError,
)
from lab_reservations.domain.models import (
    INVENTORY,
    Reservation,
    ReservationStatus,
)


def test_valid_reservation_creation() -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    reservation = Reservation(
        unit_id="MIC-01",
        requester="Alice Scientist",
        start_time=start,
        end_time=end,
    )

    assert reservation.unit_id == "MIC-01"
    assert reservation.requester == "Alice Scientist"
    assert reservation.start_time == start
    assert reservation.end_time == end
    assert reservation.status == ReservationStatus.ACTIVE
    assert reservation.is_active is True
    assert reservation.id is not None


def test_reservation_creation_rejects_unknown_unit() -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(UnitNotFoundError) as exc_info:
        Reservation(
            unit_id="UNKNOWN-99",
            requester="Alice",
            start_time=start,
            end_time=end,
        )
    assert "UNKNOWN-99" in str(exc_info.value)


@pytest.mark.parametrize("invalid_requester", ["", "   ", "\t\n  "])
def test_reservation_creation_rejects_empty_or_whitespace_requester(invalid_requester: str) -> None:
    start = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)

    with pytest.raises(EmptyRequesterError):
        Reservation(
            unit_id="MIC-01",
            requester=invalid_requester,
            start_time=start,
            end_time=end,
        )


def test_reservation_creation_rejects_inverted_time_range() -> None:
    start = datetime(2026, 11, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(InvalidTimeRangeError):
        Reservation(
            unit_id="MIC-01",
            requester="Alice",
            start_time=start,
            end_time=end,
        )


def test_reservation_creation_rejects_identical_start_and_end() -> None:
    moment = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(InvalidTimeRangeError):
        Reservation(
            unit_id="MIC-01",
            requester="Alice",
            start_time=moment,
            end_time=moment,
        )


def test_consecutive_boundaries_do_not_overlap() -> None:
    # Reservation A: 10:00 to 11:00
    res_a = Reservation(
        unit_id="MIC-01",
        requester="Alice",
        start_time=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc),
    )

    # Immediately after: 11:00 to 12:00
    after_start = datetime(2026, 11, 1, 11, 0, tzinfo=timezone.utc)
    after_end = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
    assert res_a.overlaps_with(after_start, after_end) is False

    # Immediately before: 09:00 to 10:00
    before_start = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    before_end = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)
    assert res_a.overlaps_with(before_start, before_end) is False


def test_overlapping_intervals_detected() -> None:
    # Reservation: 10:00 to 12:00
    res = Reservation(
        unit_id="MIC-01",
        requester="Alice",
        start_time=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
    )

    # Partial overlap inside: 10:30 to 11:30
    assert res.overlaps_with(
        datetime(2026, 11, 1, 10, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 11, 30, tzinfo=timezone.utc),
    ) is True

    # Partial overlap left: 09:30 to 10:30
    assert res.overlaps_with(
        datetime(2026, 11, 1, 9, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 10, 30, tzinfo=timezone.utc),
    ) is True

    # Partial overlap right: 11:30 to 12:30
    assert res.overlaps_with(
        datetime(2026, 11, 1, 11, 30, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 12, 30, tzinfo=timezone.utc),
    ) is True

    # Enclosing overlap: 09:00 to 13:00
    assert res.overlaps_with(
        datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 13, 0, tzinfo=timezone.utc),
    ) is True


def test_cancelled_reservation_does_not_overlap() -> None:
    res = Reservation(
        unit_id="MIC-01",
        requester="Alice",
        start_time=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
    )
    res.cancel()

    assert res.status == ReservationStatus.CANCELLED
    assert res.is_active is False
    # Exact same window does not overlap because status is CANCELLED
    assert res.overlaps_with(
        datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc),
    ) is False
