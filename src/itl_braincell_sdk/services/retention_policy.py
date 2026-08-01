"""Retention policy engine for BrainCell memory cells.

For every save operation this module determines:
- Whether the content is worth storing at all (should_save)
- Why it should (or should not) be kept (reason)
- How long to keep it (retention_days; 0 = keep forever)

Rules are rule-based (no LLM call) so they add no latency.

Usage::

    from itl_braincell_sdk.services.retention_policy import evaluate

    result = evaluate("decisions", {"decision": "Use PostgreSQL", "rationale": "..."})
    if not result.should_save:
        return {"saved": False, "reason": result.reason}
    # else: create DB row using result.retention_days, result.reason, result.expires_at
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RetentionResult:
    """Result of a retention policy evaluation."""

    should_save: bool
    reason: str
    retention_days: int  # 0 = keep forever

    @property
    def expires_at(self) -> datetime | None:
        """UTC expiry timestamp, or None if the record should be kept forever."""
        if self.retention_days == 0:
            return None
        return datetime.now(tz=timezone.utc) + timedelta(days=self.retention_days)


# ---------------------------------------------------------------------------
# Per-cell default retention (days; 0 = forever)
# ---------------------------------------------------------------------------

CELL_DEFAULTS: dict[str, int] = {
    "interactions":       30,   # Raw messages — high volume, low individual value
    "conversations":      90,   # Conversation summaries
    "decisions":           0,   # Architectural decisions — permanent
    "architecture_notes":  0,   # Component documentation — permanent
    "notes":              60,   # Free-form notes
    "snippets":            0,   # Code patterns — permanent
    "files_discussed":    30,   # File references — refreshed on each encounter
    "sessions":           90,   # Work session summaries
    # National security intelligence — all permanent
    "threats":             0,
    "incidents":           0,
    "iocs":                0,
    "intel_reports":       0,
    # Vulnerability knowledge base — permanent
    "vuln_patches":        0,
    # Operational cells — permanent
    "tasks":              90,   # Done tasks expire; open/in-progress are set to 0 per-record
    "runbooks":            0,   # Operational procedures — permanent
    "api_contracts":       0,   # API specs — permanent
    "dependencies":        0,   # Package tracking — permanent
}

# ---------------------------------------------------------------------------
# Keywords that promote any content to permanent retention (0 days)
# ---------------------------------------------------------------------------

_PERMANENT_KEYWORDS: frozenset[str] = frozenset({
    "permanent", "forever", "never", "always",
    "critical", "important", "must", "required",
    "security", "breaking", "migration", "deprecat",
    "compliance", "audit", "production",
})

# ---------------------------------------------------------------------------
# Minimum content length thresholds (characters, across all field values)
# ---------------------------------------------------------------------------

_MIN_LENGTH: dict[str, int] = {
    "interactions": 8,
    "conversations": 10,
    "decisions": 10,
    "architecture_notes": 15,
    "notes": 5,
    "snippets": 10,
    "files_discussed": 3,   # file path alone is enough
    "sessions": 5,
}

_DEFAULT_MIN_LENGTH = 5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(cell_name: str, content: dict[str, Any]) -> RetentionResult:
    """Evaluate a content dict and return a RetentionResult.

    Args:
        cell_name: The cell identifier (e.g. ``"decisions"``, ``"interactions"``).
        content:   All field values that will be stored. Keys are field names.

    Returns:
        A :class:`RetentionResult` with ``should_save``, ``reason``, and
        ``retention_days``.  The caller is responsible for acting on the result.
    """
    default_days = CELL_DEFAULTS.get(cell_name, 60)
    min_len = _MIN_LENGTH.get(cell_name, _DEFAULT_MIN_LENGTH)

    # Flatten all text values for analysis
    text_parts = [str(v) for v in content.values() if v is not None and str(v).strip()]
    combined_text = " ".join(text_parts).strip()

    # --- Guard: content too short to be meaningful ---
    if len(combined_text) < min_len:
        return RetentionResult(
            should_save=False,
            reason=f"Content too short (< {min_len} chars) — not worth storing",
            retention_days=0,
        )

    # --- Cell-specific triage rules ---

    if cell_name == "interactions":
        result = _evaluate_interaction(content, combined_text, default_days)
        if result is not None:
            return result

    if cell_name == "conversations":
        result = _evaluate_conversation(content, combined_text, default_days)
        if result is not None:
            return result

    # --- Keyword-based promotion to permanent retention ---
    text_lower = combined_text.lower()
    matched = [kw for kw in _PERMANENT_KEYWORDS if kw in text_lower]
    if matched:
        return RetentionResult(
            should_save=True,
            reason=f"High-value keywords detected ({', '.join(sorted(matched))}) — retained permanently",
            retention_days=0,
        )

    # --- Default: save with cell-appropriate retention ---
    if default_days == 0:
        reason = f"Permanent {cell_name} record"
    else:
        reason = f"Standard {cell_name} — retain for {default_days} days"

    return RetentionResult(
        should_save=True,
        reason=reason,
        retention_days=default_days,
    )


# ---------------------------------------------------------------------------
# Cell-specific evaluation helpers (return None to fall through to defaults)
# ---------------------------------------------------------------------------

def _evaluate_interaction(
    content: dict[str, Any],
    combined_text: str,
    default_days: int,
) -> RetentionResult | None:
    role = str(content.get("role", "")).lower().strip()
    msg = str(content.get("content", "")).strip()

    # Very short system prompts are not useful to keep
    if role == "system" and len(msg) < 80:
        return RetentionResult(
            should_save=False,
            reason="Short system message — not worth storing",
            retention_days=0,
        )

    # Acknowledgement-only responses add no value
    trivial = {"ok", "okay", "yes", "no", "sure", "thanks", "thank you", "got it"}
    if msg.lower().strip().rstrip(".!") in trivial:
        return RetentionResult(
            should_save=False,
            reason="Trivial acknowledgement — no informational value",
            retention_days=0,
        )

    return None  # fall through to keyword/default check


def _evaluate_conversation(
    content: dict[str, Any],
    combined_text: str,
    default_days: int,
) -> RetentionResult | None:
    topic = str(content.get("topic", "")).strip()
    summary = str(content.get("summary", "")).strip()

    # A conversation with no summary and a very generic topic is not useful
    if not summary and len(topic) < 5:
        return RetentionResult(
            should_save=False,
            reason="Conversation has no summary and a trivial topic",
            retention_days=0,
        )

    return None
