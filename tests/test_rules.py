import unittest

from src.core.models import Transaction
from src.rules import (
    HighAmountRule,
    HighRiskCategoryRule,
    RuleEngine,
    SuspiciousLocationRule,
)


class TestTransactionRules(unittest.TestCase):
    def make_transaction(self, **overrides: object) -> Transaction:
        values: dict[str, object] = {
            "transaction_id": "tx_rules",
            "user_id": "user_1",
            "amount": 125.00,
            "currency": "USD",
            "ip_address": "198.51.100.8",
            "merchant_category": "groceries",
            "location": "US",
        }
        values.update(overrides)
        return Transaction(**values)  # type: ignore[arg-type]

    def test_clean_transaction_has_zero_score(self) -> None:
        engine = RuleEngine(
            [
                HighAmountRule(),
                HighRiskCategoryRule(),
                SuspiciousLocationRule(
                    flagged_jurisdictions={"IR"},
                    flagged_ip_ranges={"203.0.113.0/24"},
                ),
            ]
        )

        result = engine.evaluate_transaction(self.make_transaction())

        self.assertEqual(result["rule_score"], 0.0)
        self.assertEqual(result["triggered_rules"], [])
        self.assertEqual(result["details"], [])

    def test_fraud_like_transaction_triggers_rules_and_caps_score(self) -> None:
        engine = RuleEngine(
            [
                HighAmountRule(threshold=10_000),
                HighRiskCategoryRule(),
                SuspiciousLocationRule(
                    flagged_jurisdictions={"IR"},
                    flagged_ip_ranges={"203.0.113.0/24"},
                ),
            ]
        )
        transaction = self.make_transaction(
            amount=15_000.00,
            merchant_category="Crypto_Exchange",
            location="IR",
            ip_address="203.0.113.42",
        )

        result = engine.evaluate_transaction(transaction)

        self.assertEqual(
            result["triggered_rules"],
            ["HighAmountRule", "HighRiskCategoryRule", "SuspiciousLocationRule"],
        )
        self.assertEqual(result["rule_score"], 100.0)
        self.assertEqual(len(result["details"]), 3)
        self.assertTrue(all(detail["details"] for detail in result["details"]))

    def test_high_amount_threshold_is_exclusive(self) -> None:
        rule = HighAmountRule(threshold=10_000)

        result = rule.evaluate(self.make_transaction(amount=10_000))

        self.assertFalse(result["triggered"])
        self.assertEqual(result["score_impact"], 0.0)

    def test_high_risk_category_is_case_insensitive(self) -> None:
        result = HighRiskCategoryRule().evaluate(
            self.make_transaction(merchant_category="GAMBLING")
        )

        self.assertTrue(result["triggered"])

    def test_suspicious_location_matches_configured_ip_range(self) -> None:
        rule = SuspiciousLocationRule(flagged_ip_ranges={"203.0.113.0/24"})

        result = rule.evaluate(self.make_transaction(ip_address="203.0.113.10"))

        self.assertTrue(result["triggered"])
        self.assertIn("203.0.113.0/24", result["details"])

    def test_engine_rejects_duplicate_rule_names(self) -> None:
        engine = RuleEngine([HighAmountRule()])
        with self.assertRaises(ValueError):
            engine.register_rule(HighAmountRule())


if __name__ == "__main__":
    unittest.main()
