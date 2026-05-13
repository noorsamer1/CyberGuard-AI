"""Unit tests for incident portfolio aggregation helpers and schemas."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.schemas.incident_portfolio import PortfolioAIOut
from app.services.incident_portfolio_service import detect_spike_last_period


class DetectSpikeTests(unittest.TestCase):
    """Tests for weekly volume spike detection (used in portfolio stats)."""

    def test_too_few_buckets(self) -> None:
        self.assertFalse(detect_spike_last_period([{"count": 1}, {"count": 2}, {"count": 3}]))

    def test_no_spike_flat(self) -> None:
        weeks = [{"week_start": f"w{i}", "count": 2} for i in range(5)]
        self.assertFalse(detect_spike_last_period(weeks))

    def test_spike_when_last_doubles_baseline_and_exceeds_prior_max(self) -> None:
        weeks = [
            {"week_start": "w0", "count": 2},
            {"week_start": "w1", "count": 2},
            {"week_start": "w2", "count": 2},
            {"week_start": "w3", "count": 10},
        ]
        self.assertTrue(detect_spike_last_period(weeks))

    def test_high_last_not_spike_if_not_double_baseline(self) -> None:
        weeks = [
            {"week_start": "w0", "count": 5},
            {"week_start": "w1", "count": 5},
            {"week_start": "w2", "count": 5},
            {"week_start": "w3", "count": 7},
        ]
        self.assertFalse(detect_spike_last_period(weeks))


class PortfolioAIOutSchemaTests(unittest.TestCase):
    """Contract tests for structured LLM output validation."""

    def test_accepts_minimal_valid_payload(self) -> None:
        out = PortfolioAIOut.model_validate(
            {
                "executive_summary": "Summary.",
                "key_findings": ["a"],
                "risks": [],
                "recommendations": ["r1"],
                "themes": [],
            }
        )
        self.assertEqual(out.executive_summary, "Summary.")
        self.assertEqual(out.key_findings, ["a"])

    def test_rejects_wrong_field_types(self) -> None:
        with self.assertRaises(ValidationError):
            PortfolioAIOut.model_validate(
                {
                    "executive_summary": "ok",
                    "key_findings": "not-a-list",
                    "risks": [],
                    "recommendations": [],
                    "themes": [],
                }
            )


if __name__ == "__main__":
    unittest.main()
