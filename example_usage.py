"""Example script demonstrating programmatic usage of the Airplane Ticket Concierge Agent."""

import asyncio
from agent import create_agent


async def run_example():
    """Runs a multi-turn travel search and reservation conversation with SkyConcierge."""
    print("Initializing SkyConcierge Agent...")
    agent = create_agent()

    async with agent:
        # Turn 1: Search for flights
        print("\n--- User Turn 1 ---")
        prompt1 = "Hi! I need to find flights from SFO to JFK on 2026-09-15 in Economy."
        print(f"User: {prompt1}")
        
        response1 = await agent.chat(prompt1)
        print("SkyConcierge: ", end="")
        async for token in response1:
            print(token, end="", flush=True)
        print()

        # Turn 2: Reserve ticket
        print("\n--- User Turn 2 ---")
        prompt2 = "Great! Please book me on flight AA-101 for passenger Alex Morgan, Passport P12345678, seat 12A."
        print(f"User: {prompt2}")
        
        response2 = await agent.chat(prompt2)
        print("SkyConcierge: ", end="")
        async for token in response2:
            print(token, end="", flush=True)
        print()

        # Turn 3: Check booking confirmation
        print("\n--- User Turn 3 ---")
        prompt3 = "Can you show me my booking details to make sure everything is confirmed?"
        print(f"User: {prompt3}")
        
        response3 = await agent.chat(prompt3)
        print("SkyConcierge: ", end="")
        async for token in response3:
            print(token, end="", flush=True)
        print()


if __name__ == "__main__":
    asyncio.run(run_example())
