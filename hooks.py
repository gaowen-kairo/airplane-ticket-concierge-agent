"""Lifecycle, Context Compaction, Tool Error Recovery, and Human-In-The-Loop (HITL) Hooks.

This module provides hooks to intercept lifecycle events, handle context compaction events,
redact PII in audit logs, and format explicit recovery guidance for the LLM on tool errors.
"""

import sys
from typing import Any, Dict, List, Optional
from google.antigravity import types
from google.antigravity.hooks import hooks

from logging_tracing import PIIRedactor, logger
from schemas import ErrorResponseWithRecovery


async def human_approval_handler(tool_call: types.ToolCall) -> bool:
    """Approval handler invoked when a high-stakes tool requires human confirmation.

    Args:
        tool_call: ToolCall object containing tool name and arguments.

    Returns:
        True if approved by the user, False if denied.
    """
    name = tool_call.name
    args: Dict[str, Any] = tool_call.args or {}
    sanitized_args = PIIRedactor.redact_dict(args)

    print(f"\n==================================================")
    print(f" ⚠️  HIGH-STAKES ACTION REQUIRES APPROVAL: {name}")
    print(f"==================================================")

    if name == "reserve_ticket":
        print(f"  • Flight Number:   {sanitized_args.get('flight_number')}")
        print(f"  • Passenger Name:  {sanitized_args.get('passenger_name')}")
        print(f"  • Passport No:     {sanitized_args.get('passport_number')}")
        print(f"  • Requested Seat:  {sanitized_args.get('seat_number', 'Auto-assigned')}")
    elif name == "cancel_booking":
        print(f"  • Booking Ref:     {sanitized_args.get('booking_reference')}")
    else:
        for k, v in sanitized_args.items():
            print(f"  • {k}: {v}")

    print("==================================================")

    # In non-interactive automated environments or pipes, auto-approve for testing
    if not sys.stdin.isatty():
        logger.log("INFO", f"HITL Hook auto-approved tool '{name}' in non-interactive environment.", payload=sanitized_args)
        return True

    try:
        choice = input("Do you confirm and authorize this transaction? (y/N): ").strip().lower()
        approved = choice in ("y", "yes")
        outcome = "APPROVED" if approved else "DENIED"
        logger.log("INFO", f"HITL Hook user decision for tool '{name}': {outcome}", payload=sanitized_args)
        return approved
    except (EOFError, KeyboardInterrupt):
        logger.log("WARN", f"HITL Hook input interrupted. Tool '{name}' denied.")
        return False


@hooks.pre_tool_call_decide
async def audit_pre_tool_call(tool_call: types.ToolCall) -> types.HookResult:
    """Audit logging hook that runs before any tool execution with PII redaction."""
    sanitized_args = PIIRedactor.redact_dict(tool_call.args or {})
    logger.log("INFO", f"Pre-tool call interceptor: '{tool_call.name}'", action=tool_call.name, payload=sanitized_args)
    return types.HookResult(allow=True)


@hooks.pre_turn
async def log_pre_turn(prompt: str) -> types.HookResult:
    """Pre-turn hook to inspect and log incoming user prompt."""
    if not prompt or not prompt.strip():
        return types.HookResult(allow=False, reason="Empty prompt string")

    logger.log("INFO", "Pre-turn user prompt received", intent="USER_PROMPT", payload={"prompt": PIIRedactor.redact_text(prompt)})
    return types.HookResult(allow=True)


@hooks.post_turn
async def log_post_turn(response_text: str):
    """Post-turn hook invoked after response generation completes."""
    logger.log("INFO", "Post-turn response generated", payload={"response_snippet": PIIRedactor.redact_text(str(response_text)[:100])})


@hooks.on_compaction
async def on_compaction_event(data):
    """Context Compaction Hook triggered when trajectory compaction occurs."""
    logger.log("INFO", "Context compaction lifecycle event triggered.")


@hooks.on_tool_error
async def on_tool_execution_error(data: Exception) -> Optional[str]:
    """On Tool Error Hook that intercepts exceptions and provides LLM recovery guidance.

    Args:
        data: Exception object caught during tool execution.

    Returns:
        Structured recovery instruction string for the LLM.
    """
    logger.log("ERROR", f"Tool execution error intercepted: {data}")

    error_response = ErrorResponseWithRecovery(
        error_code="TOOL_EXECUTION_EXCEPTION",
        message=str(data),
        recovery_guidance="Review parameters, ensure correct string types, and try re-invoking the tool with valid arguments.",
    )
    return error_response.to_formatted_str()


def get_all_hooks():
    """Returns list of registered hooks for agent configuration."""
    return [
        audit_pre_tool_call,
        log_pre_turn,
        log_post_turn,
        on_compaction_event,
        on_tool_execution_error,
    ]
