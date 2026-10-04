"""Canonical data models for the Shield & Sword risk engine.

These models are the shared contract between the statistical rule layer, the
local/cloud LLM layers, and the orchestration pipeline. They are implemented
with the standard library `dataclasses` module so that the initial scaffold
carries no third-party dependencies; validation is enforced in `__post_init__`
so malformed entities are rejected at the boundary rather than deep inside the
pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final

__all__ = [
    "RiskAction",
    "RiskEvaluation",
    "RiskSeverity",
    "Transaction",
    "EmailPayload",
    "SCORE_MIN",
    "SCORE_MAX",
    "RULE_SCORE_WEIGHT",
]

SCORE_MIN: Final[float] = 0.0
SCORE_MAX: Final[float] = 100.0

RULE_SCORE_WEIGHT: Final[float] = 0.6


class RiskSeverity(str, Enum):
    """Qualitative risk band derived from a numeric risk score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_score(cls, score: float) -> "RiskSeverity":
        """Map a 0-100 risk score onto a severity band."""
        _validate_score("score", score)
        if score < 25.0:
            return cls.LOW
        if score < 50.0:
            return cls.MEDIUM
        if score < 75.0:
            return cls.HIGH
        return cls.CRITICAL


class RiskAction(str, Enum):
    """Disposition applied to an entity once its risk is scored."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


def _validate_score(field_name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a number, got {type(value).__name__}")
    if not SCORE_MIN <= float(value) <= SCORE_MAX:
        raise ValueError(
            f"{field_name} must be between {SCORE_MIN} and {SCORE_MAX}, got {value}"
        )
    return float(value)


def _require_identifier(field_name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Transaction:
    """A retail payment event submitted for risk analysis."""

    transaction_id: str
    user_id: str
    amount: float
    currency: str = "USD"
    timestamp: datetime = field(default_factory=_utc_now)
    ip_address: str = ""
    merchant_category: str = ""
    location: str = ""

    def __post_init__(self) -> None:
        _require_identifier("transaction_id", self.transaction_id)
        _require_identifier("user_id", self.user_id)
        if not isinstance(self.amount, (int, float)) or isinstance(self.amount, bool):
            raise TypeError(
                f"amount must be a number, got {type(self.amount).__name__}"
            )
        if self.amount < 0:
            raise ValueError(f"amount must be non-negative, got {self.amount}")
        if not isinstance(self.timestamp, datetime):
            raise TypeError(
                f"timestamp must be a datetime, got {type(self.timestamp).__name__}"
            )
        _require_identifier("currency", self.currency)

    @property
    def is_tz_aware(self) -> bool:
        """Whether the timestamp carries timezone information."""
        return self.timestamp.tzinfo is not None


@dataclass(frozen=True, slots=True)
class EmailPayload:
    """An inbound email submitted for threat and phishing analysis."""

    payload_id: str
    sender: str
    subject: str
    body_text: str
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_identifier("payload_id", self.payload_id)
        _require_identifier("sender", self.sender)
        if not isinstance(self.subject, str):
            raise TypeError(f"subject must be a string, got {type(self.subject).__name__}")
        if not isinstance(self.body_text, str):
            raise TypeError(
                f"body_text must be a string, got {type(self.body_text).__name__}"
            )
        if not isinstance(self.headers, dict):
            raise TypeError(f"headers must be a dict, got {type(self.headers).__name__}")

    def header(self, name: str, default: str = "") -> str:
        """Case-insensitive header lookup."""
        target = name.lower()
        for key, value in self.headers.items():
            if key.lower() == target:
                return value
        return default


@dataclass(slots=True)
class RiskEvaluation:
    """Aggregated risk verdict for a single entity.

    `rule_score` comes from the deterministic statistical layer, `llm_score`
    from the LLM layer, and `final_score` is their weighted blend. When
    `final_score` is omitted it is derived automatically using
    `RULE_SCORE_WEIGHT`.
    """

    entity_id: str
    rule_score: float = 0.0
    llm_score: float = 0.0
    final_score: float | None = None
    action: RiskAction | str = RiskAction.ALLOW
    triggered_rules: list[str] = field(default_factory=list)
    summary: str = ""

    def __post_init__(self) -> None:
        _require_identifier("entity_id", self.entity_id)
        object.__setattr__(self, "rule_score", _validate_score("rule_score", self.rule_score))
        object.__setattr__(self, "llm_score", _validate_score("llm_score", self.llm_score))

        if self.final_score is None:
            object.__setattr__(self, "final_score", self.blended_score())
        else:
            object.__setattr__(
                self, "final_score", _validate_score("final_score", self.final_score)
            )

        object.__setattr__(self, "action", RiskAction(self.action))
        if not isinstance(self.triggered_rules, list):
            raise TypeError(
                "triggered_rules must be a list, got "
                f"{type(self.triggered_rules).__name__}"
            )
        if not isinstance(self.summary, str):
            raise TypeError(f"summary must be a string, got {type(self.summary).__name__}")

    def blended_score(self) -> float:
        """Weighted blend of the rule and LLM scores."""
        return round(
            self.rule_score * RULE_SCORE_WEIGHT
            + self.llm_score * (1.0 - RULE_SCORE_WEIGHT),
            4,
        )

    @property
    def severity(self) -> RiskSeverity:
        """Severity band for the current final score."""
        return RiskSeverity.from_score(self.final_score)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serialisable representation, suitable for LLM prompting."""
        return {
            "entity_id": self.entity_id,
            "rule_score": self.rule_score,
            "llm_score": self.llm_score,
            "final_score": self.final_score,
            "action": self.action.value,
            "severity": self.severity.value,
            "triggered_rules": list(self.triggered_rules),
            "summary": self.summary,
        }