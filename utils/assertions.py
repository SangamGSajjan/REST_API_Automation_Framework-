"""Custom assertion helpers for robust API contract, headers, and latency validation."""
from typing import Any, Dict, List, Type, Union
import requests
from pydantic import BaseModel, ValidationError
from utils.logger import logger


def assert_status_code(actual_code: int, expected_code: int, response_body: Any = None) -> None:
    """Verify HTTP status code with diagnostic error details."""
    assert actual_code == expected_code, (
        f"Status Code Mismatch! Expected: {expected_code}, Got: {actual_code}. "
        f"Response snippet: {str(response_body)[:300]}"
    )


def assert_response_time(elapsed_seconds: float, max_allowed_ms: float = 3000.0) -> None:
    """Verify API latency is within SLA threshold (in milliseconds)."""
    elapsed_ms = elapsed_seconds * 1000.0
    logger.debug(f"API Latency: {elapsed_ms:.2f}ms (Max threshold: {max_allowed_ms}ms)")
    assert elapsed_ms <= max_allowed_ms, (
        f"SLA Violation! API took {elapsed_ms:.2f}ms which exceeded threshold of {max_allowed_ms}ms"
    )


def assert_header(
    response: requests.Response,
    header_name: str,
    expected_value: str,
    case_sensitive: bool = False,
) -> None:
    """
    Verify that an HTTP response contains an expected header and matches its value.
    Supports substring match (e.g., verifying 'application/json' in 'application/json; charset=utf-8').
    """
    actual_value = response.headers.get(header_name)
    assert actual_value is not None, (
        f"Header '{header_name}' missing from response headers: {dict(response.headers)}"
    )

    actual_cmp = actual_value if case_sensitive else actual_value.lower()
    expected_cmp = expected_value if case_sensitive else expected_value.lower()

    assert expected_cmp in actual_cmp, (
        f"Header mismatch for '{header_name}'! Expected substring '{expected_value}', got: '{actual_value}'"
    )
    logger.debug(f"Verified header '{header_name}': {actual_value}")


def assert_contains_keys(data: Dict[str, Any], required_keys: List[str]) -> None:
    """Verify that all required keys are present in JSON response."""
    missing_keys = [k for k in required_keys if k not in data]
    assert not missing_keys, f"Response JSON missing required keys: {missing_keys}"


def assert_json_field(data: Dict[str, Any], key: str, expected_val: Any) -> None:
    """Verify specific JSON field matches expected value."""
    assert key in data, f"Key '{key}' not found in JSON response: {data}"
    actual_val = data[key]
    assert actual_val == expected_val, (
        f"Field '{key}' mismatch! Expected: {expected_val} ({type(expected_val).__name__}), "
        f"Got: {actual_val} ({type(actual_val).__name__})"
    )


def assert_schema_valid(data: Union[Dict[str, Any], List[Any]], model_class: Type[BaseModel]) -> BaseModel:
    """
    Validate JSON payload against a Pydantic schema model.
    Catches type errors, missing fields, and contract drifts.
    """
    try:
        if isinstance(data, list):
            validated = [model_class.model_validate(item) for item in data]
            return validated
        return model_class.model_validate(data)
    except ValidationError as err:
        logger.error(f"Schema Contract Violation against {model_class.__name__}: {err.json()}")
        raise AssertionError(f"Schema validation failed for {model_class.__name__}: {err}") from err
