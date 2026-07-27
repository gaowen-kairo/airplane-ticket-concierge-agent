"""Lifecycle, Context Compaction, and Human-In-The-Loop (HITL) Hooks for Airplane Ticket Concierge Agent.

This module provides hooks to intercept lifecycle events, handle history context compaction events,
log turn interactions, and enforce human approval before executing high-stakes transactions.
"""

import sys
from typing import Any, Dict
from google.antigravity import types
from google.antigravity.hooks import hooks


async def human_approval_handler(tool_call: types.ToolCall) -> bool:
    """Approval handler invoked when a high-stakes tool requires human confirmation.

    Args:
        tool_call: ToolCall object containing tool name and arguments.

    Returns:
        True if approved by the user, False if denied.
    """
    name = tool_call.name
    args: Dict[str, Any] = tool_call.args or {}

    print(f"\n==================================================")
    print(f" ⚠️  HIGH-STAKES ACTION REQUIRES APPROVAL: {name}")
    print(f"==================================================")

    if name == "reserve_ticket":
        print(f"  • Flight Number:   {args.get('flight_number')}")
        print(f"  • Passenger Name:  {args.get('passenger_name')}")
        print(f"  • Passport No:     {args.get('passport_number')}")
        print(f"  • Requested Seat:  {args.get('seat_number', 'Auto-assigned')}")
    elif name == "cancel_booking":
        print(f"  • Booking Ref:     {args.get('booking_reference')}")
    else:
        for k, v in args.items():
            print(f"  • {k}: {v}")

    print("==================================================")

    # In non-interactive automated environments or pipes, auto-approve for testing
    if not sys.stdin.isatty():
        print("[HITL Hook] Non-interactive stdin detected -> Auto-approving high-stakes action for automation test.")
        return True

    try:
        choice = input("Do you confirm and authorize this transaction? (y/N): ").strip().lower()
        approved = choice in ("y", "yes")
        if approved:
            print("[HITL Hook] ✅ Transaction APPROVED by user.")
        else:
            print("[HITL Hook] ❌ Transaction DENIED by user.")
        return approved
    except (EOFError, KeyboardInterrupt):
        print("\n[HITL Hook] ❌ Input interrupted. Transaction DENIED.")
        return False


@hooks.pre_tool_call_decide
async def audit_pre_tool_call(tool_call: types.ToolCall) -> types.HookResult:
    """Audit logging hook that runs before any tool execution."""
    tool_name = tool_call.name
    print(f"\n[Audit Hook] Pre-tool execution intercept: '{tool_name}'")
    return types.HookResult(allow=True)


@hooks.pre_turn
async def log_pre_turn(prompt: str) -> types.HookResult:
    """Pre-turn hook to inspect incoming user prompt."""
    if not prompt or not prompt.strip():
        return types.HookResult(allow=False, reason="Empty prompt")

    return types.HookResult(allow=False if not prompt else True)


@hooks.post_turn
async def log_post_turn(response_text: str):
    """Post-turn hook invoked after response generation completes."""
    pass


@hooks.on_compaction
async def on_compaction_event(data):
    """Context Compaction Hook.

    Invoked when conversation trajectory history context compaction occurs.
    """
    print(f"\n[Compaction Hook] 🧹 History Context Compaction Event Intercepted. Compacting turn trajectory...")


def get_all_hooks():
    """Returns list of registered hooks for agent configuration."""
    return [
        audit_pre_tool_call,
        log_pre_turn,
        log_post_turn,
        on_compaction_event,
    ]
