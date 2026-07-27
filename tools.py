"""Tools for the Airplane Ticket Concierge Agent.

This module defines the custom functions available to the concierge agent
for searching flights, retrieving seat maps, making reservations, and managing bookings.
"""

import random
import string
from typing import Optional
from google.antigravity import ToolContext

# In-memory mock database of flight offers
MOCK_FLIGHTS = [
    {
        "flight_number": "AA-101",
        "airline": "American Skyways",
        "origin": "SFO",
        "destination": "JFK",
        "departure_time": "08:00 AM",
        "arrival_time": "04:30 PM",
        "duration": "5h 30m",
        "price_usd": 350.0,
        "cabin_class": "economy",
        "available_seats": ["12A", "12B", "14C", "15D", "18A"],
    },
    {
        "flight_number": "AA-202",
        "airline": "American Skyways",
        "origin": "SFO",
        "destination": "JFK",
        "departure_time": "01:15 PM",
        "arrival_time": "09:45 PM",
        "duration": "5h 30m",
        "price_usd": 720.0,
        "cabin_class": "business",
        "available_seats": ["2A", "2B", "3A", "3F"],
    },
    {
        "flight_number": "UA-405",
        "airline": "United Global",
        "origin": "SFO",
        "destination": "JFK",
        "departure_time": "10:30 AM",
        "arrival_time": "07:00 PM",
        "duration": "5h 30m",
        "price_usd": 310.0,
        "cabin_class": "economy",
        "available_seats": ["10A", "11C", "20E", "22F"],
    },
    {
        "flight_number": "DL-882",
        "airline": "Delta Express",
        "origin": "LAX",
        "destination": "ORD",
        "departure_time": "07:00 AM",
        "arrival_time": "01:15 PM",
        "duration": "4h 15m",
        "price_usd": 280.0,
        "cabin_class": "economy",
        "available_seats": ["8A", "9B", "14D"],
    },
    {
        "flight_number": "BA-178",
        "airline": "British Airways",
        "origin": "JFK",
        "destination": "LHR",
        "departure_time": "06:30 PM",
        "arrival_time": "06:30 AM (+1)",
        "duration": "7h 00m",
        "price_usd": 850.0,
        "cabin_class": "premium economy",
        "available_seats": ["12D", "12E", "14A"],
    },
]


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    cabin_class: str = "economy",
) -> str:
    """Searches for available airplane flights matching origin, destination, and class.

    Args:
        origin: 3-letter IATA airport code for origin (e.g., 'SFO', 'LAX', 'JFK').
        destination: 3-letter IATA airport code for destination (e.g., 'JFK', 'ORD', 'LHR').
        departure_date: Departure date in YYYY-MM-DD format.
        return_date: Optional return date in YYYY-MM-DD format for round trips.
        cabin_class: Cabin class preference ('economy', 'premium economy', 'business', 'first').
    """
    origin_clean = origin.strip().upper()
    dest_clean = destination.strip().upper()
    class_clean = cabin_class.strip().lower()

    matches = [
        f for f in MOCK_FLIGHTS
        if f["origin"] == origin_clean
        and f["destination"] == dest_clean
        and (f["cabin_class"].lower() == class_clean or class_clean == "any")
    ]

    if not matches:
        return (
            f"No direct flights found from {origin_clean} to {dest_clean} on {departure_date} "
            f"for cabin class '{cabin_class}'."
        )

    results = [
        f"Found {len(matches)} flight(s) from {origin_clean} to {dest_clean} on {departure_date}:"
    ]
    for flight in matches:
        results.append(
            f"- Flight {flight['flight_number']} ({flight['airline']}): "
            f"Departs {flight['departure_time']} -> Arrives {flight['arrival_time']} "
            f"({flight['duration']}) | Class: {flight['cabin_class'].title()} | "
            f"Price: ${flight['price_usd']:.2f} | Available Seats: {', '.join(flight['available_seats'])}"
        )

    if return_date:
        results.append(f"\nNote: Return trip for {return_date} will be searched separately.")

    return "\n".join(results)


def get_flight_details(flight_number: str) -> str:
    """Retrieves full details for a specific flight by flight number.

    Args:
        flight_number: Flight code string (e.g., 'AA-101', 'UA-405').
    """
    flight_code = flight_number.strip().upper()
    for flight in MOCK_FLIGHTS:
        if flight["flight_number"] == flight_code:
            return (
                f"Flight Details for {flight['flight_number']}:\n"
                f"Airline: {flight['airline']}\n"
                f"Route: {flight['origin']} -> {flight['destination']}\n"
                f"Schedule: Departs {flight['departure_time']}, Arrives {flight['arrival_time']}\n"
                f"Duration: {flight['duration']}\n"
                f"Cabin Class: {flight['cabin_class'].title()}\n"
                f"Price: ${flight['price_usd']:.2f}\n"
                f"Seats Open: {', '.join(flight['available_seats'])}"
            )

    return f"Flight number {flight_code} not found in the flight schedules database."


