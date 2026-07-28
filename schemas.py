"""Explicit Pydantic JSON Schemas for Strict Argument Validation and Structured Responses.

This module defines Pydantic models for all tool inputs and outputs used across the SkyConcierge system.
Enforces strict type validation, field constraints, and structured error responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import re


# --- Input Validation Schemas ---

class FlightSearchInput(BaseModel):
    """Schema for flight search queries."""
    origin: str = Field(..., description="3-letter IATA origin airport code (e.g., SFO, LAX, JFK)")
    destination: str = Field(..., description="3-letter IATA destination airport code (e.g., JFK, ORD, LHR)")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Optional return date in YYYY-MM-DD format for round trips")
    cabin_class: str = Field("economy", description="Cabin class preference: 'economy', 'premium economy', 'business', 'first', or 'any'")

    @field_validator("origin", "destination")
    @classmethod
    def validate_iata(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v_clean):
            raise ValueError(f"Invalid airport code '{v}'. Must be a 3-letter IATA code (e.g., 'SFO').")
        return v_clean


class FlightDetailsInput(BaseModel):
    """Schema for flight detail requests."""
    flight_number: str = Field(..., description="Flight code identifier (e.g., AA-101, UA-405)")

    @field_validator("flight_number")
    @classmethod
    def validate_flight_code(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9]{2,3}-\d{3,4}$", v_clean):
            raise ValueError(f"Invalid flight number format '{v}'. Expected format like 'AA-101' or 'UA-405'.")
        return v_clean


class SeatMapInput(BaseModel):
    """Schema for seat map queries."""
    flight_number: str = Field(..., description="Flight code identifier (e.g., AA-101)")


class TicketReservationInput(BaseModel):
    """Schema for creating a ticket reservation."""
    flight_number: str = Field(..., description="Flight code identifier (e.g., AA-101)")
    passenger_name: str = Field(..., description="Full legal name of the passenger")
    passport_number: str = Field(..., description="Passenger passport or national ID number")
    seat_number: Optional[str] = Field(None, description="Optional preferred seat code from open seat map (e.g., 12A)")

    @field_validator("passport_number")
    @classmethod
    def validate_passport(cls, v: str) -> str:
        v_clean = v.strip()
        if not re.match(r"^[A-Za-z0-9]{6,12}$", v_clean):
            raise ValueError(f"Invalid passport number '{v}'. Must be 6 to 12 alphanumeric characters.")
        return v_clean

    @field_validator("passenger_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v_clean = v.strip()
        if len(v_clean) < 2:
            raise ValueError("Passenger name must be at least 2 characters long.")
        return v_clean


class BookingDetailsInput(BaseModel):
    """Schema for retrieving booking by PNR."""
    booking_reference: str = Field(..., description="6-character alphanumeric PNR booking code")

    @field_validator("booking_reference")
    @classmethod
    def validate_pnr(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9]{6}$", v_clean):
            raise ValueError(f"Invalid booking reference (PNR) '{v}'. Expected exactly 6 alphanumeric characters.")
        return v_clean


class BookingCancelInput(BaseModel):
    """Schema for cancelling a booking by PNR."""
    booking_reference: str = Field(..., description="6-character alphanumeric PNR booking code")


class BaggageCalculationInput(BaseModel):
    """Schema for calculating baggage fees."""
    cabin_class: str = Field("economy", description="Cabin class: 'economy', 'premium economy', 'business', 'first'")
    checked_bags: int = Field(1, description="Number of checked bags (>= 0)")

    @field_validator("checked_bags")
    @classmethod
    def validate_bags(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Checked bags count cannot be negative.")
        return v


class UserPreferenceInput(BaseModel):
    """Schema for storing user preferences."""
    key: str = Field(..., description="Preference key name (e.g., seat_preference, dietary_req)")
    value: str = Field(..., description="Preference value detail string")


# --- Structured Output Schemas ---

class ErrorResponseWithRecovery(BaseModel):
    """Structured error response containing recovery instructions for the LLM."""
    status: str = "ERROR"
    error_code: str
    message: str
    recovery_guidance: str
    valid_options: Optional[List[str]] = None

    def to_formatted_str(self) -> str:
        options_str = f"\nValid Options: {', '.join(self.valid_options)}" if self.valid_options else ""
        return (
            f"[Error {self.error_code}]: {self.message}\n"
            f"💡 Recovery Guidance for LLM: {self.recovery_guidance}"
            f"{options_str}"
        )
