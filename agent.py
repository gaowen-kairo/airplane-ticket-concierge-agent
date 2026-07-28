"""Airplane Ticket Concierge Orchestration Agent.

An enterprise multi-agent AI system built with the Google Antigravity (AGY) SDK.
Integrates:
  - Multi-Agent Delegation: Main orchestrator coordinating subagents & delegation tools
  - Model Routing: Fast (flash) and Reasoning (pro) model tiering
  - Security Guardrails: Input validation, passport & PNR policies
  - Human-In-The-Loop (HITL) Hooks: Confirmation interceptor for high-stakes transactions
  - Structured Logging & Tracing: JSON logging, intent vs. outcome logging, PII redactor
  - Secret Manager Integration: Secure credential retrieval via secrets_manager
  - Pydantic Validation & Recovery Guidance: Strict schema validation with LLM recovery hints
"""

import asyncio
import os
import sys
from typing import Optional

from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import TemplatedSystemInstructions

from database import _init_db_tables
from hooks import get_all_hooks, human_approval_handler
from logging_tracing import logger
from secrets_manager import get_secret
from security import create_security_policies
from subagents import (
    delegate_to_booking_specialist,
    delegate_to_search_specialist,
    route_model_for_task,
)
from tools import ALL_TOOLS

# Expand main agent tools to include explicit subagent delegation tools
ORCHESTRATOR_TOOLS = ALL_TOOLS + [
    delegate_to_search_specialist,
    delegate_to_booking_specialist,
]

MAIN_CONCIERGE_SYSTEM_INSTRUCTION = """
You are SkyConcierge, an elite, professional, and secure Airplane Ticket Concierge AI System.

Architecture & Subagent Delegation:
1. Multi-Agent Orchestration: You coordinate specialized subagent workers:
   - Use 'delegate_to_search_specialist' for complex flight searches, schedules, and baggage policies.
   - Use 'delegate_to_booking_specialist' for ticket reservations, passenger identity verification, and cancellations.
2. Safety & Security: High-stakes actions (reserving tickets, cancelling bookings) require explicit human confirmation.
3. Persistent Database & State: All flight schedules, seat inventory, passenger tickets, and booking PNRs are backed by a persistent database.
4. Error Recovery: If a tool returns validation errors or failure guidance, follow the provided LLM recovery instructions to fix inputs.

Services:
- Search flights by origin, destination, date, cabin class.
- Inspect seat maps and calculate baggage allowances.
- Process ticket reservations (requiring valid passenger name and passport credentials).
- Save and recall traveler preferences.
- Compact long conversation memory when needed.

Guidelines:
- Maintain a polite, professional, and clear tone.
- Format pricing clearly in USD and present flight schedules cleanly in markdown tables or bullet points.
- Before triggering a reservation or cancellation, confirm key travel details with the user.
- If an action is denied by security policies or user refusal, explain politely and offer alternatives.
"""


def create_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
    save_dir: Optional[str] = None,
    conversation_id: Optional[str] = None,
    model: Optional[str] = None,
    approval_handler=human_approval_handler,
) -> Agent:
    """Factory function to instantiate the main SkyConcierge Orchestration Agent.

    Args:
        api_key: Optional Gemini API key. If omitted, retrieves from Secret Manager or GEMINI_API_KEY env.
        app_data_dir: Optional storage directory path for artifacts.
        save_dir: Optional persistence directory path for conversation history trajectories.
        conversation_id: Optional conversation ID to resume past persistent sessions.
        model: Optional model identifier override.
        approval_handler: Human-in-the-loop approval handler function.

    Returns:
        Instantiated Agent object ready for use in async context manager.
    """
    # 1. Initialize persistent database tables
    _init_db_tables()

    # 2. Retrieve API Key securely from Secret Manager or environment
    resolved_api_key = api_key or get_secret("GEMINI_API_KEY")

    selected_model = model or route_model_for_task("complex")
    templated_si = TemplatedSystemInstructions(
        identity=MAIN_CONCIERGE_SYSTEM_INSTRUCTION
    )

    # 3. Security policies & guardrails
    policies = create_security_policies(approval_handler=approval_handler)

    # 4. Lifecycle, compaction & LLM recovery hooks
    registered_hooks = get_all_hooks()

    # 5. Capabilities: subagents and write tools
    capabilities = types.CapabilitiesConfig(
        enable_subagents=True,
    )

    config_kwargs = {
        "model": selected_model,
        "tools": ORCHESTRATOR_TOOLS,
        "system_instructions": templated_si,
        "policies": policies,
        "hooks": registered_hooks,
        "capabilities": capabilities,
    }

    if resolved_api_key:
        config_kwargs["api_key"] = resolved_api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir
    if save_dir:
        config_kwargs["save_dir"] = save_dir
    if conversation_id:
        config_kwargs["conversation_id"] = conversation_id

    config = LocalAgentConfig(**config_kwargs)
    logger.log("INFO", f"SkyConcierge Agent created with model '{selected_model}' and {len(ORCHESTRATOR_TOOLS)} tools.")
    return Agent(config=config)


async def run_interactive_loop(agent: Agent):
    """Interactive terminal execution loop with SkyConcierge."""
    print("\n==================================================")
    print(" 🛫 SkyConcierge Multi-Agent System Ready ")
    print(" (Subagent Delegation • Pydantic Validation • HITL Security) ")
    print(" Type 'exit' or 'quit' to end session.")
    print("==================================================\n")

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
    """Main entry point for interactive terminal chat."""
    agent = create_agent()
    async with agent:
        await run_interactive_loop(agent)


if __name__ == "__main__":
    asyncio.run(main())
