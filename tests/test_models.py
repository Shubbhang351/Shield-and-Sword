import unittest

from src.core.models import (
    EmailPayload,
    RiskAction,
    RiskEvaluation,
    RiskSeverity,
    Transaction,
)


class TestModels(unittest.TestCase):
    def test_transaction_creation(self) -> None:
        tx = Transaction(
            transaction_id="tx_100",
            user_id="user_42",
            amount=250.50,
            currency="USD",
            ip_address="192.168.1.1",
            merchant_category="retail",
            location="US-CA",
        )
        self.assertEqual(tx.transaction_id, "tx_100")
        self.assertEqual(tx.user_id, "user_42")
        self.assertEqual(tx.amount, 250.50)
        self.assertEqual(tx.currency, "USD")
        self.assertTrue(tx.is_tz_aware)
        self.assertEqual(tx.ip_address, "192.168.1.1")

    def test_transaction_validation(self) -> None:
        with self.assertRaises(ValueError):
            Transaction(transaction_id="tx_1", user_id="u_1", amount=-10.0)

        with self.assertRaises(ValueError):
            Transaction(transaction_id="", user_id="u_1", amount=10.0)

    def test_email_payload_creation(self) -> None:
        email = EmailPayload(
            payload_id="em_500",
            sender="attacker@phish.com",
            subject="Urgent Account Verification",
            body_text="Click here to verify your account.",
            headers={"X-Mailer": "CustomScript"},
        )
        self.assertEqual(email.payload_id, "em_500")
        self.assertEqual(email.sender, "attacker@phish.com")
        self.assertEqual(email.header("x-mailer"), "CustomScript")
        self.assertEqual(email.header("missing", default="default"), "default")

    def test_email_payload_validation(self) -> None:
        with self.assertRaises(ValueError):
            EmailPayload(
                payload_id="em_1",
                sender="  ",
                subject="Sub",
                body_text="Body",
            )

    def test_risk_severity_mapping(self) -> None:
        self.assertEqual(RiskSeverity.from_score(10.0), RiskSeverity.LOW)
        self.assertEqual(RiskSeverity.from_score(30.0), RiskSeverity.MEDIUM)
        self.assertEqual(RiskSeverity.from_score(60.0), RiskSeverity.HIGH)
        self.assertEqual(RiskSeverity.from_score(90.0), RiskSeverity.CRITICAL)

        with self.assertRaises(ValueError):
            RiskSeverity.from_score(150.0)

    def test_risk_evaluation(self) -> None:
        evaluation = RiskEvaluation(
            entity_id="tx_100",
            rule_score=60.0,
            llm_score=80.0,
            action=RiskAction.REVIEW,
            triggered_rules=["RULE_HIGH_AMOUNT"],
            summary="High amount transaction from new IP.",
        )
        self.assertEqual(evaluation.final_score, 68.0)
        self.assertEqual(evaluation.severity, RiskSeverity.HIGH)
        self.assertEqual(evaluation.action, RiskAction.REVIEW)

        d = evaluation.to_dict()
        self.assertEqual(d["entity_id"], "tx_100")
        self.assertEqual(d["rule_score"], 60.0)
        self.assertEqual(d["llm_score"], 80.0)
        self.assertEqual(d["final_score"], 68.0)
        self.assertEqual(d["action"], "REVIEW")
        self.assertEqual(d["severity"], "HIGH")
        self.assertEqual(d["triggered_rules"], ["RULE_HIGH_AMOUNT"])
        self.assertEqual(d["summary"], "High amount transaction from new IP.")


if __name__ == "__main__":
    unittest.main()
