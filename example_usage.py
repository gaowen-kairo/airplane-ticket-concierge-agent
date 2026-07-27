"""Comprehensive example demonstrating Multi-Agent patterns, Model Routing, Security Guardrails, and HITL hooks."""

import asyncio
from agent import create_agent
from security import validate_passport_number
from subagents import route_model_for_task


async def run_example():
    """Runs demonstration of SkyConcierge multi-agent system features."""
    print("==================================================")
    print(" 🚀 SkyConcierge Advanced Features Demonstration ")
    print("==================================================")

    # Demonstrate Model Router
    print("\n[1] Testing Model Router:")
    search_model = route_model_for_task("search")
    booking_model = route_model_for_task("booking")
    print(f"  • Search task model tier:    '{search_model}' (Fast)")
    print(f"  • Booking task model tier:   '{booking_model}' (Reasoning)")

    # Demonstrate Security Guardrail
    print("\n[2] Testing Passport Guardrail Validation:")
    valid_pass = "P12345678"
    invalid_pass = "bad_pass; DROP TABLE users;"
    print(f"  • Passport '{valid_pass}':    Valid={validate_passport_number(valid_pass)}")
    print(f"  • Passport '{invalid_pass}': Valid={validate_passport_number(invalid_pass)}")

    print("\n[3] Initializing Main Concierge Agent...")
    agent = create_agent()

    async with agent:
        # Scenario A: Search query (Read-only, allowed by policy)
        print("\n--- Scenario A: Flight Search (Policy: Allowed) ---")
        prompt_a = "Search for flights from SFO to JFK on 2026-09-15."
        print(f"User: {prompt_a}")
        
        response_a = await agent.chat(prompt_a)
        print("SkyConcierge: ", end="")
        async for token in response_a:
            print(token, end="", flush=True)
        print()

        # Scenario B: Reserve ticket (High-Stakes, triggers HITL Hook)
        print("\n--- Scenario B: Reserve Ticket (Policy: High-Stakes HITL Hook) ---")
        prompt_b = "Reserve seat 12A on flight AA-101 for passenger Alex Morgan, Passport P12345678."
        print(f"User: {prompt_b}")
        
        response_b = await agent.chat(prompt_b)
        print("SkyConcierge: ", end="")
        async for token in response_b:
            print(token, end="", flush=True)
        print()

        # Scenario C: Check booking confirmation
        print("\n--- Scenario C: Check Booking Details ---")
        prompt_c = "Show my booking details."
        print(f"User: {prompt_c}")
        
        response_c = await agent.chat(prompt_c)
        print("SkyConcierge: ", end="")
        async for token in response_c:
            print(token, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(run_example())
