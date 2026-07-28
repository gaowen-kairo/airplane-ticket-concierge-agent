"""Subagents, Delegation Orchestration, and Model Routing.

This module defines specialized subagent roles (Search Specialist, Booking Specialist)
and provides active delegation functions so the main agent coordinates specialized subagent workers.
"""

import asyncio
from typing import Dict, List, Optional
from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import TemplatedSystemInstructions

from logging_tracing import log_tool_intent_and_outcome
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
        return MODEL_TIER_FAST
    elif category in ("booking", "reservation", "cancellation", "passport_verification"):
        return MODEL_TIER_REASONING
    else:
        return MODEL_TIER_FAST


from secrets_manager import get_secret

def create_search_specialist_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
) -> Agent:
    """Creates the Flight Search Specialist Subagent."""
    resolved_api_key = api_key or get_secret("GEMINI_API_KEY")
    system_instructions = TemplatedSystemInstructions(
        identity=(
            "You are FlightSearchSpecialist, a specialized subagent dedicated to flight search, "
            "schedules, seat maps, and baggage fee calculations."
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
    if resolved_api_key:
        config_kwargs["api_key"] = resolved_api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    return Agent(config=LocalAgentConfig(**config_kwargs))


def create_booking_specialist_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
    approval_handler: Optional[object] = None,
) -> Agent:
    """Creates the Booking & Reservation Specialist Subagent."""
    resolved_api_key = api_key or get_secret("GEMINI_API_KEY")
    system_instructions = TemplatedSystemInstructions(
        identity=(
            "You are BookingSpecialist, a specialized subagent dedicated to ticket reservations, "
            "passenger identity validation, PNR tracking, and cancellation."
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
    if resolved_api_key:
        config_kwargs["api_key"] = resolved_api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    return Agent(config=LocalAgentConfig(**config_kwargs))


# --- Active Subagent Delegation Tools for Main Agent Coordination ---

async def delegate_to_search_specialist(task_description: str) -> str:
    """Delegates a flight search, schedule, seat map, or baggage task to the specialized FlightSearchSpecialist subagent.

    Args:
        task_description: The specific search query or baggage inquiry to delegate.
    """
    specialist = create_search_specialist_agent()
    log_tool_intent_and_outcome(
        intent="DELEGATE_SEARCH",
        action="delegate_to_search_specialist",
        outcome="SUCCESS",
        duration_ms=5.0,
        payload={"task": task_description},
    )

    async with specialist:
        response = await specialist.chat(task_description)
        return await response.text()


async def delegate_to_booking_specialist(task_description: str) -> str:
    """Delegates a reservation, booking lookup, or cancellation task to the specialized BookingSpecialist subagent.

    Args:
        task_description: The reservation or cancellation instructions to delegate.
    """
    specialist = create_booking_specialist_agent()
    log_tool_intent_and_outcome(
        intent="DELEGATE_BOOKING",
        action="delegate_to_booking_specialist",
        outcome="SUCCESS",
        duration_ms=5.0,
        payload={"task": task_description},
    )

    async with specialist:
        response = await specialist.chat(task_description)
        return await response.text()
