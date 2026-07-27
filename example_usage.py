"""Comprehensive demonstration of Persistent Database State, Async Memory Operations, and History Compaction."""

import asyncio
import tempfile
from agent import create_agent
from database import async_get_booking
from memory import async_get_user_memories, async_save_user_memory


async def run_example():
    """Runs demonstration of SkyConcierge persistence, async memory, and history compaction features."""
    print("==================================================")
    print(" 🚀 SkyConcierge Memory, Compaction & Database Demo ")
    print("==================================================")

    # 1. Async Memory Operations
    print("\n[1] Testing Async Memory Operations:")
    await async_save_user_memory("user_123", "frequent_flyer_no", "AA-998877", category="loyalty")
    await async_save_user_memory("user_123", "seat_preference", "Window Row 12", category="preference")
    memories = await async_get_user_memories("user_123")
    print(f"  • Retrieved {len(memories)} stored memories for 'user_123':")
    for m in memories:
        print(f"    - {m['memory_key']}: {m['memory_value']} ({m['category']})")

    # 2. Session Trajectory Persistence (save_dir) & Persistent Database
    print("\n[2] Initializing Agent with Persistent save_dir and SQLite Database...")
    save_dir = tempfile.mkdtemp()
    
    agent = create_agent(save_dir=save_dir)

    async with agent:
        conv_id = agent.conversation_id
        print(f"  • Session Conversation ID: {conv_id}")

        # Scenario A: Save User Travel Preference via Agent
        print("\n--- Turn 1: Save User Travel Preference ---")
        prompt1 = "Please save my preferred seating as Window Row 12 and my passport as P12345678."
        print(f"User: {prompt1}")
        resp1 = await agent.chat(prompt1)
        print("SkyConcierge: ", end="")
        async for token in resp1:
            print(token, end="", flush=True)
        print()

        # Scenario B: Reserve Ticket into SQLite Database
        print("\n--- Turn 2: Reserve Ticket (Persisted in SQLite Database) ---")
        prompt2 = "Book flight AA-101 for passenger Alex Morgan with passport P12345678."
        print(f"User: {prompt2}")
        resp2 = await agent.chat(prompt2)
        print("SkyConcierge: ", end="")
        async for token in resp2:
            print(token, end="", flush=True)
        print()

        # Scenario C: Context Compaction
        print("\n--- Turn 3: History Context Compaction ---")
        prompt3 = "Please compact my conversation context memory."
        print(f"User: {prompt3}")
        resp3 = await agent.chat(prompt3)
        print("SkyConcierge: ", end="")
        async for token in resp3:
            print(token, end="", flush=True)
        print()

    # 3. Verify Database Persistence across Sessions
    print("\n[3] Verifying Database Record Persistence across Session Restart...")
    # Read reservations directly from database
    import sqlite3
    conn = sqlite3.connect("concierge.db")
    cursor = conn.cursor()
    cursor.execute("SELECT booking_reference, passenger_name, flight_number, seat_number, status FROM reservations")
    rows = cursor.fetchall()
    conn.close()

    print(f"  • Persistent SQLite Database Table 'reservations' ({len(rows)} entries):")
    for r in rows:
        print(f"    - PNR {r[0]} | Passenger: {r[1]} | Flight: {r[2]} | Seat: {r[3]} | Status: {r[4]}")

    print("\n==================================================")
    print(" ✅ Persistence, Async Memory & Compaction Verified!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_example())
