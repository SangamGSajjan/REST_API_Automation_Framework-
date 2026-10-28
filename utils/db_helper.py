"""
Database Helper Module for Backend Database Validation using SQL Queries.
Simulates and validates backend relational database persistence for REST API operations.
Uses Python's standard sqlite3 library to execute SQL queries.
"""
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.logger import logger


class DatabaseHelper:
    """
    Manages database connection and executes SQL queries
    to confirm API operations reflect expected backend data changes.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_dir = Path(__file__).resolve().parent.parent / "test_data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_dir / "backend_test.db")
        else:
            self.db_path = db_path

        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with dictionary-like row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self) -> None:
        """Initialize the backend bookings database table schema."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            totalprice INTEGER NOT NULL,
            depositpaid INTEGER NOT NULL,
            checkin_date TEXT NOT NULL,
            checkout_date TEXT NOT NULL,
            additionalneeds TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self._get_connection() as conn:
            conn.execute(create_table_sql)
            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT SQL query and return rows as a list of dictionaries.
        Logs the executed query for test audit trail.
        """
        logger.debug(f"[SQL QUERY] {query} | Params: {params}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """Execute INSERT, UPDATE, or DELETE SQL statement and return affected rows."""
        logger.debug(f"[SQL EXEC] {sql} | Params: {params}")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.rowcount

    def sync_booking_record(self, booking_id: int, payload: Dict[str, Any]) -> None:
        """
        Record API transaction in backend database to simulate/mirror
        the backend persistence layer of the Restful-Booker API.
        """
        insert_or_replace_sql = """
        INSERT OR REPLACE INTO bookings (
            booking_id, firstname, lastname, totalprice, depositpaid,
            checkin_date, checkout_date, additionalneeds, status, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP);
        """
        dates = payload.get("bookingdates", {})
        params = (
            booking_id,
            payload.get("firstname"),
            payload.get("lastname"),
            payload.get("totalprice"),
            1 if payload.get("depositpaid") else 0,
            dates.get("checkin", "2026-01-01"),
            dates.get("checkout", "2026-01-05"),
            payload.get("additionalneeds", ""),
        )
        self.execute_update(insert_or_replace_sql, params)
        logger.info(f"[DB SYNC] Persisted booking ID {booking_id} into backend database.")

    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Fetch booking record by ID using SQL SELECT query."""
        sql = "SELECT * FROM bookings WHERE booking_id = ?;"
        results = self.execute_query(sql, (booking_id,))
        return results[0] if results else None

    def delete_booking_record(self, booking_id: int) -> int:
        """Delete booking record by ID using SQL DELETE query."""
        sql = "DELETE FROM bookings WHERE booking_id = ?;"
        affected = self.execute_update(sql, (booking_id,))
        logger.info(f"[DB DELETE] Removed booking ID {booking_id} from backend DB (rows: {affected}).")
        return affected

    def verify_booking_in_db(self, booking_id: int, expected_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate backend database row against expected API payload.
        Confirms that API operation accurately reflected in the database.
        """
        sql = """
        SELECT booking_id, firstname, lastname, totalprice, depositpaid,
               checkin_date, checkout_date, additionalneeds, status
        FROM bookings
        WHERE booking_id = ?;
        """
        results = self.execute_query(sql, (booking_id,))
        assert len(results) == 1, (
            f"DB Validation Failed! Expected 1 record for booking_id={booking_id}, found {len(results)}"
        )

        db_row = results[0]
        logger.info(f"[DB VERIFY] Found database row for booking ID {booking_id}: {db_row}")

        # Assert database column values match API payload
        assert db_row["firstname"] == expected_payload["firstname"], (
            f"DB Mismatch: 'firstname' expected {expected_payload['firstname']}, got {db_row['firstname']}"
        )
        assert db_row["lastname"] == expected_payload["lastname"], (
            f"DB Mismatch: 'lastname' expected {expected_payload['lastname']}, got {db_row['lastname']}"
        )
        assert db_row["totalprice"] == expected_payload["totalprice"], (
            f"DB Mismatch: 'totalprice' expected {expected_payload['totalprice']}, got {db_row['totalprice']}"
        )
        assert bool(db_row["depositpaid"]) == bool(expected_payload["depositpaid"]), (
            f"DB Mismatch: 'depositpaid' expected {expected_payload['depositpaid']}, got {bool(db_row['depositpaid'])}"
        )

        if "bookingdates" in expected_payload:
            assert db_row["checkin_date"] == expected_payload["bookingdates"]["checkin"], (
                f"DB Mismatch: 'checkin_date' expected {expected_payload['bookingdates']['checkin']}, got {db_row['checkin_date']}"
            )
            assert db_row["checkout_date"] == expected_payload["bookingdates"]["checkout"], (
                f"DB Mismatch: 'checkout_date' expected {expected_payload['bookingdates']['checkout']}, got {db_row['checkout_date']}"
            )

        logger.info(f"[DB VERIFY SUCCESS] Database record matches API operation for ID: {booking_id}")
        return db_row

    def clean_all_test_records(self) -> None:
        """Clean all records from test database."""
        self.execute_update("DELETE FROM bookings;")


# Singleton instance
db_helper = DatabaseHelper()
