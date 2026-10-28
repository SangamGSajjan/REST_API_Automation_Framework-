"""Custom logger utility with cURL generation for easy debugging."""
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional


def get_logger(name: str = "api_framework") -> logging.Logger:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # Create reports/logs directory if it doesn't exist
        log_dir = Path(__file__).resolve().parent.parent / "reports"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "test_execution.log"

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File Handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = get_logger("API_Test_Suite")


def curlify_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate an executable cURL command from request parameters.
    Allows SDETs and developers to instantly reproduce failed calls in terminal or Postman.
    """
    parts = ["curl", "-X", method.upper()]

    if headers:
        for k, v in headers.items():
            parts.extend(["-H", f'"{k}: {v}"'])

    if json_data:
        import json
        body = json.dumps(json_data).replace('"', '\\"')
        parts.extend(["-d", f'"{body}"'])

    # Append query parameters if any
    final_url = url
    if params:
        from urllib.parse import urlencode
        query_string = urlencode(params)
        final_url = f"{url}?{query_string}"

    parts.append(f'"{final_url}"')
    return " ".join(parts)
