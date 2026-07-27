# Airplane Ticket Concierge Agent (SkyConcierge)

An autonomous AI travel concierge agent built with the [Google Antigravity (AGY) SDK](file:///usr/local/google/home/gaowen/.gemini/config/plugins/google-antigravity-sdk/skills/google-antigravity-sdk/SKILL.md) to assist travelers with flight searches, seat maps, flight details, and ticket reservations.

---

## Features

- 🛫 **Flight Search**: Search direct flights between major airport hubs by origin, destination, date, and cabin class.
- 📋 **Flight Details**: View detailed schedules, aircraft info, and pricing.
- 💺 **Seat Map & Selection**: Inspect open seats and pick preferred seating for passengers.
- 🎫 **Ticket Reservation**: Reserve tickets with passenger names and passport credentials, returning confirmation PNRs.
- 🔄 **Session State Management**: Remembers reservations made within the active session via AGY `ToolContext`.
- ❌ **Booking Cancellation**: Cancel existing reservations and update booking status.

---

## Directory Structure

```text
.
├── README.md           # Project documentation and guide
├── requirements.txt    # Dependency requirements
├── agent.py            # Main Agent setup, configuration & interactive entry point
├── tools.py            # Flight search, seat map, and booking tools
└── example_usage.py    # Example script showing programmatic multi-turn usage
```

---

## Prerequisites & Installation

### 1. Python Environment

Ensure Python 3.10+ is installed. Install required packages:

```bash
pip install -r requirements.txt
```

### 2. API Key Setup

The Google Antigravity SDK uses Gemini models and requires a valid API key.

1. Obtain an API Key from [Google AI Studio](https://aistudio.google.com/app/api-keys).
2. Set the `GEMINI_API_KEY` environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Alternatively, pass `api_key` explicitly to `create_agent(api_key="...")`.

---

## Usage

### Interactive Terminal Mode

To chat interactively with the SkyConcierge agent in your terminal:

```bash
python agent.py
```

### Programmatic Usage

You can also run the provided example multi-turn demonstration script:

```bash
python example_usage.py
```

Or import `create_agent` into your own Python codebase:

```python
import asyncio
from agent import create_agent

async def main():
    agent = create_agent()
    async with agent:
        response = await agent.chat("Search flights from SFO to JFK for 2026-09-15.")
        async for chunk in response:
            print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Concierge Tools Reference

Defined in [`tools.py`](file:///usr/local/google/home/gaowen/workspace/airplane-ticket-concierge-agent/tools.py):

| Tool Function | Description |
|---|---|
| `search_flights` | Searches available flight options given origin, destination, date, and cabin class. |
| `get_flight_details` | Retrieves schedule, duration, airline, and open seats for a flight number. |
| `check_seat_map` | Displays seat layout and open seats for a given flight number. |
| `reserve_ticket` | Books a ticket for a passenger on a flight, generating a 6-character PNR reference. |
| `get_booking_details` | Retrieves booking details for a given PNR from current session state. |
| `cancel_booking` | Cancels an existing ticket reservation by PNR reference and restores seat availability. |
| `calculate_baggage_fees` | Calculates checked baggage allowance and extra baggage fees by cabin class. |

---

## License

Internal / Project Template. Built with Google Antigravity SDK.
