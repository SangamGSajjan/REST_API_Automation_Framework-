"""Pytest fixtures configuration file providing API clients, auth tokens, database helper, test data, and teardown."""
import json
from pathlib import Path
from typing import Generator, Dict, Any
import pytest

from clients.booking_client import BookingClient
from utils.data_generator import data_gen
from utils.logger import logger
from utils.db_helper import db_helper, DatabaseHelper


@pytest.fixture(scope="session")
def api_client() -> BookingClient:
    """Session-scoped Requests HTTP client for executing REST API calls."""
    client = BookingClient()
    logger.info("Initialized session-scoped BookingClient (Requests engine)")
    return client


@pytest.fixture(scope="session")
def auth_token(api_client: BookingClient) -> str:
    """
    Session-scoped authentication token.
    Authenticates once per test session to optimize test run execution speed,
    similar to setting a collection-level environment variable in Postman.
    """
    logger.info("Requesting authentication token for test session...")
    response = api_client.create_token()
    assert response.status_code == 200, f"Auth failed with status {response.status_code}: {response.text}"
    token_val = response.json().get("token")
    assert token_val, "Token key missing in auth response!"
    logger.info("Successfully acquired session auth token.")
    return token_val


@pytest.fixture(scope="function")
def authenticated_client(api_client: BookingClient, auth_token: str) -> BookingClient:
    """Client pre-configured with auth token in cookies for secure endpoints."""
    api_client.set_auth_token(auth_token)
    yield api_client
    api_client.clear_auth()


@pytest.fixture(scope="session")
def db_service() -> DatabaseHelper:
    """Session-scoped database helper for SQL query execution and DB validation."""
    logger.info("Initialized DatabaseHelper for backend SQL validation.")
    return db_helper


@pytest.fixture(scope="function")
def created_booking(
    api_client: BookingClient,
    auth_token: str,
    db_service: DatabaseHelper,
) -> Generator[Dict[str, Any], None, None]:
    """
    Test Data Setup and Teardown Fixture:
    1. [SETUP] Creates a fresh dynamic booking record before the test runs.
    2. [SYNC] Syncs record into backend test DB to mirror backend persistence.
    3. [YIELD] Passes booking details and booking ID to the test case.
    4. [TEARDOWN] Automatically deletes the booking from both API and DB post-execution.
    Ensures zero test data residue and keeps the environment clean.
    """
    payload = data_gen.generate_booking_payload()
    response = api_client.create_booking(payload)
    assert response.status_code == 200, f"Failed to setup booking: {response.text}"

    created_data = response.json()
    booking_id = created_data["bookingid"]
    logger.info(f"[SETUP] Created temporary test booking ID: {booking_id}")

    # Mirror to backend DB for end-to-end data validation
    db_service.sync_booking_record(booking_id, payload)

    yield {
        "booking_id": booking_id,
        "booking": created_data["booking"],
        "payload": payload,
    }

    # Teardown logic
    logger.info(f"[TEARDOWN] Cleaning up temporary test booking ID: {booking_id}")
    del_resp = api_client.delete_booking(booking_id, token=auth_token)
    db_service.delete_booking_record(booking_id)
    if del_resp.status_code in [201, 200, 204]:
        logger.info(f"[TEARDOWN SUCCESS] Successfully removed booking ID: {booking_id}")
    else:
        logger.warning(f"[TEARDOWN WARNING] Teardown returned unexpected status {del_resp.status_code}")


@pytest.fixture(scope="session")
def ddt_booking_payloads() -> list:
    """Load positive test datasets from JSON file for Data-Driven Testing (DDT)."""
    data_file = Path(__file__).resolve().parent.parent / "test_data" / "booking_payloads.json"
    with open(data_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def ddt_negative_payloads() -> list:
    """Load negative test datasets from JSON file for negative / boundary testing."""
    data_file = Path(__file__).resolve().parent.parent / "test_data" / "negative_payloads.json"
    if data_file.exists():
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# --- Pytest Report Customization Hooks ---
def pytest_html_report_title(report):
    """Customize HTML Report title."""
    report.title = "REST API Automation Test Report (Python + Requests + Pytest)"
