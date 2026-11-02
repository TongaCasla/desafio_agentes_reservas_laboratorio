"""FastAPI application factory and global domain exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from lab_reservations.api.routes import router
from lab_reservations.domain.exceptions import (
    EmptyRequesterError,
    InvalidTimeRangeError,
    ReservationAlreadyCancelledError,
    ReservationNotFoundError,
    ReservationOverlapError,
    UnitNotFoundError,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Laboratory Equipment Reservation API",
        version="1.0.0",
        description="Clean-architecture local API for managing laboratory equipment reservations.",
    )

    @app.exception_handler(UnitNotFoundError)
    async def unit_not_found_handler(request: Request, exc: UnitNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "UNIT_NOT_FOUND"},
        )

    @app.exception_handler(ReservationNotFoundError)
    async def reservation_not_found_handler(request: Request, exc: ReservationNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "RESERVATION_NOT_FOUND"},
        )

    @app.exception_handler(EmptyRequesterError)
    async def empty_requester_handler(request: Request, exc: EmptyRequesterError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "error_type": "EMPTY_REQUESTER"},
        )

    @app.exception_handler(InvalidTimeRangeError)
    async def invalid_time_range_handler(request: Request, exc: InvalidTimeRangeError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "error_type": "INVALID_TIME_RANGE"},
        )

    @app.exception_handler(ReservationOverlapError)
    async def overlap_handler(request: Request, exc: ReservationOverlapError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "RESERVATION_OVERLAP"},
        )

    @app.exception_handler(ReservationAlreadyCancelledError)
    async def already_cancelled_handler(request: Request, exc: ReservationAlreadyCancelledError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "ALREADY_CANCELLED"},
        )

    app.include_router(router)
    return app


app = create_app()
