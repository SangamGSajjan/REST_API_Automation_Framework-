"""
Test Suite: Authentication Endpoints (POST /auth).
Authored from a QA testing perspective: validating positive token generation,
invalid credentials handling, HTTP headers, response bodies, and response schema contracts.
"""
import pytest
from clients.booking_client import BookingClient
from models.booking_models import AuthTokenResponse
from utils.assertions import (
    assert_status_code,
    assert_response_time,
    assert_header,
    assert_schema_valid,
    assert_contains_keys,
    assert_json_field,
)
from utils.logger import logger


@pytest.mark.auth
class TestAuthentication:
    """Covers Positive, Negative, and Schema Contract tests for /auth."""

    @pytest.mark.smoke
    def test_TC_AUTH01_token_generation_success(self, api_client: BookingClient):
        """
        [TC-AUTH-01] Positive: Verify auth token is successfully generated with valid credentials.
        Validates HTTP 200, Content-Type header, response latency (< 3000ms), schema contract, and non-empty token string.
        """
        logger.info("Executing TC-AUTH-01: Valid credentials authentication...")
        response = api_client.create_token(username="admin", password="password123")

        # 1. Assert HTTP Status Code
        assert_status_code(response.status_code, 200, response.text)

        # 2. Assert Response Headers
        assert_header(response, "Content-Type", "application/json")

        # 3. Assert Response Time SLA (< 3000ms)
        assert_response_time(response.elapsed.total_seconds(), max_allowed_ms=3000)

        # 4. Assert JSON response body contains token key
        json_body = response.json()
        assert_contains_keys(json_body, ["token"])

        # 5. Strict Pydantic Schema Validation
        validated = assert_schema_valid(json_body, AuthTokenResponse)
        assert len(validated.token) > 0, "Token string must not be empty"
        logger.info(f"Verified valid auth token generation: {validated.token[:6]}***")

    @pytest.mark.regression
    @pytest.mark.parametrize(
        "invalid_user,invalid_pass,desc",
        [
            ("invalid_user", "password123", "incorrect_username"),
            ("admin", "wrong_password_999", "incorrect_password"),
            ("", "", "empty_credentials"),
            ("admin", "", "empty_password"),
        ],
    )
    def test_TC_AUTH02_invalid_credentials_rejected(
        self,
        api_client: BookingClient,
        invalid_user: str,
        invalid_pass: str,
        desc: str,
    ):
        """
        [TC-AUTH-02] Negative: Verify /auth rejects unauthorized credentials.
        Validates HTTP 200, Content-Type header, and response body containing {'reason': 'Bad credentials'}.
        """
        logger.info(f"Executing TC-AUTH-02 Negative Auth Test: {desc}")
        response = api_client.create_token(username=invalid_user, password=invalid_pass)

        # Assert Status Code & Headers
        assert_status_code(response.status_code, 200, response.text)
        assert_header(response, "Content-Type", "application/json")

        json_body = response.json()
        # Assert JSON fields and expected error reason
        assert_contains_keys(json_body, ["reason"])
        assert_json_field(json_body, "reason", "Bad credentials")
        assert "token" not in json_body, "Security violation: Token returned for bad credentials!"
        logger.info(f"TC-AUTH-02 Passed for scenario: {desc}")
