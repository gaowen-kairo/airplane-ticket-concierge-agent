"""Structured JSON Logging, Tracing, Intent vs Outcome Logger, and PII Redactor.

Provides enterprise-grade observability with structured JSON log formatting,
OpenTelemetry-compatible trace IDs, intent vs. outcome tracking, and automatic PII redaction
(passport numbers, credit cards, SSNs, sensitive credentials).
"""

import json
import logging
import re
import time
import uuid
from typing import Any, Dict, Optional

# Regex patterns for matching PII data
PASSPORT_PATTERN = re.compile(r"\b[A-Za-z0-9]{6,12}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


class PIIRedactor:
    """Utility class to sanitize and redact PII from text and structured payloads."""

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive PII from a text string."""
        if not text or not isinstance(text, str):
            return text

        # Redact SSNs
        redacted = SSN_PATTERN.sub("[REDACTED_SSN]", text)
        # Redact Credit Cards
        redacted = CREDIT_CARD_PATTERN.sub("[REDACTED_CC]", redacted)
        return redacted

    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitizes a payload dictionary, masking sensitive fields."""
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, val in data.items():
            key_lower = str(key).lower()
            if "passport" in key_lower:
                # Mask passport number showing only first 3 chars
                str_val = str(val)
                sanitized[key] = str_val[:3] + "****" if len(str_val) > 3 else "****"
            elif any(k in key_lower for k in ("credit_card", "card_number", "ssn", "secret", "password")):
                sanitized[key] = "[REDACTED]"
            elif isinstance(val, dict):
                sanitized[key] = cls.redact_dict(val)
            elif isinstance(val, list):
                sanitized[key] = [cls.redact_dict(item) if isinstance(item, dict) else cls.redact_text(str(item)) for item in val]
            elif isinstance(val, str):
                sanitized[key] = cls.redact_text(val)
            else:
                sanitized[key] = val

        return sanitized


class StructuredLogger:
    """Structured JSON Logger for OpenTelemetry-compatible tracing and observability."""

    def __init__(self, service_name: str = "SkyConcierge"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        intent: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        duration_ms: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Emits a structured JSON log entry with PII redaction."""
        trace = trace_id or str(uuid.uuid4())
        sanitized_payload = PIIRedactor.redact_dict(payload) if payload else {}

        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": self.service_name,
            "trace_id": trace,
            "level": level.upper(),
            "message": PIIRedactor.redact_text(message),
            "intent": intent or "N/A",
            "action": action or "N/A",
            "outcome": outcome or "N/A",
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "payload": sanitized_payload,
        }

        # Print cleanly formatted JSON log string
        json_output = json.dumps(log_entry)
        if level.upper() == "ERROR":
            self.logger.error(json_output)
        else:
            self.logger.info(json_output)


# Singleton logger instance
logger = StructuredLogger()


def log_tool_intent_and_outcome(
    intent: str,
    action: str,
    outcome: str,
    duration_ms: float,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
):
    """Convenience helper to record Intent vs. Outcome log events."""
    logger.log(
        level="INFO" if outcome.upper() == "SUCCESS" else "WARN",
        message=f"Action '{action}' executed with outcome '{outcome}'",
        trace_id=trace_id,
        intent=intent,
        action=action,
        outcome=outcome,
        duration_ms=duration_ms,
        payload=payload,
    )
