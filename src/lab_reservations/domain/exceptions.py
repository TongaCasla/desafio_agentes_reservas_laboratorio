"""Domain exceptions for laboratory equipment reservations."""


class LabReservationError(Exception):
    """Base exception for domain errors."""


class UnitNotFoundError(LabReservationError):
    """Raised when equipment unit ID is not found in the inventory."""

    def __init__(self, unit_id: str) -> None:
        self.unit_id = unit_id
        super().__init__(f"Equipment unit '{unit_id}' does not exist in inventory.")


class InvalidTimeRangeError(LabReservationError):
    """Raised when start time is not strictly before end time."""

    def __init__(self, message: str = "Reservation start time must be strictly before end time.") -> None:
        super().__init__(message)


class EmptyRequesterError(LabReservationError):
    """Raised when requester name is empty or contains only whitespace."""

    def __init__(self, message: str = "Requester name cannot be empty or blank.") -> None:
        super().__init__(message)


class ReservationOverlapError(LabReservationError):
    """Raised when a reservation conflicts with an existing active reservation on the same unit."""

    def __init__(self, unit_id: str, message: str | None = None) -> None:
        self.unit_id = unit_id
        msg = message or f"Equipment unit '{unit_id}' is already reserved during the requested time window."
        super().__init__(msg)


class ReservationNotFoundError(LabReservationError):
    """Raised when reservation ID is not found."""

    def __init__(self, reservation_id: str) -> None:
        self.reservation_id = reservation_id
        super().__init__(f"Reservation '{reservation_id}' was not found.")


class ReservationAlreadyCancelledError(LabReservationError):
    """Raised when attempting to cancel an already cancelled reservation."""

    def __init__(self, reservation_id: str) -> None:
        self.reservation_id = reservation_id
        super().__init__(f"Reservation '{reservation_id}' is already cancelled.")
