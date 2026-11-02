"""Pydantic schemas for API request and response serialization."""

from datetime import datetime
from pydantic import BaseModel, Field

from lab_reservations.domain.models import ReservationStatus


class EquipmentUnitResponse(BaseModel):
    unit_id: str
    name: str


class ReservationCreateRequest(BaseModel):
    unit_id: str = Field(..., description="ID of the equipment unit (e.g. MIC-01)")
    requester: str = Field(..., description="Name of the person requesting the reservation")
    start_time: datetime = Field(..., description="ISO 8601 start timestamp")
    end_time: datetime = Field(..., description="ISO 8601 end timestamp")


class ReservationResponse(BaseModel):
    id: str
    unit_id: str
    requester: str
    start_time: datetime
    end_time: datetime
    status: ReservationStatus
    created_at: datetime


class AvailabilityCheckResponse(BaseModel):
    unit_id: str
    available: bool


class AvailableUnitsResponse(BaseModel):
    available_units: list[EquipmentUnitResponse]
