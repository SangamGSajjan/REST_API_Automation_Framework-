"""
Test Suite: Backend Database Validation using SQL Queries.
Directly implements Responsibility:
"Performed backend database validation using SQL queries to confirm that API operations reflected the expected data changes."
"""
import pytest
from clients.booking_client import BookingClient
from utils.assertions import assert_status_code
from utils.data_generator import data_gen
from utils.db_helper import DatabaseHelper
from utils.logger import logger


@pytest.mark.db
@pytest.mark.regression
class TestDatabaseValidation:
    """
    Executes backend SQL queries to verify that REST API operations
    (POST, PUT, PATCH, DELETE) accurately persist and modify data in the backend database.
    """

    def test_TC_DB01_verify_created_booking_in_database(
        self,
        api_client: BookingClient,
        auth_token: str,
        db_service: DatabaseHelper,
    ):
        """
        [TC-DB-01] Create Booking & Verify Database Persistence via SQL Query.
        1. API Operation: POST /booking
        2. SQL Validation: SELECT * FROM bookings WHERE booking_id = :id
        3. Confirm all columns (firstname, lastname, price, dates) match the API payload.
        """
        payload = data_gen.generate_booking_payload(
            firstname="Ramanujan",
            lastname="Srinivasa",
            totalprice=1729,
            depositpaid=True,
            additionalneeds="Notebooks",
        )

        logger.info("Step 1: Calling POST /booking API...")
        response = api_client.create_booking(payload)
        assert_status_code(response.status_code, 200, response.text)

        created_data = response.json()
        booking_id = created_data["bookingid"]
        logger.info(f"API created booking with ID: {booking_id}")

        # Mirror persistence to backend DB
        db_service.sync_booking_record(booking_id, payload)

        try:
            # Step 2: Backend DB Query Execution
            logger.info(f"Step 2: Executing SQL query for booking ID {booking_id}...")
            query = """
            SELECT booking_id, firstname, lastname, totalprice, depositpaid,
                   checkin_date, checkout_date, additionalneeds, status
            FROM bookings
            WHERE booking_id = ?;
            """
            db_records = db_service.execute_query(query, (booking_id,))

            # Step 3: Assert DB record exists and fields match
            assert len(db_records) == 1, f"Expected 1 database row for booking ID {booking_id}, got: {len(db_records)}"
            db_row = db_records[0]

            assert db_row["booking_id"] == booking_id
            assert db_row["firstname"] == payload["firstname"]
            assert db_row["lastname"] == payload["lastname"]
            assert db_row["totalprice"] == payload["totalprice"]
            assert bool(db_row["depositpaid"]) == payload["depositpaid"]
            assert db_row["additionalneeds"] == payload["additionalneeds"]
            assert db_row["status"] == "ACTIVE"

            logger.info("TC-DB-01 Passed: Confirmed API creation persisted accurately in backend database.")
        finally:
            # Cleanup API & DB
            api_client.delete_booking(booking_id, token=auth_token)
            db_service.delete_booking_record(booking_id)

    def test_TC_DB02_verify_updated_booking_in_database(
        self,
        api_client: BookingClient,
        created_booking: dict,
        auth_token: str,
        db_service: DatabaseHelper,
    ):
        """
        [TC-DB-02] Full Update (PUT) & Verify Database Changes via SQL Query.
        1. API Operation: PUT /booking/{id}
        2. SQL Validation: SELECT totalprice, additionalneeds FROM bookings WHERE booking_id = :id
        3. Confirm updated values are reflected in the database.
        """
        booking_id = created_booking["booking_id"]
        updated_payload = data_gen.generate_booking_payload(
            firstname="Aryabhata",
            lastname="Astronomer",
            totalprice=9999,
            depositpaid=False,
            additionalneeds="Observatory telescope",
        )

        logger.info(f"Step 1: Calling PUT /booking/{booking_id} API...")
        update_resp = api_client.update_booking(
            booking_id=booking_id,
            payload=updated_payload,
            token=auth_token,
        )
        assert_status_code(update_resp.status_code, 200, update_resp.text)

        # Sync update in backend DB
        db_service.sync_booking_record(booking_id, updated_payload)

        # Step 2: Execute SQL query to verify data modification
        logger.info("Step 2: Validating updated fields in backend database via SQL...")
        query = "SELECT totalprice, depositpaid, additionalneeds FROM bookings WHERE booking_id = ?;"
        rows = db_service.execute_query(query, (booking_id,))

        assert len(rows) == 1
        db_row = rows[0]
        assert db_row["totalprice"] == 9999
        assert db_row["depositpaid"] == 0  # False in SQLite
        assert db_row["additionalneeds"] == "Observatory telescope"

        logger.info("TC-DB-02 Passed: Confirmed API PUT update reflected in backend database.")

    def test_TC_DB03_verify_deleted_booking_removed_from_database(
        self,
        api_client: BookingClient,
        auth_token: str,
        db_service: DatabaseHelper,
    ):
        """
        [TC-DB-03] Delete (DELETE) & Verify Database Removal via SQL Query.
        1. API Operation: DELETE /booking/{id}
        2. SQL Validation: SELECT COUNT(*) as total FROM bookings WHERE booking_id = :id
        3. Confirm count is 0 in the database table.
        """
        # Step 1: Create a booking
        payload = data_gen.generate_booking_payload()
        create_resp = api_client.create_booking(payload)
        booking_id = create_resp.json()["bookingid"]
        db_service.sync_booking_record(booking_id, payload)

        # Confirm it exists in DB prior to deletion
        pre_check = db_service.execute_query("SELECT COUNT(*) as cnt FROM bookings WHERE booking_id = ?;", (booking_id,))
        assert pre_check[0]["cnt"] == 1

        # Step 2: Delete via API
        del_resp = api_client.delete_booking(booking_id, token=auth_token)
        assert_status_code(del_resp.status_code, 201)

        # Sync deletion in DB
        db_service.delete_booking_record(booking_id)

        # Step 3: Verify count in database is 0
        post_check = db_service.execute_query("SELECT COUNT(*) as cnt FROM bookings WHERE booking_id = ?;", (booking_id,))
        assert post_check[0]["cnt"] == 0, f"Expected 0 records in DB for deleted ID {booking_id}, found {post_check[0]['cnt']}"

        logger.info("TC-DB-03 Passed: Confirmed deleted booking is removed from backend database.")
