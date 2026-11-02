"""Repository interface for persisting and retrieving reservations."""

from abc import ABC, abstractmethod

from lab_reservations.domain.models import Reservation


class ReservationRepository(ABC):
    """Abstract repository boundary for reservation persistence."""

    @abstractmethod
    def save(self, reservation: Reservation) -> Reservation:
        """Create or update a reservation."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, reservation_id: str) -> Reservation | None:
        """Retrieve a reservation by its unique identifier."""
        raise NotImplementedError

    @abstractmethod
    def get_active_by_unit(self, unit_id: str) -> list[Reservation]:
        """Retrieve all currently active reservations for a given equipment unit."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[Reservation]:
        """Retrieve all reservations, both active and cancelled."""
        raise NotImplementedError
