"""Persistent SQLite Database Module for Airplane Ticket Concierge Agent.

Provides thread-safe async database operations for persisting flight inventories,
ticket reservations, PNR references, user memories, and conversation compaction summaries.
"""

import asyncio
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# Default database file path
DEFAULT_DB_PATH = "concierge.db"


def _get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a sqlite3 connection configured with dict rows."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db_tables(db_path: str = DEFAULT_DB_PATH):
    """Initializes SQLite tables for persistent flight inventory, reservations, memories, and compactions."""
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. Flights table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flights (
        flight_number TEXT PRIMARY KEY,
        airline TEXT NOT NULL,
        origin TEXT NOT NULL,
        destination TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        duration TEXT NOT NULL,
        price_usd REAL NOT NULL,
        cabin_class TEXT NOT NULL,
        available_seats TEXT NOT NULL
    )
    """)

    # 2. Reservations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        booking_reference TEXT PRIMARY KEY,
        flight_number TEXT NOT NULL,
        airline TEXT NOT NULL,
        route TEXT NOT NULL,
        passenger_name TEXT NOT NULL,
        passport_number TEXT NOT NULL,
        seat_number TEXT NOT NULL,
        status TEXT NOT NULL,
        price_paid_usd REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. User Memories table (Async Memory Persistence)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        memory_key TEXT NOT NULL,
        memory_value TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, memory_key)
    )
    """)

    # 4. History Compaction Summaries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compaction_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT NOT NULL,
        summary_text TEXT NOT NULL,
        compacted_turns INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed initial flights if table is empty
    cursor.execute("SELECT COUNT(*) FROM flights")
    if cursor.fetchone()[0] == 0:
        seed_flights = [
            ("AA-101", "American Skyways", "SFO", "JFK", "08:00 AM", "04:30 PM", "5h 30m", 350.0, "economy", json.dumps(["12A", "12B", "14C", "15D", "18A"])),
            ("AA-202", "American Skyways", "SFO", "JFK", "01:15 PM", "09:45 PM", "5h 30m", 720.0, "business", json.dumps(["2A", "2B", "3A", "3F"])),
            ("UA-405", "United Global", "SFO", "JFK", "10:30 AM", "07:00 PM", "5h 30m", 310.0, "economy", json.dumps(["10A", "11C", "20E", "22F"])),
            ("DL-882", "Delta Express", "LAX", "ORD", "07:00 AM", "01:15 PM", "4h 15m", 280.0, "economy", json.dumps(["8A", "9B", "14D"])),
            ("BA-178", "British Airways", "JFK", "LHR", "06:30 PM", "06:30 AM (+1)", "7h 00m", 850.0, "premium economy", json.dumps(["12D", "12E", "14A"])),
        ]
        cursor.executemany("""
        INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, duration, price_usd, cabin_class, available_seats)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_flights)

    conn.commit()
    conn.close()


async def async_init_db(db_path: str = DEFAULT_DB_PATH):
    """Asynchronously initializes database tables."""
    await asyncio.to_thread(_init_db_tables, db_path)


# --- Flight Queries ---

def _db_search_flights(origin: str, destination: str, cabin_class: str, db_path: str) -> List[Dict[str, Any]]:
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    
    class_clean = cabin_class.strip().lower()
    if class_clean == "any":
        cursor.execute(
            "SELECT * FROM flights WHERE origin = ? AND destination = ?",
            (origin.upper(), destination.upper())
        )
    else:
        cursor.execute(
            "SELECT * FROM flights WHERE origin = ? AND destination = ? AND lower(cabin_class) = ?",
            (origin.upper(), destination.upper(), class_clean)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item["available_seats"] = json.loads(item["available_seats"])
        results.append(item)
    return results


async def async_search_flights(origin: str, destination: str, cabin_class: str = "economy", db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Asynchronously searches flights in database."""
    return await asyncio.to_thread(_db_search_flights, origin, destination, cabin_class, db_path)


def _db_get_flight(flight_number: str, db_path: str) -> Optional[Dict[str, Any]]:
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flights WHERE upper(flight_number) = ?", (flight_number.upper(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    res = dict(row)
    res["available_seats"] = json.loads(res["available_seats"])
    return res


async def async_get_flight(flight_number: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Asynchronously retrieves details for a flight number."""
    return await asyncio.to_thread(_db_get_flight, flight_number, db_path)


# --- Reservation Persistence ---

def _db_reserve_ticket(flight_number: str, passenger_name: str, passport_number: str, seat_number: Optional[str], db_path: str) -> Dict[str, Any]:
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM flights WHERE upper(flight_number) = ?", (flight_number.upper(),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Flight '{flight_number}' does not exist.")

    flight = dict(row)
    available_seats = json.loads(flight["available_seats"])

    if not available_seats:
        conn.close()
        raise ValueError(f"Flight '{flight_number}' is sold out.")

    if seat_number:
        seat_clean = seat_number.strip().upper()
        if seat_clean not in available_seats:
            conn.close()
            raise ValueError(f"Seat '{seat_clean}' is not available. Open seats: {', '.join(available_seats)}")
        selected_seat = seat_clean
    else:
        selected_seat = available_seats[0]

    # Remove allocated seat & update DB
    available_seats.remove(selected_seat)
    cursor.execute(
        "UPDATE flights SET available_seats = ? WHERE flight_number = ?",
        (json.dumps(available_seats), flight["flight_number"])
    )

    # Generate PNR
    import random, string
    pnr = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    record = {
        "booking_reference": pnr,
        "flight_number": flight["flight_number"],
        "airline": flight["airline"],
        "route": f"{flight['origin']} -> {flight['destination']}",
        "passenger_name": passenger_name,
        "passport_number": passport_number,
        "seat_number": selected_seat,
        "status": "CONFIRMED",
        "price_paid_usd": flight["price_usd"],
    }

    cursor.execute("""
    INSERT INTO reservations (booking_reference, flight_number, airline, route, passenger_name, passport_number, seat_number, status, price_paid_usd)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pnr, flight["flight_number"], flight["airline"], record["route"], passenger_name, passport_number, selected_seat, "CONFIRMED", flight["price_usd"]))

    conn.commit()
    conn.close()
    return record


