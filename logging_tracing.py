"""Distributed Tracing & Context Propagation with Structured JSON Logging and PII Redaction.

Implements OpenTelemetry-compatible distributed trace context propagation across turns,
subagents, and tool calls using Python's contextvars.
Maintains root trace_id, current span_id, and parent_span_id to form a fully linked
hierarchical execution span graph.
"""

import contextvars
import json
import logging
import re
import time
import uuid
from typing import Any, Dict, Optional

# Context Variables for OpenTelemetry Trace Context Propagation
_current_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_trace_id", default=None)
_current_span_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_span_id", default=None)
_current_parent_span_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_parent_span_id", default=None)

# Regex patterns for matching PII data
PASSPORT_PATTERN = re.compile(r"\b[A-Za-z0-9]{6,12}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def get_current_trace_context() -> Dict[str, Optional[str]]:
    """Returns the current active distributed trace context (trace_id, span_id, parent_span_id)."""
    trace_id = _current_trace_id.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())
        _current_trace_id.set(trace_id)

    return {
        "trace_id": trace_id,
        "span_id": _current_span_id.get() or "root",
        "parent_span_id": _current_parent_span_id.get(),
    }


def start_trace(trace_id: Optional[str] = None) -> str:
    """Starts a new root trace context or sets the active trace_id."""
    active_id = trace_id or str(uuid.uuid4())
    _current_trace_id.set(active_id)
    _current_span_id.set("root")
    _current_parent_span_id.set(None)
    return active_id


class PIIRedactor:
    """Utility class to sanitize and redact PII from text and structured payloads."""

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redacts sensitive PII from a text string."""
        if not text or not isinstance(text, str):
            return text

        redacted = SSN_PATTERN.sub("[REDACTED_SSN]", text)
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
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        intent: Optional[str] = None,
        action: Optional[str] = None,
        outcome: Optional[str] = None,
        duration_ms: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Emits a structured JSON log entry with propagated trace context and PII redaction."""
        ctx = get_current_trace_context()
        active_trace_id = trace_id or ctx["trace_id"]
        active_span_id = span_id or ctx["span_id"]
        active_parent_span_id = parent_span_id or ctx["parent_span_id"]

        sanitized_payload = PIIRedactor.redact_dict(payload) if payload else {}

        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service": self.service_name,
            "trace_id": active_trace_id,
            "span_id": active_span_id,
            "parent_span_id": active_parent_span_id,
            "level": level.upper(),
            "message": PIIRedactor.redact_text(message),
            "intent": intent or "N/A",
            "action": action or "N/A",
            "outcome": outcome or "N/A",
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
            "payload": sanitized_payload,
        }

        json_output = json.dumps(log_entry)
        if level.upper() == "ERROR":
            self.logger.error(json_output)
        else:
            self.logger.info(json_output)


# Singleton logger instance
logger = StructuredLogger()


class TraceSpan:
    """Context Manager for OpenTelemetry-compatible Span Linkage & Context Propagation.

    Automatically links parent_span_id -> span_id within the active root trace_id graph.
    """

    def __init__(self, span_name: str, intent: Optional[str] = None, payload: Optional[Dict[str, Any]] = None):
        self.span_name = span_name
        self.intent = intent or span_name
        self.payload = payload or {}
        self.span_id = str(uuid.uuid4())[:8]
        self.start_time = 0.0
        self.token_parent = None
        self.token_span = None

    def __enter__(self):
        ctx = get_current_trace_context()
        self.trace_id = ctx["trace_id"]
        parent_id = ctx["span_id"]

        self.token_parent = _current_parent_span_id.set(parent_id)
        self.token_span = _current_span_id.set(self.span_id)

        self.start_time = time.time()
        logger.log(
            level="INFO",
            message=f"Span STARTED: '{self.span_name}'",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=parent_id,
            intent=self.intent,
            action=self.span_name,
            outcome="STARTED",
            payload=self.payload,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        outcome = "ERROR" if exc_type else "SUCCESS"
        parent_id = _current_parent_span_id.get()

        logger.log(
            level="ERROR" if exc_type else "INFO",
            message=f"Span ENDED: '{self.span_name}' ({outcome})",
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=parent_id,
            intent=self.intent,
            action=self.span_name,
            outcome=outcome,
            duration_ms=duration_ms,
            payload=self.payload,
        )

        if self.token_parent:
            _current_parent_span_id.reset(self.token_parent)
        if self.token_span:
            _current_span_id.reset(self.token_span)

        return False


def log_tool_intent_and_outcome(
    intent: str,
    action: str,
    outcome: str,
    duration_ms: float,
    payload: Dict[str, Any],
    trace_id: Optional[str] = None,
):
    """Convenience helper to record Intent vs. Outcome log events linked to active trace context."""
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
