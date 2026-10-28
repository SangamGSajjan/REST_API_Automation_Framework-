"""
Test Suite: CRUD Lifecycle for Bookings (Create, Read, Update, Delete).
Authored from a QA testing perspective: validating full resource lifecycle,
HTTP status codes, response headers, JSON fields, schema contracts, and post-teardown verification.
"""
import pytest
from clients.booking_client import BookingClient
from models.booking_models import BookingModel, BookingResponseModel
from utils.data_generator import data_gen
from utils.assertions import (
    assert_status_code,
    assert_response_time,
    assert_header,
    assert_schema_valid,
    assert_json_field,
)
from utils.logger import logger


@pytest.mark.crud
class TestBookingCRUD:
    """Complete End-to-End lifecycle testing of booking resources."""

    @pytest.mark.smoke
    def test_TC_CRUD01_health_check_ping(self, api_client: BookingClient):
        """
        [TC-CRUD-01] Sanity/Smoke: Verify the API service is up and healthy.
        GET /ping returns HTTP 201 Created.
        """
        logger.info("Executing TC-CRUD-01: Health check ping...")
        response = api_client.health_check()
        assert_status_code(response.status_code, 201, response.text)
        assert response.text.strip() == "Created"
        logger.info("TC-CRUD-01 Passed: API service is alive.")

    @pytest.mark.smoke
    def test_TC_CRUD02_create_booking_success(self, api_client: BookingClient, auth_token: str):
        """
        [TC-CRUD-02] Create: Verify creating a new booking with dynamic valid payload.
        Ensures HTTP 200, Content-Type header, response SLA, schema contract, and deep field matching.
        Cleans up test data immediately after verification.
        """
        logger.info("Executing TC-CRUD-02: Create booking...")
        payload = data_gen.generate_booking_payload(
            firstname="Nikola",
            lastname="Tesla",
            totalprice=500,
            depositpaid=True,
            additionalneeds="AC power outlet",
        )
        response = api_client.create_booking(payload)

        # 1. Assert HTTP Status code
        assert_status_code(response.status_code, 200, response.text)

        # 2. Assert HTTP Response Headers
        assert_header(response, "Content-Type", "application/json")

        # 3. Assert Response SLA
        assert_response_time(response.elapsed.total_seconds(), max_allowed_ms=3000)

        # 4. Assert response schema contract
        json_body = response.json()
        validated: BookingResponseModel = assert_schema_valid(json_body, BookingResponseModel)

        # 5. Assert individual JSON fields and deep payload fidelity
        created_booking = validated.booking
        assert_json_field(json_body["booking"], "firstname", payload["firstname"])
        assert_json_field(json_body["booking"], "lastname", payload["lastname"])
        assert_json_field(json_body["booking"], "totalprice", payload["totalprice"])
        assert_json_field(json_body["booking"], "depositpaid", payload["depositpaid"])
        assert created_booking.bookingdates.checkin == payload["bookingdates"]["checkin"]
        assert created_booking.bookingdates.checkout == payload["bookingdates"]["checkout"]

        # Teardown: Delete the newly created booking to avoid database clutter
        booking_id = validated.bookingid
        del_resp = api_client.delete_booking(booking_id, token=auth_token)
        assert_status_code(del_resp.status_code, 201, del_resp.text)
        logger.info(f"TC-CRUD-02 Passed: Verified creation and cleaned up booking ID: {booking_id}")

    @pytest.mark.regression
    def test_TC_CRUD03_get_booking_by_id(self, api_client: BookingClient, created_booking: dict):
        """
        [TC-CRUD-03] Read: Verify fetching an existing booking by its unique ID.
        Validates HTTP 200, Content-Type header, JSON response fields, and schema.
        Uses the `created_booking` fixture for automatic setup & teardown.
        """
        booking_id = created_booking["booking_id"]
        expected_payload = created_booking["payload"]
        logger.info(f"Executing TC-CRUD-03: Fetching booking ID {booking_id}...")

        response = api_client.get_booking(booking_id)

        # Assert Status Code & Headers
        assert_status_code(response.status_code, 200, response.text)
        assert_header(response, "Content-Type", "application/json")

        json_body = response.json()

        # Schema contract verification
        validated = assert_schema_valid(json_body, BookingModel)

        # JSON field assertions
        assert_json_field(json_body, "firstname", expected_payload["firstname"])
        assert_json_field(json_body, "lastname", expected_payload["lastname"])
        assert_json_field(json_body, "totalprice", expected_payload["totalprice"])
        assert_json_field(json_body, "depositpaid", expected_payload["depositpaid"])
        logger.info(f"TC-CRUD-03 Passed: Successfully fetched booking {booking_id}")

    @pytest.mark.regression
    def test_TC_CRUD04_full_update_booking_put(
        self,
        api_client: BookingClient,
        created_booking: dict,
        auth_token: str,
    ):
        """
        [TC-CRUD-04] Update (Full PUT): Update entire booking entity with an authentication token.
        Verifies HTTP 200, Content-Type header, and persisted JSON fields.
        """
        booking_id = created_booking["booking_id"]
        logger.info(f"Executing TC-CRUD-04: Full update PUT on booking ID {booking_id}...")

        updated_payload = data_gen.generate_booking_payload(
            firstname="Marie",
            lastname="Curie",
            totalprice=850,
            depositpaid=False,
            additionalneeds="Laboratory access",
        )

        response = api_client.update_booking(
            booking_id=booking_id,
            payload=updated_payload,
            token=auth_token,
        )

        assert_status_code(response.status_code, 200, response.text)
        assert_header(response, "Content-Type", "application/json")

        json_body = response.json()

        # Validate that the values were indeed updated
        validated = assert_schema_valid(json_body, BookingModel)
        assert_json_field(json_body, "firstname", "Marie")
        assert_json_field(json_body, "lastname", "Curie")
        assert_json_field(json_body, "totalprice", 850)
        assert_json_field(json_body, "depositpaid", False)
        assert_json_field(json_body, "additionalneeds", "Laboratory access")
        logger.info(f"TC-CRUD-04 Passed: PUT update persisted successfully for ID: {booking_id}")

    @pytest.mark.regression
    def test_TC_CRUD05_partial_update_booking_patch(
        self,
        api_client: BookingClient,
        created_booking: dict,
        auth_token: str,
    ):
        """
        [TC-CRUD-05] Update (Partial PATCH): Update only specific fields (firstname and totalprice)
        while verifying that untouched fields remain preserved.
        """
        booking_id = created_booking["booking_id"]
        original_booking = created_booking["booking"]
        logger.info(f"Executing TC-CRUD-05: Partial update PATCH on booking ID {booking_id}...")

        patch_payload = {
            "firstname": "Ada",
            "totalprice": 999,
        }

        response = api_client.partial_update_booking(
            booking_id=booking_id,
            payload=patch_payload,
            token=auth_token,
        )

        assert_status_code(response.status_code, 200, response.text)
        assert_header(response, "Content-Type", "application/json")

        json_body = response.json()

        # Assert modified fields changed
        assert_json_field(json_body, "firstname", "Ada")
        assert_json_field(json_body, "totalprice", 999)

        # Assert untouched fields remained original
        assert_json_field(json_body, "lastname", original_booking["lastname"])
        assert_json_field(json_body, "depositpaid", original_booking["depositpaid"])
        assert json_body["bookingdates"]["checkin"] == original_booking["bookingdates"]["checkin"]
        logger.info(f"TC-CRUD-05 Passed: PATCH partial update verified for ID: {booking_id}")

    @pytest.mark.regression
    def test_TC_CRUD06_delete_booking_and_verify_404(
        self,
        api_client: BookingClient,
        auth_token: str,
    ):
        """
        [TC-CRUD-06] Delete & Verify: Create a booking, delete it using token,
        and verify subsequent GET returns 404 Not Found.
        """
        # Step 1: Create fresh booking
        payload = data_gen.generate_booking_payload()
        create_resp = api_client.create_booking(payload)
        assert_status_code(create_resp.status_code, 200)
        booking_id = create_resp.json()["bookingid"]
        logger.info(f"Executing TC-CRUD-06: Created booking {booking_id} for deletion test")

        # Step 2: Delete booking
        delete_resp = api_client.delete_booking(booking_id, token=auth_token)
        assert_status_code(delete_resp.status_code, 201, delete_resp.text)

        # Step 3: Verify GET on deleted ID returns 404 Not Found
        get_resp = api_client.get_booking(booking_id)
        assert_status_code(get_resp.status_code, 404, get_resp.text)
        logger.info(f"TC-CRUD-06 Passed: Booking {booking_id} confirmed deleted with 404.")
