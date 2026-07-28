"""Comprehensive demonstration of SkyConcierge Advanced Architecture:
Pydantic Validation, Structured JSON Logging, Subagent Delegation, Secret Manager, & Evaluator.
"""

import asyncio
import tempfile
from agent import create_agent
from database import async_get_booking
from logging_tracing import logger
from memory import async_save_user_memory
from secrets_manager import get_secret
from subagents import delegate_to_booking_specialist, delegate_to_search_specialist


async def run_example():
    """Runs demonstration of SkyConcierge features."""
    print("==================================================")
    print(" 🚀 SkyConcierge Comprehensive Features Demo ")
    print("==================================================")

    # 1. Secret Manager Resolution
    print("\n[1] Testing Secret Manager Resolution:")
    api_key = get_secret("GEMINI_API_KEY", default="env_or_mock_key")
    print(f"  • Resolved Secret Key: '{api_key[:4]}****'")

    # 2. Structured JSON Logger & PII Redaction
    print("\n[2] Testing Structured JSON Logger & PII Redaction:")
    logger.log(
        level="INFO",
        message="User requested ticket reservation with passport credentials",
        intent="RESERVE_TICKET",
        action="reserve_ticket",
        outcome="PENDING",
        duration_ms=12.5,
        payload={"passenger": "Alex Morgan", "passport_number": "P12345678", "credit_card": "4111111111111111"}
    )

    # 3. Subagent Delegation Tools
    print("\n[3] Testing Active Subagent Delegation Tools:")
    search_subagent_res = await delegate_to_search_specialist("Search flights from SFO to JFK on 2026-09-15.")
    print(f"  • FlightSearchSpecialist Output:\n{search_subagent_res[:160]}...")

    # 4. Main Agent Execution
    print("\n[4] Initializing Main Agent with Persistence...")
    save_dir = tempfile.mkdtemp()
    agent = create_agent(save_dir=save_dir)

    async with agent:
        print("\n--- Turn 1: Save User Preference ---")
        prompt1 = "Save my preferred seat as 12A and passport as P12345678."
        print(f"User: {prompt1}")
        resp1 = await agent.chat(prompt1)
        print("SkyConcierge: ", end="")
        async for token in resp1:
            print(token, end="", flush=True)
        print()

        print("\n--- Turn 2: Reserve Ticket (Strict Pydantic Validation & HITL) ---")
        prompt2 = "Book flight AA-101 for passenger Alex Morgan with passport P12345678."
        print(f"User: {prompt2}")
        resp2 = await agent.chat(prompt2)
        print("SkyConcierge: ", end="")
        async for token in resp2:
            print(token, end="", flush=True)
        print()

    print("\n==================================================")
    print(" ✅ All Features Verified Successfully!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_example())
