# Airplane Ticket Concierge Agent (SkyConcierge)

An enterprise-grade autonomous AI travel concierge system built with the [Google Antigravity (AGY) SDK](file:///usr/local/google/home/gaowen/.gemini/config/plugins/google-antigravity-sdk/skills/google-antigravity-sdk/SKILL.md).

SkyConcierge features a **multi-agent architecture**, **dynamic model routing**, **declarative security guardrails**, and **human-in-the-loop (HITL) approval hooks** for high-stakes actions like flight reservations and booking cancellations.

---

## Key Architectural Capabilities

### 🤖 1. Multi-Agent Delegation Pattern
- **Main Orchestrator (`SkyConcierge`)**: Manages end-to-end conversation flow, evaluates user requests, and orchestrates sub-agent sub-tasks.
- **Flight Search Specialist (`FlightSearchSpecialist`)**: Subagent specialized in querying schedules, airport codes, seat maps, and baggage allowances.
- **Booking & Reservation Specialist (`BookingSpecialist`)**: Subagent focused on processing passenger identity verification, PNR creation, and cancellation lifecycles.

### ⚡ 2. Task-Based Model Routing
- **Fast Tier (`gemini-3.5-flash`)**: Low-latency model utilized for read-only lookups, flight search queries, seat maps, and baggage fee rules.
- **High-Reasoning Tier (`gemini-3.5-pro`)**: High-precision model utilized for identity validation, reservation processing, and security policy verification.

### 🛡️ 3. Declarative Security Guardrails
Built using `google.antigravity.hooks.policy`:
- **Passport Guardrail Predicate**: Validates passport strings against regex format rules and guards against prompt injection keywords before allowing reservation tools to run.
- **Priority Policy Evaluation**:
  1. *Deny*: Rejects invalid or malicious passport credentials automatically.
  2. *Ask User*: Triggers human approval for high-stakes state changes (`reserve_ticket`, `cancel_booking`).
  3. *Allow*: Grants permission for read-only inquiry tools (`search_flights`, `get_flight_details`, `check_seat_map`, `calculate_baggage_fees`).

### 👤 4. Human-In-The-Loop (HITL) Hooks
- **Pre-Tool Call Interceptor (`human_approval_handler`)**: Before executing any high-stakes transaction (`reserve_ticket`, `cancel_booking`), the system intercepts the execution, displays transaction details (flight, passenger, seat, price), and prompts for explicit human approval.

---

## Project Structure

```text
.
├── README.md           # Architecture, security policy & usage guide
├── requirements.txt    # Package dependencies
├── agent.py            # Main SkyConcierge orchestrator & interactive CLI entry point
├── subagents.py        # Search and Booking specialist subagents & model router
├── security.py         # Declarative policy rules, passport & PNR guardrails
├── hooks.py            # Human-in-the-loop approval handler & lifecycle hooks
├── tools.py            # Flight search, seat map, reservation, and baggage tools
└── example_usage.py    # Demonstration of multi-agent, router, security & HITL features
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

## Tools Reference

| Tool | Action Type | Security Policy | Handler |
|---|---|---|---|
| `search_flights` | Read-only | `policy.allow` | Unrestricted |
| `get_flight_details` | Read-only | `policy.allow` | Unrestricted |
| `check_seat_map` | Read-only | `policy.allow` | Unrestricted |
| `calculate_baggage_fees` | Read-only | `policy.allow` | Unrestricted |
| `get_booking_details` | Read-only | `policy.allow` | Unrestricted |
| `reserve_ticket` | **High-Stakes** | `policy.ask_user` + Passport Guardrail | `human_approval_handler` |
| `cancel_booking` | **High-Stakes** | `policy.ask_user` | `human_approval_handler` |

---

## License

Built with Google Antigravity SDK. Internal Project Template.
