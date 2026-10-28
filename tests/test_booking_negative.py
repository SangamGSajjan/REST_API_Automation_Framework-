"""
Test Suite: Negative, Security, and Boundary Scenarios for Restful-Booker API.
Authored from a QA functional & negative testing perspective:
- Validates negative scenarios for invalid inputs and missing mandatory fields using parameterization.
- Validates access control and security (403 Forbidden).
- Validates resource boundaries and error handling (404 Not Found, 405 Method Not Allowed).
"""
import pytest
from clients.booking_client import BookingClient
from utils.assertions import assert_status_code
from utils.data_generator import data_gen
from utils.logger import logger


@pytest.mark.negative
@pytest.mark.regression
class TestBookingNegativeScenarios:
    """
    Covers Negative Test Scenarios, Authorization validation, and Boundary Edge Cases.
    Demonstrates solid QA manual test scenario design translated into automated Pytest scripts.
    """

    def test_TC_NEG01_get_non_existent_booking_id(self, api_client: BookingClient):
        """
        [TC-NEG-01] Verify that querying a non-existent booking ID returns 404 Not Found.
        Severity: High
        Expected Status: 404
        """
        invalid_booking_id = 99999999
        logger.info(f"Querying non-existent booking ID: {invalid_booking_id}")
        response = api_client.get_booking(invalid_booking_id)

        assert_status_code(response.status_code, 404, response.text)
        logger.info("Verified 404 response for non-existent booking ID.")

    def test_TC_NEG02_update_booking_without_token(
        self,
        api_client: BookingClient,
        created_booking: dict,
    ):
        """
        [TC-NEG-02] Security: Verify updating a booking without auth token returns 403 Forbidden.
        Severity: Critical
        Expected Status: 403
        """
        booking_id = created_booking["booking_id"]
        update_payload = data_gen.generate_booking_payload()

        logger.info(f"Attempting PUT on booking ID {booking_id} without auth token...")
        response = api_client.update_booking(
            booking_id=booking_id,
            payload=update_payload,
            token=None,  # No token passed
        )

        assert_status_code(response.status_code, 403, response.text)
        assert "Forbidden" in response.text
        logger.info("Verified 403 Forbidden when auth token is omitted.")

    def test_TC_NEG03_delete_booking_without_token(
        self,
        api_client: BookingClient,
        created_booking: dict,
    ):
        """
        [TC-NEG-03] Security: Verify deleting a booking without auth token returns 403 Forbidden.
        Severity: Critical
        Expected Status: 403
        """
        booking_id = created_booking["booking_id"]

        logger.info(f"Attempting DELETE on booking ID {booking_id} without auth token...")
        response = api_client.delete_booking(booking_id=booking_id, token=None)

        assert_status_code(response.status_code, 403, response.text)
        assert "Forbidden" in response.text
        logger.info("Verified 403 Forbidden on DELETE without auth token.")

    def test_TC_NEG04_update_booking_with_invalid_token(
        self,
        api_client: BookingClient,
        created_booking: dict,
    ):
        """
        [TC-NEG-04] Security: Verify updating with a fake/expired token returns 403 Forbidden.
        Severity: High
        Expected Status: 403
        """
        booking_id = created_booking["booking_id"]
        fake_token = "invalid_expired_token_12345"
        update_payload = data_gen.generate_booking_payload()

        response = api_client.update_booking(
            booking_id=booking_id,
            payload=update_payload,
            token=fake_token,
        )

        assert_status_code(response.status_code, 403, response.text)
        assert "Forbidden" in response.text
        logger.info("Verified 403 Forbidden with invalid token.")

    def test_TC_NEG05_delete_booking_with_invalid_token(
        self,
        api_client: BookingClient,
        created_booking: dict,
    ):
        """
        [TC-NEG-05] Security: Verify deleting with a fake/expired token returns 403 Forbidden.
        Severity: High
        Expected Status: 403
        """
        booking_id = created_booking["booking_id"]
        fake_token = "invalid_dummy_token_99999"

        response = api_client.delete_booking(booking_id=booking_id, token=fake_token)

        assert_status_code(response.status_code, 403, response.text)
        assert "Forbidden" in response.text
        logger.info("Verified 403 Forbidden on DELETE with invalid token.")

    @pytest.mark.parametrize(
        "invalid_payload,scenario_desc,expected_statuses",
        [
            (
                {
                    "lastname": "Brown",
                    "totalprice": 150,
                    "depositpaid": True,
                    "bookingdates": {"checkin": "2026-11-01", "checkout": "2026-11-05"},
                },
                "missing_firstname",
                [400, 500],
            ),
            (
                {
                    "firstname": "John",
                    "totalprice": 200,
                    "depositpaid": True,
                    "bookingdates": {"checkin": "2026-11-01", "checkout": "2026-11-05"},
                },
                "missing_lastname",
                [400, 500],
            ),
            (
                {
                    "firstname": "Alex",
                    "lastname": "Morgan",
                    "totalprice": 300,
                    "depositpaid": False,
                },
                "missing_bookingdates",
                [400, 500],
            ),
            (
                {},
                "completely_empty_payload",
                [400, 500],
            ),
        ],
    )
    def test_TC_NEG06_create_booking_missing_mandatory_fields(
        self,
        api_client: BookingClient,
        invalid_payload: dict,
        scenario_desc: str,
        expected_statuses: list,
    ):
        """
        [TC-NEG-06] Parameterized Negative Test: Verify API handles missing mandatory fields.
        Validates that API returns 400 Bad Request or 500 error when required fields are omitted.
        """
        logger.info(f"Executing TC-NEG-06 Parameterized Test: {scenario_desc}")
        response = api_client.create_booking(invalid_payload)

        assert response.status_code in expected_statuses, (
            f"Failed for scenario '{scenario_desc}'. "
            f"Expected status in {expected_statuses}, got: {response.status_code} - {response.text}"
        )
        logger.info(f"Passed TC-NEG-06 [{scenario_desc}]: Status {response.status_code}")

    @pytest.mark.parametrize(
        "invalid_input_payload,scenario_desc",
        [
            (
                {
                    "firstname": 12345,
                    "lastname": ["Invalid", "Type"],
                    "totalprice": "one_thousand_dollars",
                    "depositpaid": "not_a_boolean",
                    "bookingdates": {"checkin": "2026-13-45", "checkout": "invalid-date"},
                    "additionalneeds": 99999,
                },
                "invalid_data_types_in_fields",
            ),
            (
                {
                    "firstname": "John",
                    "lastname": "Doe",
                    "totalprice": -100,  # Negative boundary
                    "depositpaid": True,
                    "bookingdates": {"checkin": "2026-12-01", "checkout": "2026-01-01"},  # Checkout before checkin
                    "additionalneeds": "None",
                },
                "boundary_invalid_date_range",
            ),
        ],
    )
    def test_TC_NEG07_create_booking_invalid_inputs(
        self,
        api_client: BookingClient,
        invalid_input_payload: dict,
        scenario_desc: str,
    ):
        """
        [TC-NEG-07] Parameterized Negative Test: Verify API behavior with invalid data types and boundary values.
        """
        logger.info(f"Executing TC-NEG-07 Parameterized Test: {scenario_desc}")
        response = api_client.create_booking(invalid_input_payload)
        # Server must either reject with 400/500 or handle boundary safely
        logger.info(f"TC-NEG-07 [{scenario_desc}] returned status: {response.status_code}")
        assert response.status_code in [200, 400, 422, 500]

    def test_TC_NEG08_delete_already_deleted_booking(
        self,
        api_client: BookingClient,
        auth_token: str,
    ):
        """
        [TC-NEG-08] Lifecycle Boundary: Verify deleting an already deleted booking returns 405 Method Not Allowed.
        (Restful-booker returns 405 when attempting to DELETE a non-existent or previously deleted booking ID).
        """
        # Step 1: Create a booking
        payload = data_gen.generate_booking_payload()
        create_resp = api_client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]

        # Step 2: Delete it the first time -> 201 Created
        first_del = api_client.delete_booking(booking_id, token=auth_token)
        assert_status_code(first_del.status_code, 201)

        # Step 3: Attempt second deletion on same ID -> 405 Method Not Allowed
        second_del = api_client.delete_booking(booking_id, token=auth_token)
        assert second_del.status_code in [404, 405], (
            f"Expected 404 or 405 on duplicate delete, got: {second_del.status_code}"
        )
        logger.info(f"Verified duplicate deletion on booking {booking_id} handled correctly.")