def check_seat_map(flight_number: str) -> str:
    """Displays seat availability map for a specific flight.

    Args:
        flight_number: Flight code string (e.g., 'AA-101').
    """
    flight_code = flight_number.strip().upper()
    for flight in MOCK_FLIGHTS:
        if flight["flight_number"] == flight_code:
            seats = flight["available_seats"]
            return (
                f"Seat Map for Flight {flight_code} ({flight['airline']}):\n"
                f"Available Seats: {', '.join(seats)}\n"
                f"Cabin: {flight['cabin_class'].title()}"
            )
    return f"Flight {flight_code} not found."


def reserve_ticket(
    flight_number: str,
    passenger_name: str,
    passport_number: str,
    seat_number: Optional[str] = None,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Reserves an airplane ticket for a passenger on a specified flight.

    Args:
        flight_number: Flight code string (e.g., 'AA-101').
        passenger_name: Full legal name of the passenger.
        passport_number: Passport or identification number.
        seat_number: Optional preferred seat from available seats.
        ctx: Injected ToolContext for maintaining session state.
    """
    flight_code = flight_number.strip().upper()
    target_flight = None

    for flight in MOCK_FLIGHTS:
        if flight["flight_number"] == flight_code:
            target_flight = flight
            break

    if not target_flight:
        return f"Error: Flight {flight_code} does not exist."

    available = target_flight["available_seats"]
    if seat_number:
        seat_clean = seat_number.strip().upper()
        if seat_clean not in available:
            return f"Error: Seat {seat_clean} is not available on flight {flight_code}. Open seats: {', '.join(available)}"
        selected_seat = seat_clean
    else:
        selected_seat = available[0] if available else "14B"

    # Generate PNR / Booking reference
    pnr = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    booking_record = {
        "booking_reference": pnr,
        "flight_number": flight_code,
        "airline": target_flight["airline"],
        "route": f"{target_flight['origin']} -> {target_flight['destination']}",
        "passenger_name": passenger_name,
        "passport_number": passport_number,
        "seat_number": selected_seat,
        "status": "CONFIRMED",
        "price_paid_usd": target_flight["price_usd"],
    }

    if ctx:
        user_bookings = ctx.get_state("user_bookings", [])
        user_bookings.append(booking_record)
        ctx.set_state("user_bookings", user_bookings)

    return (
        f"Ticket successfully reserved!\n"
        f"Booking Reference (PNR): {pnr}\n"
        f"Passenger: {passenger_name}\n"
        f"Flight: {flight_code} ({target_flight['airline']})\n"
        f"Route: {target_flight['origin']} -> {target_flight['destination']}\n"
        f"Seat: {selected_seat}\n"
        f"Total Paid: ${target_flight['price_usd']:.2f}\n"
        f"Status: CONFIRMED"
    )


def get_booking_details(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Retrieves details of an existing ticket reservation by booking reference (PNR).

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext for retrieving session state.
    """
    ref_clean = booking_reference.strip().upper()

    if ctx:
        user_bookings = ctx.get_state("user_bookings", [])
        for booking in user_bookings:
            if booking["booking_reference"] == ref_clean:
                return (
                    f"Booking Record for PNR {ref_clean}:\n"
                    f"Passenger: {booking['passenger_name']}\n"
                    f"Flight: {booking['flight_number']} ({booking['airline']})\n"
                    f"Route: {booking['route']}\n"
                    f"Seat: {booking['seat_number']}\n"
                    f"Status: {booking['status']}\n"
                    f"Amount Paid: ${booking['price_paid_usd']:.2f}"
                )

    return f"No booking record found for reference '{ref_clean}' in this session."


def cancel_booking(
    booking_reference: str,
    ctx: Optional[ToolContext] = None,
) -> str:
    """Cancels an existing ticket booking by booking reference (PNR).

    Args:
        booking_reference: The 6-character booking PNR code.
        ctx: Injected ToolContext for modifying session state.
    """
    ref_clean = booking_reference.strip().upper()

    if ctx:
        user_bookings = ctx.get_state("user_bookings", [])
        for booking in user_bookings:
            if booking["booking_reference"] == ref_clean:
                booking["status"] = "CANCELLED"
                ctx.set_state("user_bookings", user_bookings)
                return f"Booking {ref_clean} for passenger {booking['passenger_name']} has been CANCELLED. Refund issued."

    return f"Unable to cancel. Booking reference '{ref_clean}' was not found."


ALL_TOOLS = [
    search_flights,
    get_flight_details,
    check_seat_map,
    reserve_ticket,
    get_booking_details,
    cancel_booking,
]
