# Airplane Ticket Concierge Agent (SkyConcierge)

An enterprise-grade autonomous AI travel concierge system built with the [Google Antigravity (AGY) SDK](file:///usr/local/google/home/gaowen/.gemini/config/plugins/google-antigravity-sdk/skills/google-antigravity-sdk/SKILL.md).

SkyConcierge features a **multi-agent architecture**, **task-based model routing**, **declarative security guardrails**, **human-in-the-loop (HITL) hooks**, **persistent SQLite database storage**, **history context compaction**, and **async memory operations**.

---

## Key Architectural Capabilities

### 💾 1. Persistent SQLite Database Storage
- **Database Backend (`concierge.db`)**: Replaces transient in-memory dictionaries with a persistent, thread-safe SQLite database handled asynchronously via `database.py`.
- **Flight & Reservation Schema**: Stores flight inventories, seat allocations, PNR booking records, traveler identity profiles, and context compaction summaries.
- **Survives Restart**: All ticket reservations, PNR references, seat map changes, and traveler profiles survive application restarts.

### 🧠 2. History Context Compaction & Trajectory Persistence
- **Context Compaction Hook (`@hooks.on_compaction`)**: Automatically listens to context window compaction events.
- **Trajectory Persistence (`save_dir` & `conversation_id`)**: Persists conversation trajectories to disk, allowing session resumption.
- **Memory Compaction Tool (`compact_conversation_memory`)**: Summarizes long turn histories into structured state memory to optimize prompt token limits.

### ⚡ 3. Async Memory Operations
- **Async Memory Read/Write**: Asynchronously stores, updates, and recalls user travel preferences, loyalty numbers, and dietary requirements using `memory.py` (`async_save_user_memory`, `async_get_user_memories`).
- **Memory Tools**: Integrated agent tools (`save_user_preference`, `recall_user_preferences`).

### 🤖 4. Multi-Agent Delegation Pattern
- **Main Orchestrator (`SkyConcierge`)**: Manages end-to-end conversation flow and coordinates specialized subagents.
- **Flight Search Specialist (`FlightSearchSpecialist`)**: Subagent specialized in querying schedules, airport codes, seat maps, and baggage allowances.
- **Booking Specialist (`BookingSpecialist`)**: Subagent focused on processing passenger identity verification, PNR creation, and cancellation lifecycles.

### 🎯 5. Model Routing & Security Guardrails
- **Fast Tier (`gemini-3.5-flash`)**: Low-latency model for read-only lookups and flight searches.
- **Reasoning Tier (`gemini-3.5-pro`)**: High-precision model for identity validation and reservations.
- **Human-In-The-Loop (HITL) Approval Hooks**: Intercepts high-stakes transactions (`reserve_ticket`, `cancel_booking`) for user confirmation.

---

## Project Structure

```text
.
├── README.md           # System architecture, database, & usage guide
├── requirements.txt    # Package dependencies
├── agent.py            # Main SkyConcierge orchestrator & interactive CLI entry point
├── database.py         # Persistent SQLite database storage & async CRUD queries
├── memory.py           # Async user memory persistence & history context compaction
├── subagents.py        # Search and Booking specialist subagents & model router
├── security.py         # Declarative policy rules, passport & PNR guardrails
├── hooks.py            # Compaction hook, HITL approval handler & lifecycle hooks
├── tools.py            # Database-backed flight search, seat map, reservation, & baggage tools
└── example_usage.py    # Demonstration of database persistence, async memory & compaction
```

---

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

---

## Running SkyConcierge

### Interactive Terminal CLI

```bash
python agent.py
```

### Feature Demonstration Script

```bash
python example_usage.py
```

---

## License

Built with Google Antigravity SDK. Internal Project Template.
