"""Tools for the Airplane Ticket Concierge Agent.

Includes strict Pydantic argument validation, structured LLM error recovery guidance,
Intent vs. Outcome logging, PII redaction, and database persistence.
"""

import asyncio
import time
from typing import Optional
from google.antigravity import ToolContext

from database import (
    async_cancel_booking,
    async_get_booking,
    async_get_flight,
    async_reserve_ticket,
    async_search_flights,
)
from logging_tracing import log_tool_intent_and_outcome
from memory import (
    compact_conversation_memory,
    recall_user_preferences,
    save_user_preference,
)
from schemas import (
    BaggageCalculationInput,
    BookingCancelInput,
    BookingDetailsInput,
    ErrorResponseWithRecovery,
    FlightDetailsInput,
    FlightSearchInput,
    SeatMapInput,
    TicketReservationInput,
)


async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    cabin_class: str = "economy",
) -> str:
    """Searches for available airplane flights matching origin, destination, and class from database.

    Args:
        origin: 3-letter IATA airport code for origin (e.g., 'SFO', 'LAX', 'JFK').
        destination: 3-letter IATA airport code for destination (e.g., 'JFK', 'ORD', 'LHR').
        departure_date: Departure date in YYYY-MM-DD format.
        return_date: Optional return date in YYYY-MM-DD format for round trips.
        cabin_class: Cabin class preference ('economy', 'premium economy', 'business', 'first', or 'any').
    """
    start_time = time.time()
    # 1. Pydantic Strict Argument Validation
    try:
        validated = FlightSearchInput(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            cabin_class=cabin_class,
        )
    except Exception as err:
        duration_ms = (time.time() - start_time) * 1000
        error_resp = ErrorResponseWithRecovery(
            error_code="INVALID_SEARCH_PARAMETERS",
            message=str(err),
            recovery_guidance="Please provide a valid 3-letter IATA airport code for origin and destination (e.g., 'SFO', 'JFK') and a date formatted as YYYY-MM-DD.",
            valid_options=["SFO", "JFK", "LAX", "ORD", "LHR"],
        )
        log_tool_intent_and_outcome(
            intent="SEARCH_FLIGHTS", action="search_flights", outcome="VALIDATION_FAILED",
            duration_ms=duration_ms, payload={"origin": origin, "destination": destination}
        )
        return error_resp.to_formatted_str()

    matches = await async_search_flights(validated.origin, validated.destination, validated.cabin_class)
    duration_ms = (time.time() - start_time) * 1000

    if not matches:
        error_resp = ErrorResponseWithRecovery(
            error_code="NO_FLIGHTS_FOUND",
            message=f"No direct flights found from {validated.origin} to {validated.destination} on {validated.departure_date} for cabin class '{validated.cabin_class}'.",
            recovery_guidance="Try broadening your search by setting cabin_class='any' or searching alternative nearby hubs (e.g. SFO, LAX, JFK, ORD, LHR).",
            valid_options=["SFO -> JFK", "LAX -> ORD", "JFK -> LHR"],
        )
        log_tool_intent_and_outcome(
            intent="SEARCH_FLIGHTS", action="search_flights", outcome="NO_MATCHES",
            duration_ms=duration_ms, payload=validated.model_dump()
        )
        return error_resp.to_formatted_str()

    results = [
        f"Found {len(matches)} flight(s) from {validated.origin} to {validated.destination} on {validated.departure_date}:"
    ]
    for flight in matches:
        open_seats_str = ", ".join(flight["available_seats"]) if flight["available_seats"] else "None (Sold Out)"
        results.append(
            f"- Flight {flight['flight_number']} ({flight['airline']}): "
            f"Departs {flight['departure_time']} -> Arrives {flight['arrival_time']} "
            f"({flight['duration']}) | Class: {flight['cabin_class'].title()} | "
            f"Price: ${flight['price_usd']:.2f} | Available Seats: {open_seats_str}"
        )

    if validated.return_date:
        results.append(f"\nNote: Return trip for {validated.return_date} will be searched separately.")

    log_tool_intent_and_outcome(
        intent="SEARCH_FLIGHTS", action="search_flights", outcome="SUCCESS",
        duration_ms=duration_ms, payload=validated.model_dump()
    )
    return "\n".join(results)


