"""Integration tests for FastAPI endpoints."""

from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from lab_reservations.api.app import create_app
from lab_reservations.api.dependencies import get_service
from lab_reservations.domain.service import ReservationService
from lab_reservations.infrastructure.sqlite_repository import SQLiteReservationRepository


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "api_test.db"
    repo = SQLiteReservationRepository(db_path=db_path)
    test_service = ReservationService(repository=repo)

    app = create_app()
    app.dependency_overrides[get_service] = lambda: test_service
    return TestClient(app)


def test_api_list_inventory(client: TestClient) -> None:
    response = client.get("/inventory")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    unit_ids = {u["unit_id"] for u in data}
    assert unit_ids == {"MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"}


def test_api_create_reservation_success(client: TestClient) -> None:
    payload = {
        "unit_id": "MIC-01",
        "requester": "Rosalind Franklin",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["unit_id"] == "MIC-01"
    assert body["requester"] == "Rosalind Franklin"
    assert body["status"] == "ACTIVE"
    assert "id" in body


def test_api_create_reservation_rejects_unknown_unit(client: TestClient) -> None:
    payload = {
        "unit_id": "INVALID-99",
        "requester": "Rosalind",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 404
    assert response.json()["error_type"] == "UNIT_NOT_FOUND"


def test_api_create_reservation_rejects_empty_requester(client: TestClient) -> None:
    payload = {
        "unit_id": "MIC-01",
        "requester": "   ",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 400
    assert response.json()["error_type"] == "EMPTY_REQUESTER"


def test_api_create_reservation_rejects_inverted_time(client: TestClient) -> None:
    payload = {
        "unit_id": "MIC-01",
        "requester": "Rosalind",
        "start_time": "2026-11-01T14:00:00Z",
        "end_time": "2026-11-01T10:00:00Z",
    }
    response = client.post("/reservations", json=payload)
    assert response.status_code == 400
    assert response.json()["error_type"] == "INVALID_TIME_RANGE"


def test_api_concurrency_overlap_and_consecutive_boundaries(client: TestClient) -> None:
    # 1. Create first reservation: 10:00 to 11:00 on MIC-01
    res1 = client.post("/reservations", json={
        "unit_id": "MIC-01",
        "requester": "Alice",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T11:00:00Z",
    })
    assert res1.status_code == 201

    # 2. Overlapping reservation on same unit: 10:30 to 11:30 -> Conflict 409
    res_overlap = client.post("/reservations", json={
        "unit_id": "MIC-01",
        "requester": "Bob",
        "start_time": "2026-11-01T10:30:00Z",
        "end_time": "2026-11-01T11:30:00Z",
    })
    assert res_overlap.status_code == 409
    assert res_overlap.json()["error_type"] == "RESERVATION_OVERLAP"

    # 3. Consecutive boundary on same unit: 11:00 to 12:00 -> Success 201
    res_consecutive = client.post("/reservations", json={
        "unit_id": "MIC-01",
        "requester": "Charlie",
        "start_time": "2026-11-01T11:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    })
    assert res_consecutive.status_code == 201

    # 4. Simultaneous reservation on DIFFERENT unit (MIC-02): 10:00 to 11:00 -> Success 201
    res_diff_unit = client.post("/reservations", json={
        "unit_id": "MIC-02",
        "requester": "Dana",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T11:00:00Z",
    })
    assert res_diff_unit.status_code == 201


def test_api_cancel_and_free_slot(client: TestClient) -> None:
    res = client.post("/reservations", json={
        "unit_id": "OSC-01",
        "requester": "Alice",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    }).json()
    res_id = res["id"]

    # Cancel reservation
    cancel_res = client.post(f"/reservations/{res_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Second cancel returns 409
    cancel_again = client.post(f"/reservations/{res_id}/cancel")
    assert cancel_again.status_code == 409
    assert cancel_again.json()["error_type"] == "ALREADY_CANCELLED"

    # Slot is now free for another reservation
    new_res = client.post("/reservations", json={
        "unit_id": "OSC-01",
        "requester": "Bob",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    })
    assert new_res.status_code == 201


def test_api_check_availability(client: TestClient) -> None:
    client.post("/reservations", json={
        "unit_id": "MUL-01",
        "requester": "Alice",
        "start_time": "2026-11-01T10:00:00Z",
        "end_time": "2026-11-01T12:00:00Z",
    })

    # Check MUL-01 specific availability
    check_mul = client.get(
        "/availability?unit_id=MUL-01&start_time=2026-11-01T10:00:00Z&end_time=2026-11-01T12:00:00Z"
    )
    assert check_mul.status_code == 200
    assert check_mul.json()["available"] is False

    # Check MUL-01 consecutive availability (12:00 to 14:00)
    check_mul_consecutive = client.get(
        "/availability?unit_id=MUL-01&start_time=2026-11-01T12:00:00Z&end_time=2026-11-01T14:00:00Z"
    )
    assert check_mul_consecutive.status_code == 200
    assert check_mul_consecutive.json()["available"] is True

    # Check general available units list
    all_avail = client.get(
        "/availability?start_time=2026-11-01T10:00:00Z&end_time=2026-11-01T12:00:00Z"
    )
    assert all_avail.status_code == 200
    available_units = {u["unit_id"] for u in all_avail.json()["available_units"]}
    assert "MUL-01" not in available_units
    assert "MIC-01" in available_units
