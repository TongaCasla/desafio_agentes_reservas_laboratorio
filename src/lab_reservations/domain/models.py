"""Domain models and immutable inventory definitions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from lab_reservations.domain.exceptions import (
    EmptyRequesterError,
    InvalidTimeRangeError,
    UnitNotFoundError,
)


class ReservationStatus(str, Enum):
    """Status lifecycle for reservations."""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# Fixed, immutable inventory specified in requirements
INVENTORY: dict[str, str] = {
    "MIC-01": "Microscopio digital",
    "MIC-02": "Microscopio digital",
    "OSC-01": "Osciloscopio",
    "MUL-01": "Multímetro",
    "FUE-01": "Fuente de alimentación",
}


def normalize_datetime(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class EquipmentUnit:
    """Equipment unit available in the laboratory."""

    unit_id: str
    name: str


@dataclass
class Reservation:
    """A laboratory equipment reservation entity."""

    unit_id: str
    requester: str
    start_time: datetime
    end_time: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ReservationStatus = ReservationStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.unit_id not in INVENTORY:
            raise UnitNotFoundError(self.unit_id)

        clean_requester = self.requester.strip()
        if not clean_requester:
            raise EmptyRequesterError("Requester name cannot be empty or consist only of whitespace.")
        self.requester = clean_requester

        self.start_time = normalize_datetime(self.start_time)
        self.end_time = normalize_datetime(self.end_time)
        self.created_at = normalize_datetime(self.created_at)

        if self.start_time >= self.end_time:
            raise InvalidTimeRangeError(
                f"Reservation start time ({self.start_time.isoformat()}) must be strictly "
                f"before end time ({self.end_time.isoformat()})."
            )

    @property
    def is_active(self) -> bool:
        return self.status == ReservationStatus.ACTIVE

    def overlaps_with(self, start: datetime, end: datetime) -> bool:
        """Check if an active reservation overlaps with a given [start, end) time window.

        Consecutive boundaries are strictly allowed:
        [10:00, 11:00) and [11:00, 12:00) do NOT overlap.
        """
        if not self.is_active:
            return False

        norm_start = normalize_datetime(start)
        norm_end = normalize_datetime(end)

        return max(self.start_time, norm_start) < min(self.end_time, norm_end)

    def cancel(self) -> None:
        """Cancel this reservation while preserving its identity and history."""
        self.status = ReservationStatus.CANCELLED
