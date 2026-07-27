"""Airplane Ticket Concierge Agent.

An autonomous AI concierge agent built with the Google Antigravity (AGY) SDK to assist users
with airplane ticket searches, seat selection, flight details, and ticket reservations.
"""

import asyncio
import os
import sys
from typing import Optional

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import TemplatedSystemInstructions

from tools import ALL_TOOLS

CONCIERGE_SYSTEM_INSTRUCTION = """
You are SkyConcierge, an elite, professional, and helpful Airplane Ticket Concierge AI agent.

Your mission is to assist travelers with:
1. Searching for flights according to origin, destination, dates, and cabin class preferences.
2. Explaining flight details, itineraries, schedules, and seat choices.
3. Helping users select seats and view seat maps.
4. Reserving airplane tickets with passenger details and providing PNR booking references.
5. Checking or cancelling existing bookings upon user request.

Guidelines:
- Always be polite, professional, and clear.
- Present prices clearly in USD and format flight search results cleanly.
- Before making a reservation, ensure key passenger details (full legal name, passport/ID, desired flight, seat choice) are collected.
- When a reservation is completed, highlight the booking reference (PNR) clearly to the traveler.
- If a requested flight or seat is unavailable, recommend suitable alternative options.
"""


def create_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
) -> Agent:
    """Factory function to instantiate the Airplane Ticket Concierge Agent.

    Args:
        api_key: Optional Gemini API key. If omitted, reads from GEMINI_API_KEY env var.
        app_data_dir: Optional absolute path for custom artifact and state storage.

    Returns:
        An instantiated Agent object ready for use in async context manager.
    """
    templated_si = TemplatedSystemInstructions(
        identity=CONCIERGE_SYSTEM_INSTRUCTION
    )

    config_kwargs = {
        "tools": ALL_TOOLS,
        "system_instructions": templated_si,
    }

    if api_key:
        config_kwargs["api_key"] = api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    config = LocalAgentConfig(**config_kwargs)
    return Agent(config=config)


async def run_interactive_loop(agent: Agent):
    """Custom interactive loop for interacting with the concierge agent via CLI."""
    print("\nStarting interactive session with SkyConcierge.")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        try:
            user_input = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting session. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("Thank you for using SkyConcierge. Safe travels!")
            break

        print("SkyConcierge: ", end="", flush=True)
        try:
            response = await agent.chat(user_input)
            async for token in response:
                print(token, end="", flush=True)
            print()
        except Exception as e:
            print(f"\n[Error] {e}")


async def main():
    """Main entry point for running interactive terminal chat with SkyConcierge agent."""
    print("==================================================")
    print("  Welcome to SkyConcierge - Airplane Ticket Agent ")
    print("==================================================")

    agent = create_agent()
    async with agent:
        await run_interactive_loop(agent)


if __name__ == "__main__":
    asyncio.run(main())

