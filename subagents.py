"""Subagents and Model Routing Configuration for Airplane Ticket Concierge.

This module defines specialized subagent roles (Search Specialist, Booking Specialist)
and dynamic model routing rules for balancing response speed against deep reasoning capabilities.
"""

from typing import Dict, List, Optional
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import TemplatedSystemInstructions

from security import create_security_policies
from tools import (
    calculate_baggage_fees,
    cancel_booking,
    check_seat_map,
    get_booking_details,
    get_flight_details,
    reserve_ticket,
    search_flights,
)

# Model routing tiers
MODEL_TIER_FAST = "gemini-3.5-flash"
MODEL_TIER_REASONING = "gemini-3.5-pro"


def route_model_for_task(task_type: str) -> str:
    """Dynamic Model Router.

    Selects the optimal Gemini model identifier based on task complexity, speed needs,
    and precision requirements.

    Args:
        task_type: Task category ('search', 'baggage', 'booking', 'cancellation', 'complex').

    Returns:
        Model identifier string.
    """
    category = task_type.strip().lower()

    if category in ("search", "flight_query", "seat_map", "baggage"):
        # Fast, low-latency model for routine read-only lookups
        return MODEL_TIER_FAST
    elif category in ("booking", "reservation", "cancellation", "passport_verification"):
        # High reasoning, high-precision model for sensitive state changes
        return MODEL_TIER_REASONING
    else:
        # Default balanced model
        return MODEL_TIER_FAST


def create_search_specialist_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
) -> Agent:
    """Creates the Flight Search Specialist Subagent.

    Focuses exclusively on search, schedules, seat map inspection, and baggage calculations.
    Uses the fast model tier for low latency.

    Args:
        api_key: Optional Gemini API key.
        app_data_dir: Optional application storage directory.

    Returns:
        Instantiated Agent object configured for search operations.
    """
    system_instructions = TemplatedSystemInstructions(
        identity=(
            "You are FlightSearchSpecialist, a subagent specializing in flight search, "
            "flight schedules, seat maps, and baggage fee rules. Provide concise, clear options."
        )
    )

    tools = [
        search_flights,
        get_flight_details,
        check_seat_map,
        calculate_baggage_fees,
    ]

    model = route_model_for_task("search")

    config_kwargs = {
        "model": model,
        "tools": tools,
        "system_instructions": system_instructions,
        "capabilities": types.CapabilitiesConfig(enable_subagents=False),
    }
    if api_key:
        config_kwargs["api_key"] = api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    return Agent(config=LocalAgentConfig(**config_kwargs))


def create_booking_specialist_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
    approval_handler: Optional[object] = None,
) -> Agent:
    """Creates the Booking & Reservation Specialist Subagent.

    Focuses on reservation creation, passenger identity validation, PNR tracking,
    and cancellation. Uses security guardrails and the reasoning model tier.

    Args:
        api_key: Optional Gemini API key.
        app_data_dir: Optional application storage directory.
        approval_handler: Human-in-the-loop approval handler function.

    Returns:
        Instantiated Agent object configured for booking operations.
    """
    system_instructions = TemplatedSystemInstructions(
        identity=(
            "You are BookingSpecialist, a subagent specializing in airplane ticket reservations, "
            "seat assignments, and PNR booking management. Verify passenger details thoroughly."
        )
    )

    tools = [
        reserve_ticket,
        get_booking_details,
        cancel_booking,
        check_seat_map,
    ]

    policies = create_security_policies(approval_handler=approval_handler)
    model = route_model_for_task("booking")

    config_kwargs = {
        "model": model,
        "tools": tools,
        "system_instructions": system_instructions,
        "policies": policies,
        "capabilities": types.CapabilitiesConfig(enable_subagents=False),
    }
    if api_key:
        config_kwargs["api_key"] = api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    return Agent(config=LocalAgentConfig(**config_kwargs))