async def get_flight_details(flight_number: str) -> str:
    """Retrieves full details for a specific flight by flight number from database.

    Args:
        flight_number: Flight code string (e.g., 'AA-101', 'UA-405').
    """
    start_time = time.time()
    try:
        validated = FlightDetailsInput(flight_number=flight_number)
    except Exception as err:
        duration_ms = (time.time() - start_time) * 1000
        error_resp = ErrorResponseWithRecovery(
            error_code="INVALID_FLIGHT_CODE_FORMAT",
            message=str(err),
            recovery_guidance="Please specify a valid flight code format like 'AA-101' or 'UA-405'.",
            valid_options=["AA-101", "AA-202", "UA-405", "DL-882", "BA-178"],
        )
        return error_resp.to_formatted_str()

    flight = await async_get_flight(validated.flight_number)
    duration_ms = (time.time() - start_time) * 1000

    if not flight:
        error_resp = ErrorResponseWithRecovery(
            error_code="FLIGHT_NOT_FOUND",
            message=f"Flight number {validated.flight_number} not found in the flight schedules database.",
            recovery_guidance="Verify the flight number string. Supported flight numbers are AA-101, AA-202, UA-405, DL-882, BA-178.",
            valid_options=["AA-101", "AA-202", "UA-405", "DL-882", "BA-178"],
        )
        return error_resp.to_formatted_str()

    open_seats = ", ".join(flight["available_seats"]) if flight["available_seats"] else "Sold Out"
    log_tool_intent_and_outcome(
        intent="GET_FLIGHT_DETAILS", action="get_flight_details", outcome="SUCCESS",
        duration_ms=duration_ms, payload=validated.model_dump()
    )
    return (
        f"Flight Details for {flight['flight_number']}:\n"
        f"Airline: {flight['airline']}\n"
        f"Route: {flight['origin']} -> {flight['destination']}\n"
        f"Schedule: Departs {flight['departure_time']}, Arrives {flight['arrival_time']}\n"
        f"Duration: {flight['duration']}\n"
        f"Cabin Class: {flight['cabin_class'].title()}\n"
        f"Price: ${flight['price_usd']:.2f}\n"
        f"Seats Open: {open_seats}"
    )


async def check_seat_map(flight_number: str) -> str:
    """Displays seat availability map for a specific flight.

    Args:
        flight_number: Flight code string (e.g., 'AA-101').
    """
    flight = await async_get_flight(flight_number)
    if not flight:
        error_resp = ErrorResponseWithRecovery(
            error_code="FLIGHT_NOT_FOUND",
            message=f"Flight {flight_number} not found.",
            recovery_guidance="Please search for valid flights first before checking seat maps.",
            valid_options=["AA-101", "UA-405", "DL-882"],
        )
        return error_resp.to_formatted_str()

    seats = flight["available_seats"]
    seats_str = ", ".join(seats) if seats else "No open seats remaining"
    return (
        f"Seat Map for Flight {flight['flight_number']} ({flight['airline']}):\n"
        f"Available Seats: {seats_str}\n"
        f"Cabin: {flight['cabin_class'].title()}"
    )


