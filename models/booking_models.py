"""Pydantic models for contract and schema validation of Restful-Booker API."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BookingDates(BaseModel):
    """Schema for booking date range."""
    model_config = ConfigDict(extra="ignore")

    checkin: str = Field(description="Check-in date in YYYY-MM-DD format")
    checkout: str = Field(description="Check-out date in YYYY-MM-DD format")


class BookingModel(BaseModel):
    """Schema representing a complete booking entity."""
    model_config = ConfigDict(extra="ignore")

    firstname: str = Field(min_length=1)
    lastname: str = Field(min_length=1)
    totalprice: int = Field(ge=0)
    depositpaid: bool
    bookingdates: BookingDates
    additionalneeds: Optional[str] = None


class BookingResponseModel(BaseModel):
    """Schema returned by POST /booking."""
    model_config = ConfigDict(extra="ignore")

    bookingid: int = Field(gt=0)
    booking: BookingModel


class BookingIdItem(BaseModel):
    """Schema for items in GET /booking list."""
    model_config = ConfigDict(extra="ignore")

    bookingid: int = Field(gt=0)


class AuthTokenResponse(BaseModel):
    """Schema returned by POST /auth."""
    model_config = ConfigDict(extra="ignore")

    token: str = Field(min_length=10)
