"""Security Guardrails and Safety Policies for Airplane Ticket Concierge Agent.

This module provides input validation, guardrail predicates, and policy definitions
for controlling access to tool execution and protecting user sensitive data (e.g. passport info, PNRs).
"""

import re
from typing import Callable, List, Optional
from google.antigravity import types
from google.antigravity.hooks import policy

# Regex pattern for valid passport numbers (6 to 12 alphanumeric characters)
PASSPORT_REGEX = re.compile(r"^[A-Za-z0-9]{6,12}$")

# Regex pattern for valid 6-character PNR booking references
PNR_REGEX = re.compile(r"^[A-Za-z0-9]{6}$")

# Disallowed prompt injection strings or unsafe patterns in inputs
INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "system prompt",
    "override",
    "sudo",
    "drop table",
    "<script>",
]


def validate_passport_number(passport_number: str) -> bool:
    """Validates passport number format and guards against injection.

    Args:
        passport_number: The passport string provided by the user.

    Returns:
        True if valid and safe, False otherwise.
    """
    if not passport_number or not isinstance(passport_number, str):
        return False

    passport_clean = passport_number.strip()

    # Check length and alphanumeric format
    if not PASSPORT_REGEX.match(passport_clean):
        return False

    # Guard against prompt injection keywords
    for keyword in INJECTION_KEYWORDS:
        if keyword in passport_clean.lower():
            return False

    return True


def validate_pnr_code(pnr: str) -> bool:
    """Validates 6-character PNR booking reference format.

    Args:
        pnr: The PNR string provided by the user.

    Returns:
        True if valid 6-character alphanumeric format, False otherwise.
    """
    if not pnr or not isinstance(pnr, str):
        return False

    return bool(PNR_REGEX.match(pnr.strip()))


def create_security_policies(approval_handler: Optional[Callable] = None) -> List[types.PolicyRule]:
    """Builds a declarative priority-ordered list of security policy rules.

    Safety Policy Precedence:
    1. Specific Deny: Deny reservations with invalid or malicious passport credentials.
    2. Specific Ask: Require Human-in-the-Loop approval for high-stakes tools (reserve, cancel).
    3. Specific Allow: Allow safe read-only tools (search, details, seat map, baggage).

    Args:
        approval_handler: Custom async function to handle user approval prompts for ask_user.

    Returns:
        List of PolicyRule objects configured for AGY LocalAgentConfig.
    """
    rules = [
        # Guardrail 1: Deny ticket reservations if passport number fails validation
        policy.deny(
            "reserve_ticket",
            when=lambda args: not validate_passport_number(args.get("passport_number", "")),
            name="deny_invalid_passport_format",
        ),
        # Guardrail 2: Human-In-The-Loop approval required for high-stakes reservation actions
        policy.ask_user(
            "reserve_ticket",
            handler=approval_handler,
        ),
        # Guardrail 3: Human-In-The-Loop approval required for booking cancellation actions
        policy.ask_user(
            "cancel_booking",
            handler=approval_handler,
        ),
        # Guardrail 4: Allow read-only search and inquiry tools without confirmation
        policy.allow("search_flights"),
        policy.allow("get_flight_details"),
        policy.allow("check_seat_map"),
        policy.allow("calculate_baggage_fees"),
        policy.allow("get_booking_details"),
    ]

    return rules
