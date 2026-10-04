"""Deterministic rules for transaction anomaly detection."""

from __future__ import annotations

import ipaddress
import math
from collections.abc import Iterable

from src.core.models import Transaction
from src.rules.base import BaseRule


def _validate_non_negative_number(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return float(value)


class HighAmountRule(BaseRule):
    """Flag transactions whose amount is strictly above a configured threshold."""

    default_score_impact = 35.0

    def __init__(
        self, threshold: float = 10_000.0, score_impact: float | None = None
    ) -> None:
        self.threshold = _validate_non_negative_number("threshold", threshold)
        super().__init__(score_impact)

    def evaluate(self, transaction: Transaction) -> dict:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")
        triggered = transaction.amount > self.threshold
        if triggered:
            details = (
                f"Amount {transaction.amount:.2f} exceeds threshold "
                f"{self.threshold:.2f} {transaction.currency}."
            )
        else:
            details = (
                f"Amount {transaction.amount:.2f} is at or below threshold "
                f"{self.threshold:.2f} {transaction.currency}."
            )
        return self._result(triggered, details)


class HighRiskCategoryRule(BaseRule):
    """Flag merchant categories found in a configurable blacklist."""

    default_score_impact = 35.0
    DEFAULT_BLACKLIST = frozenset(
        {"crypto_exchange", "gambling", "wire_transfer"}
    )

    def __init__(
        self,
        blacklisted_categories: Iterable[str] | None = None,
        score_impact: float | None = None,
    ) -> None:
        categories = (
            self.DEFAULT_BLACKLIST
            if blacklisted_categories is None
            else blacklisted_categories
        )
        normalized: set[str] = set()
        for category in categories:
            if not isinstance(category, str) or not category.strip():
                raise ValueError("blacklisted categories must be non-empty strings")
            normalized.add(category.strip().casefold())
        self.blacklisted_categories = frozenset(normalized)
        super().__init__(score_impact)

    def evaluate(self, transaction: Transaction) -> dict:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")
        category = transaction.merchant_category.strip()
        triggered = category.casefold() in self.blacklisted_categories
        if triggered:
            details = f"Merchant category {category!r} is on the high-risk blacklist."
        else:
            details = f"Merchant category {category!r} is not on the high-risk blacklist."
        return self._result(triggered, details)


class SuspiciousLocationRule(BaseRule):
    """Flag exact jurisdiction matches or IPs inside configured CIDR ranges.

    This rule does not perform geolocation. Supply the jurisdiction labels and
    IP ranges approved for the deployment using this rule.
    """

    default_score_impact = 35.0

    def __init__(
        self,
        flagged_jurisdictions: Iterable[str] | None = None,
        flagged_ip_ranges: Iterable[str] | None = None,
        score_impact: float | None = None,
    ) -> None:
        jurisdictions = flagged_jurisdictions or ()
        normalized: set[str] = set()
        for jurisdiction in jurisdictions:
            if not isinstance(jurisdiction, str) or not jurisdiction.strip():
                raise ValueError("flagged jurisdictions must be non-empty strings")
            normalized.add(jurisdiction.strip().casefold())
        self.flagged_jurisdictions = frozenset(normalized)

        ranges = flagged_ip_ranges or ()
        try:
            self.flagged_ip_networks = tuple(
                ipaddress.ip_network(network, strict=False) for network in ranges
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("flagged_ip_ranges must contain valid CIDR ranges") from exc
        super().__init__(score_impact)

    def evaluate(self, transaction: Transaction) -> dict:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction")

        location = transaction.location.strip()
        if location.casefold() in self.flagged_jurisdictions:
            return self._result(
                True, f"Location {location!r} matches a flagged jurisdiction."
            )

        ip_text = transaction.ip_address.strip()
        if ip_text:
            try:
                address = ipaddress.ip_address(ip_text)
            except ValueError:
                address = None
            if address is not None:
                for network in self.flagged_ip_networks:
                    if address.version == network.version and address in network:
                        return self._result(
                            True,
                            f"IP address {ip_text!r} matches flagged range {str(network)!r}.",
                        )

        return self._result(
            False, "Neither the location nor IP address matches configured indicators."
        )
