"""Application and domain service for reservation management."""

from datetime import datetime

from lab_reservations.domain.exceptions import (
    InvalidTimeRangeError,
    ReservationAlreadyCancelledError,
    ReservationNotFoundError,
    ReservationOverlapError,
    UnitNotFoundError,
)
from lab_reservations.domain.models import (
    INVENTORY,
    EquipmentUnit,
    Reservation,
    ReservationStatus,
    normalize_datetime,
)
from lab_reservations.domain.repository import ReservationRepository


class ReservationService:
    """Service encapsulating all reservation business rules and operations."""

    def __init__(self, repository: ReservationRepository) -> None:
        self.repository = repository

    def list_inventory(self) -> list[EquipmentUnit]:
        """Return all equipment units available in the laboratory."""
        return [EquipmentUnit(unit_id=uid, name=name) for uid, name in INVENTORY.items()]

    def create_reservation(
        self,
        unit_id: str,
        requester: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Reservation:
        """Create a new reservation after validating business and concurrency rules."""
        if unit_id not in INVENTORY:
            raise UnitNotFoundError(unit_id)

        norm_start = normalize_datetime(start_time)
        norm_end = normalize_datetime(end_time)

        if norm_start >= norm_end:
            raise InvalidTimeRangeError(
                f"Start time ({norm_start.isoformat()}) must be strictly before end time ({norm_end.isoformat()})."
            )

        # Check concurrency on the same unit
        active_reservations = self.repository.get_active_by_unit(unit_id)
        for existing in active_reservations:
            if existing.overlaps_with(norm_start, norm_end):
                raise ReservationOverlapError(
                    unit_id=unit_id,
                    message=(
                        f"Unit '{unit_id}' is already reserved between "
                        f"{existing.start_time.isoformat()} and {existing.end_time.isoformat()}."
                    ),
                )

        reservation = Reservation(
            unit_id=unit_id,
            requester=requester,
            start_time=norm_start,
            end_time=norm_end,
        )

        return self.repository.save(reservation)

    def cancel_reservation(self, reservation_id: str) -> Reservation:
        """Cancel an existing reservation, releasing the time slot immediately."""
        reservation = self.repository.get_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(reservation_id)

        if not reservation.is_active:
            raise ReservationAlreadyCancelledError(reservation_id)

        reservation.cancel()
        return self.repository.save(reservation)

    def get_reservation(self, reservation_id: str) -> Reservation:
        """Retrieve a specific reservation by ID."""
        reservation = self.repository.get_by_id(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError(reservation_id)
        return reservation

    def list_reservations(
        self,
        unit_id: str | None = None,
        status: ReservationStatus | None = None,
    ) -> list[Reservation]:
        """List reservations with optional filtering by unit and status."""
        all_reservations = self.repository.get_all()
        filtered = all_reservations

        if unit_id is not None:
            if unit_id not in INVENTORY:
                raise UnitNotFoundError(unit_id)
            filtered = [r for r in filtered if r.unit_id == unit_id]

        if status is not None:
            filtered = [r for r in filtered if r.status == status]

        return filtered

    def check_unit_availability(
        self,
        unit_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Check if a specific unit is available during the given interval."""
        if unit_id not in INVENTORY:
            raise UnitNotFoundError(unit_id)

        norm_start = normalize_datetime(start_time)
        norm_end = normalize_datetime(end_time)

        if norm_start >= norm_end:
            raise InvalidTimeRangeError(
                f"Start time ({norm_start.isoformat()}) must be strictly before end time ({norm_end.isoformat()})."
            )

        active_reservations = self.repository.get_active_by_unit(unit_id)
        for existing in active_reservations:
            if existing.overlaps_with(norm_start, norm_end):
                return False

        return True

    def get_available_units(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[EquipmentUnit]:
        """Return all units available during the requested interval."""
        norm_start = normalize_datetime(start_time)
        norm_end = normalize_datetime(end_time)

        if norm_start >= norm_end:
            raise InvalidTimeRangeError(
                f"Start time ({norm_start.isoformat()}) must be strictly before end time ({norm_end.isoformat()})."
            )

        available: list[EquipmentUnit] = []
        for uid, name in INVENTORY.items():
            if self.check_unit_availability(uid, norm_start, norm_end):
                available.append(EquipmentUnit(unit_id=uid, name=name))

        return available