async def reserve_ticket(
    flight_number: str,
    passenger_name: str,
    passport_number: str,
    seat_number: Optional[str] = None,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Reserves an airplane ticket for a passenger and persists record in SQLite database.

    Args:
        flight_number: Flight code string (e.g., 'AA-101').
        passenger_name: Full legal name of the passenger.
        passport_number: Passport or identification number.
        seat_number: Optional preferred seat from available seats.
        ctx: Injected ToolContext for maintaining session state.
    """
    start_time = time.time()
    # 1. Pydantic Strict Argument & Passport Validation
    try:
        validated = TicketReservationInput(
            flight_number=flight_number,
            passenger_name=passenger_name,
            passport_number=passport_number,
            seat_number=seat_number,
        )
    except Exception as err:
        duration_ms = (time.time() - start_time) * 1000
        error_resp = ErrorResponseWithRecovery(
            error_code="RESERVATION_VALIDATION_ERROR",
            message=str(err),
            recovery_guidance="Ensure passenger_name is a valid full name and passport_number is 6 to 12 alphanumeric characters.",
        )
        log_tool_intent_and_outcome(
            intent="RESERVE_TICKET", action="reserve_ticket", outcome="VALIDATION_FAILED",
            duration_ms=duration_ms, payload={"flight_number": flight_number, "passenger_name": passenger_name, "passport_number": passport_number}
        )
        return error_resp.to_formatted_str()

    try:
        record = await async_reserve_ticket(
            validated.flight_number, validated.passenger_name, validated.passport_number, validated.seat_number
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_resp = ErrorResponseWithRecovery(
            error_code="RESERVATION_FAILED",
            message=str(e),
            recovery_guidance="Check if the selected seat is open using check_seat_map or pick another open seat.",
        )
        log_tool_intent_and_outcome(
            intent="RESERVE_TICKET", action="reserve_ticket", outcome="FAILED",
            duration_ms=duration_ms, payload=validated.model_dump()
        )
        return error_resp.to_formatted_str()

    duration_ms = (time.time() - start_time) * 1000
    if ctx:
        user_bookings = ctx.get_state("user_bookings", [])
        user_bookings.append(record)
        ctx.set_state("user_bookings", user_bookings)

    # Log intent vs outcome with PII Redaction
    log_tool_intent_and_outcome(
        intent="RESERVE_TICKET", action="reserve_ticket", outcome="SUCCESS",
        duration_ms=duration_ms, payload=record
    )

    return (
        f"Ticket successfully reserved and persisted in database!\n"
        f"Booking Reference (PNR): {record['booking_reference']}\n"
        f"Passenger: {record['passenger_name']}\n"
        f"Flight: {record['flight_number']} ({record['airline']})\n"
        f"Route: {record['route']}\n"
        f"Seat: {record['seat_number']}\n"
        f"Total Paid: ${record['price_paid_usd']:.2f}\n"
        f"Status: CONFIRMED"
    )


async def get_booking_details(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Retrieves details of an existing ticket reservation from persistent database by PNR.

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext.
    """
    try:
        validated = BookingDetailsInput(booking_reference=booking_reference)
    except Exception as err:
        error_resp = ErrorResponseWithRecovery(
            error_code="INVALID_PNR_FORMAT",
            message=str(err),
            recovery_guidance="Please provide a valid 6-character uppercase PNR code (e.g. 'A1B2C3').",
        )
        return error_resp.to_formatted_str()

    record = await async_get_booking(validated.booking_reference)

    if record:
        return (
            f"Persistent Booking Record for PNR {record['booking_reference']}:\n"
            f"Passenger: {record['passenger_name']}\n"
            f"Flight: {record['flight_number']} ({record['airline']})\n"
            f"Route: {record['route']}\n"
            f"Seat: {record['seat_number']}\n"
            f"Status: {record['status']}\n"
            f"Amount Paid: ${record['price_paid_usd']:.2f}\n"
            f"Created At: {record.get('created_at', 'N/A')}"
        )

    error_resp = ErrorResponseWithRecovery(
        error_code="BOOKING_NOT_FOUND",
        message=f"No persistent booking record found for reference '{validated.booking_reference}' in database.",
        recovery_guidance="Check if the PNR reference code was mistyped or make a new reservation.",
    )
    return error_resp.to_formatted_str()


async def cancel_booking(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Cancels an existing ticket booking by PNR in persistent database.

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext.
    """
    try:
        validated = BookingCancelInput(booking_reference=booking_reference)
    except Exception as err:
        error_resp = ErrorResponseWithRecovery(
            error_code="INVALID_PNR_FORMAT",
            message=str(err),
            recovery_guidance="Provide a 6-character alphanumeric PNR reference to cancel.",
        )
        return error_resp.to_formatted_str()

    try:
        record = await async_cancel_booking(validated.booking_reference)
        return (
            f"Booking {record['booking_reference']} for passenger {record['passenger_name']} "
            f"has been CANCELLED in database. Seat {record['seat_number']} restored to flight inventory."
        )
    except Exception as e:
        error_resp = ErrorResponseWithRecovery(
            error_code="CANCELLATION_FAILED",
            message=str(e),
            recovery_guidance="Ensure the PNR reference exists in active session bookings.",
        )
        return error_resp.to_formatted_str()


def calculate_baggage_fees(
    cabin_class: str = "economy",
    checked_bags: int = 1,
) -> str:
    """Calculates checked baggage allowances and estimated baggage fees.

    Args:
        cabin_class: Travel cabin class ('economy', 'premium economy', 'business', 'first').
        checked_bags: Total number of checked bags.
    """
    try:
        validated = BaggageCalculationInput(cabin_class=cabin_class, checked_bags=checked_bags)
    except Exception as err:
        error_resp = ErrorResponseWithRecovery(
            error_code="INVALID_BAGGAGE_INPUT",
            message=str(err),
            recovery_guidance="Specify checked_bags as a non-negative integer.",
        )
        return error_resp.to_formatted_str()

    class_clean = validated.cabin_class.strip().lower()

    if class_clean in ("business", "first"):
        included_bags = 2
        fee_per_extra_bag = 50.0
    elif class_clean == "premium economy":
        included_bags = 2
        fee_per_extra_bag = 40.0
    else:
        included_bags = 1
        fee_per_extra_bag = 35.0

    if validated.checked_bags <= included_bags:
        return (
            f"For {validated.cabin_class.title()} class, {included_bags} checked bag(s) are included free of charge. "
            f"Total baggage fee: $0.00."
        )

    extra = validated.checked_bags - included_bags
    total_fee = extra * fee_per_extra_bag

    return (
        f"Baggage Policy for {validated.cabin_class.title()} Class:\n"
        f"Included Bags: {included_bags}\n"
        f"Extra Checked Bags: {extra}\n"
        f"Fee per Extra Bag: ${fee_per_extra_bag:.2f}\n"
        f"Total Checked Baggage Fee: ${total_fee:.2f}"
    )


ALL_TOOLS = [
    search_flights,
    get_flight_details,
    check_seat_map,
    reserve_ticket,
    get_booking_details,
    cancel_booking,
    calculate_baggage_fees,
    save_user_preference,
    recall_user_preferences,
    compact_conversation_memory,
]
