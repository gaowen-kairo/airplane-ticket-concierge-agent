"""Tools for the Airplane Ticket Concierge Agent.

This module defines custom tool functions available to the SkyConcierge AI agent.
All reservation and state-changing actions interact asynchronously with the persistent SQLite database.
"""

import asyncio
from typing import Optional
from google.antigravity import ToolContext

from database import (
    async_cancel_booking,
    async_get_booking,
    async_get_flight,
    async_reserve_ticket,
    async_search_flights,
)
from memory import (
    compact_conversation_memory,
    recall_user_preferences,
    save_user_preference,
)


def search_flights(
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
    matches = asyncio.run(async_search_flights(origin, destination, cabin_class))

    if not matches:
        return (
            f"No direct flights found from {origin.upper()} to {destination.upper()} on {departure_date} "
            f"for cabin class '{cabin_class}'."
        )

    results = [
        f"Found {len(matches)} flight(s) from {origin.upper()} to {destination.upper()} on {departure_date}:"
    ]
    for flight in matches:
        open_seats_str = ", ".join(flight["available_seats"]) if flight["available_seats"] else "None (Sold Out)"
        results.append(
            f"- Flight {flight['flight_number']} ({flight['airline']}): "
            f"Departs {flight['departure_time']} -> Arrives {flight['arrival_time']} "
            f"({flight['duration']}) | Class: {flight['cabin_class'].title()} | "
            f"Price: ${flight['price_usd']:.2f} | Available Seats: {open_seats_str}"
        )

    if return_date:
        results.append(f"\nNote: Return trip for {return_date} will be searched separately.")

    return "\n".join(results)


def get_flight_details(flight_number: str) -> str:
    """Retrieves full details for a specific flight by flight number from database.

    Args:
        flight_number: Flight code string (e.g., 'AA-101', 'UA-405').
    """
    flight = asyncio.run(async_get_flight(flight_number))
    if not flight:
        return f"Flight number {flight_number} not found in the flight schedules database."

    open_seats = ", ".join(flight["available_seats"]) if flight["available_seats"] else "Sold Out"
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


def check_seat_map(flight_number: str) -> str:
    """Displays seat availability map for a specific flight.

    Args:
        flight_number: Flight code string (e.g., 'AA-101').
    """
    flight = asyncio.run(async_get_flight(flight_number))
    if not flight:
        return f"Flight {flight_number} not found."

    seats = flight["available_seats"]
    seats_str = ", ".join(seats) if seats else "No open seats remaining"
    return (
        f"Seat Map for Flight {flight['flight_number']} ({flight['airline']}):\n"
        f"Available Seats: {seats_str}\n"
        f"Cabin: {flight['cabin_class'].title()}"
    )


def reserve_ticket(
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
    try:
        record = asyncio.run(async_reserve_ticket(flight_number, passenger_name, passport_number, seat_number))
    except Exception as e:
        return f"Error creating reservation: {e}"

    if ctx:
        user_bookings = ctx.get_state("user_bookings", [])
        user_bookings.append(record)
        ctx.set_state("user_bookings", user_bookings)

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


def get_booking_details(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Retrieves details of an existing ticket reservation from persistent database by PNR.

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext.
    """
    record = asyncio.run(async_get_booking(booking_reference))

    if record:
        return (
            f"Persistent Booking Record for PNR {record['booking_reference']}:\n"
            f"Passenger: {record['passenger_name']}\n"
            f"Passport No: {record['passport_number']}\n"
            f"Flight: {record['flight_number']} ({record['airline']})\n"
            f"Route: {record['route']}\n"
            f"Seat: {record['seat_number']}\n"
            f"Status: {record['status']}\n"
            f"Amount Paid: ${record['price_paid_usd']:.2f}\n"
            f"Created At: {record.get('created_at', 'N/A')}"
        )

    return f"No persistent booking record found for reference '{booking_reference}' in database."


def cancel_booking(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Cancels an existing ticket booking by PNR in persistent database.

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext.
    """
    try:
        record = asyncio.run(async_cancel_booking(booking_reference))
        return (
            f"Booking {record['booking_reference']} for passenger {record['passenger_name']} "
            f"has been CANCELLED in database. Seat {record['seat_number']} restored to flight inventory."
        )
    except Exception as e:
        return f"Unable to cancel: {e}"


def calculate_baggage_fees(
    cabin_class: str = "economy",
    checked_bags: int = 1,
) -> str:
    """Calculates checked baggage allowances and estimated baggage fees.

    Args:
        cabin_class: Travel cabin class ('economy', 'premium economy', 'business', 'first').
        checked_bags: Total number of checked bags.
    """
    class_clean = cabin_class.strip().lower()

    if class_clean in ("business", "first"):
        included_bags = 2
        fee_per_extra_bag = 50.0
    elif class_clean == "premium economy":
        included_bags = 2
        fee_per_extra_bag = 40.0
    else:
        included_bags = 1
        fee_per_extra_bag = 35.0

    if checked_bags <= included_bags:
        return (
            f"For {cabin_class.title()} class, {included_bags} checked bag(s) are included free of charge. "
            f"Total baggage fee: $0.00."
        )

    extra = checked_bags - included_bags
    total_fee = extra * fee_per_extra_bag

    return (
        f"Baggage Policy for {cabin_class.title()} Class:\n"
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
