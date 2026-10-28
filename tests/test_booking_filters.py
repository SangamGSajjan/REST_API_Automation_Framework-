"""
Test Suite: Query Parameter Filtering and Data-Driven Testing (DDT).
Authored from a QA testing perspective: validating search/filter parameters,
headers, data fidelity across query filters, and externalized JSON data-driven test cases.
"""
import pytest
from clients.booking_client import BookingClient
from models.booking_models import BookingIdItem
from utils.assertions import (
    assert_status_code,
    assert_header,
    assert_schema_valid,
    assert_json_field,
)
from utils.data_generator import data_gen
from utils.logger import logger


@pytest.mark.filter
class TestBookingFilters:
    """Demonstrates query param filtering and externalized Data-Driven Testing (DDT)."""

    @pytest.mark.smoke
    def test_TC_FILTER01_get_all_booking_ids(self, api_client: BookingClient):
        """
        [TC-FILTER-01] Verify GET /booking returns a valid list of booking IDs matching schema and headers.
        """
        logger.info("Executing TC-FILTER-01: Get all booking IDs...")
        response = api_client.get_booking_ids()

        assert_status_code(response.status_code, 200, response.text)
        assert_header(response, "Content-Type", "application/json")

        json_data = response.json()
        assert isinstance(json_data, list), "Response body should be a list"
        assert len(json_data) > 0, "Expected at least one booking ID"

        # Validate sample items against schema
        assert_schema_valid(json_data[:10], BookingIdItem)
        logger.info(f"TC-FILTER-01 Passed: Retrieved {len(json_data)} booking IDs.")

    @pytest.mark.regression
    def test_TC_FILTER02_filter_bookings_by_name(
        self,
        api_client: BookingClient,
        auth_token: str,
    ):
        """
        [TC-FILTER-02] Filter by Query Params: Create a booking with a unique name,
        then query GET /booking?firstname=...&lastname=... and verify that the created
        booking ID is present in the filtered result set.
        """
        unique_firstname = f"Test{data_gen.generate_booking_payload()['firstname']}"
        unique_lastname = f"Filter{data_gen.generate_booking_payload()['lastname']}"

        payload = data_gen.generate_booking_payload(
            firstname=unique_firstname,
            lastname=unique_lastname,
        )
        create_resp = api_client.create_booking(payload)
        assert_status_code(create_resp.status_code, 200)
        assert_header(create_resp, "Content-Type", "application/json")

        booking_id = create_resp.json()["bookingid"]
        logger.info(f"Executing TC-FILTER-02: Created booking {booking_id} with name '{unique_firstname} {unique_lastname}'")

        try:
            # Query by firstname and lastname
            query_params = {
                "firstname": unique_firstname,
                "lastname": unique_lastname,
            }
            filter_resp = api_client.get_booking_ids(params=query_params)
            assert_status_code(filter_resp.status_code, 200)
            assert_header(filter_resp, "Content-Type", "application/json")

            results = filter_resp.json()
            returned_ids = [item["bookingid"] for item in results]
            logger.info(f"Filtered IDs matching '{unique_firstname}': {returned_ids}")

            assert booking_id in returned_ids, (
                f"Created booking ID {booking_id} was not returned in query results: {returned_ids}"
            )
            logger.info(f"TC-FILTER-02 Passed: Booking ID {booking_id} accurately returned by filter query.")
        finally:
            # Teardown
            api_client.delete_booking(booking_id, token=auth_token)

    @pytest.mark.regression
    def test_TC_FILTER03_data_driven_booking_creation(
        self,
        api_client: BookingClient,
        ddt_booking_payloads: list,
        auth_token: str,
    ):
        """
        [TC-FILTER-03] Data-Driven Testing (DDT): Iterates through external test datasets
        from test_data/booking_payloads.json, creating and asserting each scenario.
        Demonstrates how manual test data matrices are automated in Pytest.
        """
        logger.info(f"Executing TC-FILTER-03 DDT: Running {len(ddt_booking_payloads)} test scenarios...")

        for entry in ddt_booking_payloads:
            scenario_name = entry["scenario"]
            payload = entry["payload"]
            logger.info(f"Running DDT scenario: '{scenario_name}'")

            response = api_client.create_booking(payload)
            assert_status_code(response.status_code, 200, response.text)
            assert_header(response, "Content-Type", "application/json")

            created_body = response.json()
            booking_id = created_body["bookingid"]
            booking_info = created_body["booking"]

            # Field-level verification
            assert_json_field(booking_info, "firstname", payload["firstname"])
            assert_json_field(booking_info, "totalprice", payload["totalprice"])
            assert_json_field(booking_info, "depositpaid", payload["depositpaid"])

            # Teardown current iteration
            del_resp = api_client.delete_booking(booking_id, token=auth_token)
            assert_status_code(del_resp.status_code, 201)
            logger.info(f"DDT scenario '{scenario_name}' passed and cleaned up ID {booking_id}.")
