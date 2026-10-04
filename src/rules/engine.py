"""Registration and aggregation for deterministic transaction rules."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from src.core.models import Transaction
from src.rules.base import BaseRule


class RuleEngine:
    """Execute registered rules and aggregate their positive score impacts."""

    def __init__(self, rules: Iterable[BaseRule] = ()) -> None:
        self._rules: list[BaseRule] = []
        for rule in rules:
            self.register_rule(rule)

    @property
    def rules(self) -> tuple[BaseRule, ...]:
        """The currently registered rules, in execution order."""
        return tuple(self._rules)

    def register_rule(self, rule: BaseRule) -> None:
        """Register a rule, rejecting invalid objects and duplicate names."""
        if not isinstance(rule, BaseRule):
            raise TypeError("rule must be an instance of BaseRule")
        if any(existing.rule_name == rule.rule_name for existing in self._rules):
            raise ValueError(f"rule {rule.rule_name!r} is already registered")
        self._rules.append(rule)

    def evaluate_transaction(self, transaction: Transaction) -> dict[str, Any]:
        """Run rules and return a capped score with triggered names and details."""
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")

        score = 0.0
        triggered_rules: list[str] = []
        details: list[dict[str, str | float]] = []

        for rule in self._rules:
            result = rule.evaluate(transaction)
            if not isinstance(result, dict):
                raise TypeError(f"{rule.rule_name} must return a dictionary")
            required = {"rule_name", "triggered", "score_impact", "details"}
            if not required.issubset(result):
                raise ValueError(
                    f"{rule.rule_name} result must include {sorted(required)}"
                )
            if result["rule_name"] != rule.rule_name:
                raise ValueError("rule result name must match its registered rule")
            if not isinstance(result["triggered"], bool):
                raise TypeError("rule result triggered must be a bool")
            if not isinstance(result["details"], str):
                raise TypeError("rule result details must be a string")
            impact = result["score_impact"]
            if isinstance(impact, bool) or not isinstance(impact, (int, float)):
                raise TypeError("rule result score_impact must be a number")
            if not math.isfinite(float(impact)) or impact < 0:
                raise ValueError("rule result score_impact must be finite and non-negative")

            if result["triggered"]:
                impact_value = float(impact)
                score += impact_value
                triggered_rules.append(rule.rule_name)
                details.append(
                    {
                        "rule_name": rule.rule_name,
                        "score_impact": impact_value,
                        "details": result["details"],
                    }
                )

        return {
            "transaction_id": transaction.transaction_id,
            "rule_score": round(min(100.0, max(0.0, score)), 4),
            "triggered_rules": triggered_rules,
            "details": details,
        }
