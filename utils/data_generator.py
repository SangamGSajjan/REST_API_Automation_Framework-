"""Dynamic test data generator using Faker with random fallbacks."""
import random
from datetime import datetime, timedelta
from typing import Any, Dict

try:
    from faker import Faker
    fake = Faker()
except ImportError:
    # Graceful fallback if Faker is not yet installed
    class FakeFallback:
        def first_name(self) -> str:
            return random.choice(["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Casey"])

        def last_name(self) -> str:
            return random.choice(["Smith", "Doe", "Johnson", "Brown", "Davis", "Wilson"])

        def random_int(self, min_val: int = 50, max_val: int = 500) -> int:
            return random.randint(min_val, max_val)

        def boolean(self) -> bool:
            return random.choice([True, False])

        def sentence(self, nb_words: int = 3) -> str:
            return "Breakfast included"

    fake = FakeFallback()  # type: ignore


class DataGenerator:
    """Generates valid and boundary booking payloads for API testing."""

    @staticmethod
    def generate_booking_payload(
        firstname: str = None,
        lastname: str = None,
        totalprice: int = None,
        depositpaid: bool = None,
        checkin_offset_days: int = 1,
        checkout_offset_days: int = 5,
        additionalneeds: str = None,
    ) -> Dict[str, Any]:
        """Generate a valid, randomized booking payload."""
        today = datetime.now()
        checkin_date = (today + timedelta(days=checkin_offset_days)).strftime("%Y-%m-%d")
        checkout_date = (today + timedelta(days=checkout_offset_days)).strftime("%Y-%m-%d")

        return {
            "firstname": firstname if firstname is not None else fake.first_name(),
            "lastname": lastname if lastname is not None else fake.last_name(),
            "totalprice": totalprice if totalprice is not None else random.randint(100, 1000),
            "depositpaid": depositpaid if depositpaid is not None else True,
            "bookingdates": {
                "checkin": checkin_date,
                "checkout": checkout_date,
            },
            "additionalneeds": additionalneeds if additionalneeds is not None else "Breakfast & Airport Shuttle",
        }

    @staticmethod
    def generate_invalid_booking_payloads() -> list:
        """
        Generate negative and boundary payloads for edge case testing.
        Used for @pytest.mark.parametrize.
        """
        valid = DataGenerator.generate_booking_payload()
        return [
            # Missing firstname
            ({k: v for k, v in valid.items() if k != "firstname"}, "missing_firstname"),
            # Negative total price
            ({**valid, "totalprice": -150}, "negative_price"),
            # Invalid date format
            ({**valid, "bookingdates": {"checkin": "invalid-date", "checkout": "2026-99-99"}}, "invalid_dates"),
            # Non-boolean depositpaid
            ({**valid, "depositpaid": "not_a_bool"}, "invalid_depositpaid_type"),
        ]


data_gen = DataGenerator()
