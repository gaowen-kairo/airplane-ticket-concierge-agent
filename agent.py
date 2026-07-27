"""Airplane Ticket Concierge Orchestration Agent.

An autonomous multi-agent AI system built with the Google Antigravity (AGY) SDK.
Integrates:
  - Multi-Agent Pattern: Orchestrator delegating to specialized subagents/tools
  - Model Routing: Task-based tiering between fast (flash) and reasoning (pro) models
  - Security Guardrails: Input validation, passport/PNR policies
  - Human-In-The-Loop (HITL) Hooks: Confirmation interceptor before executing high-stakes transactions
"""

import asyncio
import os
import sys
from typing import Optional

from google.antigravity import Agent, LocalAgentConfig, types
from google.antigravity.types import TemplatedSystemInstructions

from hooks import get_all_hooks, human_approval_handler
from security import create_security_policies
from subagents import route_model_for_task
from tools import ALL_TOOLS

MAIN_CONCIERGE_SYSTEM_INSTRUCTION = """
You are SkyConcierge, an elite, professional, and secure Airplane Ticket Concierge AI System.

Architecture & Operations:
1. Multi-Agent Delegation: You orchestrate travel requests and can spawn subagents or execute specialized tools.
2. Safety & Security: High-stakes actions (reserving tickets, cancelling bookings) require explicit human confirmation.
3. Travel Services:
   - Search flights by origin, destination, date, cabin class.
   - Inspect seat maps and calculate baggage allowances.
   - Process ticket reservations (requiring valid passenger name and passport credentials).
   - Look up or cancel existing PNR bookings.

Guidelines:
- Maintain a polite, professional, and clear tone.
- Format pricing clearly in USD and present flight schedules in clean markdown tables or bullet points.
- Before triggering a reservation or cancellation, confirm key travel details with the user.
- If an action is denied by security policies or user refusal, explain politely and offer alternatives.
"""


def create_agent(
    api_key: Optional[str] = None,
    app_data_dir: Optional[str] = None,
    model: Optional[str] = None,
    approval_handler=human_approval_handler,
) -> Agent:
    """Factory function to instantiate the main SkyConcierge Orchestration Agent.

    Configures subagent capabilities, security policies, HITL hooks, and model routing.

    Args:
        api_key: Optional Gemini API key. If omitted, reads from GEMINI_API_KEY env var.
        app_data_dir: Optional storage directory path.
        model: Optional model override. Defaults to route_model_for_task('complex').
        approval_handler: Human-in-the-loop approval handler function.

    Returns:
        Instantiated Agent object ready for use in async context manager.
    """
    selected_model = model or route_model_for_task("complex")
    templated_si = TemplatedSystemInstructions(
        identity=MAIN_CONCIERGE_SYSTEM_INSTRUCTION
    )

    # 1. Security policies & guardrails
    policies = create_security_policies(approval_handler=approval_handler)

    # 2. Lifecycle hooks
    registered_hooks = get_all_hooks()

    # 3. Capability configuration: enable subagent spawning and write tools
    capabilities = types.CapabilitiesConfig(
        enable_subagents=True,
    )

    config_kwargs = {
        "model": selected_model,
        "tools": ALL_TOOLS,
        "system_instructions": templated_si,
        "policies": policies,
        "hooks": registered_hooks,
        "capabilities": capabilities,
    }

    if api_key:
        config_kwargs["api_key"] = api_key
    if app_data_dir:
        config_kwargs["app_data_dir"] = app_data_dir

    config = LocalAgentConfig(**config_kwargs)
    return Agent(config=config)


async def run_interactive_loop(agent: Agent):
    """Interactive terminal execution loop with SkyConcierge."""
    print("\n==================================================")
    print(" 🛫 SkyConcierge Multi-Agent System Ready ")
    print(" (Multi-Agent • Model Router • HITL Security) ")
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