async def async_reserve_ticket(flight_number: str, passenger_name: str, passport_number: str, seat_number: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Asynchronously creates a persistent ticket reservation in database."""
    return await asyncio.to_thread(_db_reserve_ticket, flight_number, passenger_name, passport_number, seat_number, db_path)


def _db_get_booking(pnr: str, db_path: str) -> Optional[Dict[str, Any]]:
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations WHERE upper(booking_reference) = ?", (pnr.upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


async def async_get_booking(pnr: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Asynchronously retrieves booking details by PNR."""
    return await asyncio.to_thread(_db_get_booking, pnr, db_path)


def _db_cancel_booking(pnr: str, db_path: str) -> Dict[str, Any]:
    conn = _get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations WHERE upper(booking_reference) = ?", (pnr.upper(),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Booking reference '{pnr}' not found.")

    res = dict(row)
    if res["status"] == "CANCELLED":
        conn.close()
        return res

    cursor.execute("UPDATE reservations SET status = 'CANCELLED' WHERE booking_reference = ?", (res["booking_reference"],))

    # Restore seat in flight inventory
    cursor.execute("SELECT available_seats FROM flights WHERE flight_number = ?", (res["flight_number"],))
    f_row = cursor.fetchone()
    if f_row:
        seats = json.loads(f_row["available_seats"])
        if res["seat_number"] not in seats:
            seats.append(res["seat_number"])
            seats.sort()
            cursor.execute("UPDATE flights SET available_seats = ? WHERE flight_number = ?", (json.dumps(seats), res["flight_number"]))

    conn.commit()
    conn.close()
    res["status"] = "CANCELLED"
    return res


async def async_cancel_booking(pnr: str, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Asynchronously cancels reservation and restores seat in database."""
    return await asyncio.to_thread(_db_cancel_booking, pnr, db_path)
