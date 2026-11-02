"""FastAPI routing for the laboratory reservation API."""

from datetime import datetime
from fastapi import APIRouter, Depends, Query, status

from lab_reservations.api.dependencies import get_service
from lab_reservations.api.schemas import (
    AvailabilityCheckResponse,
    AvailableUnitsResponse,
    EquipmentUnitResponse,
    ReservationCreateRequest,
    ReservationResponse,
)
from lab_reservations.domain.models import ReservationStatus
from lab_reservations.domain.service import ReservationService

router = APIRouter()


@router.get("/inventory", response_model=list[EquipmentUnitResponse], summary="List inventory")
def list_inventory(
    service: ReservationService = Depends(get_service),
) -> list[EquipmentUnitResponse]:
    """Retrieve all preloaded immutable equipment units."""
    units = service.list_inventory()
    return [EquipmentUnitResponse(unit_id=u.unit_id, name=u.name) for u in units]


@router.post(
    "/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reservation",
)
def create_reservation(
    payload: ReservationCreateRequest,
    service: ReservationService = Depends(get_service),
) -> ReservationResponse:
    """Create a new reservation adhering to domain and concurrency constraints."""
    res = service.create_reservation(
        unit_id=payload.unit_id,
        requester=payload.requester,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    return ReservationResponse(
        id=res.id,
        unit_id=res.unit_id,
        requester=res.requester,
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status,
        created_at=res.created_at,
    )


@router.get("/reservations", response_model=list[ReservationResponse], summary="List reservations")
def list_reservations(
    unit_id: str | None = Query(None, description="Filter by unit ID"),
    status: ReservationStatus | None = Query(None, description="Filter by status (ACTIVE/CANCELLED)"),
    service: ReservationService = Depends(get_service),
) -> list[ReservationResponse]:
    """List all reservations with optional filters."""
    reservations = service.list_reservations(unit_id=unit_id, status=status)
    return [
        ReservationResponse(
            id=r.id,
            unit_id=r.unit_id,
            requester=r.requester,
            start_time=r.start_time,
            end_time=r.end_time,
            status=r.status,
            created_at=r.created_at,
        )
        for r in reservations
    ]


@router.get(
    "/reservations/{reservation_id}",
    response_model=ReservationResponse,
    summary="Get reservation details",
)
def get_reservation(
    reservation_id: str,
    service: ReservationService = Depends(get_service),
) -> ReservationResponse:
    """Get single reservation by ID."""
    res = service.get_reservation(reservation_id)
    return ReservationResponse(
        id=res.id,
        unit_id=res.unit_id,
        requester=res.requester,
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status,
        created_at=res.created_at,
    )


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ReservationResponse,
    summary="Cancel reservation",
)
def cancel_reservation(
    reservation_id: str,
    service: ReservationService = Depends(get_service),
) -> ReservationResponse:
    """Cancel a reservation and immediately release its time slot."""
    res = service.cancel_reservation(reservation_id)
    return ReservationResponse(
        id=res.id,
        unit_id=res.unit_id,
        requester=res.requester,
        start_time=res.start_time,
        end_time=res.end_time,
        status=res.status,
        created_at=res.created_at,
    )


@router.get("/availability", summary="Check availability")
def check_availability(
    start_time: datetime = Query(..., description="Start of the interval in ISO 8601"),
    end_time: datetime = Query(..., description="End of the interval in ISO 8601"),
    unit_id: str | None = Query(None, description="Optional unit ID to check specific availability"),
    service: ReservationService = Depends(get_service),
) -> AvailabilityCheckResponse | AvailableUnitsResponse:
    """Check availability across all units or for a specific unit in a given time slot."""
    if unit_id is not None:
        is_available = service.check_unit_availability(unit_id, start_time, end_time)
        return AvailabilityCheckResponse(unit_id=unit_id, available=is_available)

    available_units = service.get_available_units(start_time, end_time)
    return AvailableUnitsResponse(
        available_units=[
            EquipmentUnitResponse(unit_id=u.unit_id, name=u.name)
            for u in available_units
        ]
    )
