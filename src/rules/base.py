"""Shared interface for deterministic transaction risk rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from typing import Any

from src.core.models import Transaction


class BaseRule(ABC):
    """Abstract contract implemented by each deterministic risk rule."""

    default_score_impact = 0.0

    def __init__(self, score_impact: float | None = None) -> None:
        impact = self.default_score_impact if score_impact is None else score_impact
        if isinstance(impact, bool) or not isinstance(impact, (int, float)):
            raise TypeError("score_impact must be a number")
        if not math.isfinite(float(impact)) or impact < 0:
            raise ValueError("score_impact must be finite and non-negative")
        self.score_impact = float(impact)

    @property
    def rule_name(self) -> str:
        """Stable, human-readable name for this concrete rule."""
        return type(self).__name__

    def _result(self, triggered: bool, details: str) -> dict[str, Any]:
        """Build the common result shape required by the rule interface."""
        return {
            "rule_name": self.rule_name,
            "triggered": triggered,
            "score_impact": self.score_impact if triggered else 0.0,
            "details": details,
        }

    @abstractmethod
    def evaluate(self, transaction: Transaction) -> dict:
        """Evaluate one transaction and return the standard rule result."""
        raise NotImplementedError
