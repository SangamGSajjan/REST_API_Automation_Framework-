"""Enterprise Base HTTP Client built on top of requests.Session with retries and logging."""
import time
from typing import Any, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config.settings import settings
from utils.logger import logger, curlify_request


class BaseHttpClient:
    """
    Robust HTTP client wrapper handling sessions, retry policies,
    custom headers, response timing, and logging.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.BASE_URL).rstrip("/")
        self.session = requests.Session()
        self._configure_retries()
        self.default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session.headers.update(self.default_headers)

    def _configure_retries(self) -> None:
        """Configure exponential backoff retry strategy for flaky networks."""
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "PUT", "DELETE", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def set_auth_token(self, token: str) -> None:
        """Attach auth cookie token for authenticated routes."""
        self.session.cookies.set("token", token)
        logger.debug(f"Auth token attached to session: {token[:6]}***")

    def set_basic_auth(self, username: str, password: str) -> None:
        """Attach HTTP Basic Authentication."""
        self.session.auth = (username, password)

    def clear_auth(self) -> None:
        """Clear authentication credentials."""
        self.session.cookies.clear()
        self.session.auth = None

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> requests.Response:
        """Centralized dispatcher executing all HTTP requests with observability."""
        url = f"{self.base_url}{endpoint}" if endpoint.startswith("/") else f"{self.base_url}/{endpoint}"
        effective_headers = {**self.session.headers, **(headers or {})}

        # Log cURL representation for instant developer reproduction
        curl_cmd = curlify_request(
            method=method,
            url=url,
            headers=effective_headers,
            json_data=json,
            params=params,
        )
        logger.debug(f"[REQUEST cURL] {curl_cmd}")

        start_time = time.perf_counter()
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout or settings.REQUEST_TIMEOUT,
            **kwargs,
        )
        elapsed_sec = time.perf_counter() - start_time

        # Structured response logging
        logger.info(
            f"[{method.upper()}] {url} -> {response.status_code} "
            f"({elapsed_sec * 1000:.1f}ms) | Size: {len(response.content)} bytes"
        )

        return response

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
