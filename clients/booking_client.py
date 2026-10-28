"""Service object encapsulating Restful-Booker API endpoints."""
from typing import Any, Dict, Optional
import requests

from config.settings import settings
from clients.base_client import BaseHttpClient


class BookingClient(BaseHttpClient):
    """
    API Service Object for Restful-Booker service.
    Implements the API Object Model design pattern.
    """

    def __init__(self, base_url: Optional[str] = None):
        super().__init__(base_url=base_url)

    def health_check(self) -> requests.Response:
        """Ping endpoint to verify API availability."""
        return self.get(settings.PING_ENDPOINT)

    def create_token(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> requests.Response:
        """Generate authentication token via POST /auth."""
        payload = {
            "username": username or settings.API_USERNAME,
            "password": password or settings.API_PASSWORD,
        }
        return self.post(settings.AUTH_ENDPOINT, json=payload)

    def get_booking_ids(self, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Retrieve booking IDs with optional query filters (firstname, lastname, checkin, checkout)."""
        return self.get(settings.BOOKING_ENDPOINT, params=params)

    def get_booking(self, booking_id: int, headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Fetch details of a single booking by ID."""
        return self.get(f"{settings.BOOKING_ENDPOINT}/{booking_id}", headers=headers)

    def create_booking(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Create a new booking via POST /booking."""
        return self.post(settings.BOOKING_ENDPOINT, json=payload, headers=headers)

    def update_booking(
        self,
        booking_id: int,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Full update of booking details via PUT /booking/{id}."""
        req_headers = dict(headers or {})
        if token:
            req_headers["Cookie"] = f"token={token}"
        return self.put(f"{settings.BOOKING_ENDPOINT}/{booking_id}", json=payload, headers=req_headers)

    def partial_update_booking(
        self,
        booking_id: int,
        payload: Dict[str, Any],
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Partial update of booking details via PATCH /booking/{id}."""
        req_headers = dict(headers or {})
        if token:
            req_headers["Cookie"] = f"token={token}"
        return self.patch(f"{settings.BOOKING_ENDPOINT}/{booking_id}", json=payload, headers=req_headers)

    def delete_booking(
        self,
        booking_id: int,
        token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        """Delete booking record via DELETE /booking/{id}."""
        req_headers = dict(headers or {})
        if token:
            req_headers["Cookie"] = f"token={token}"
        return self.delete(f"{settings.BOOKING_ENDPOINT}/{booking_id}", headers=req_headers)
