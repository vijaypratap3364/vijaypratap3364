from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunabot.contributions import normalize_graphql_response, validate_normalized_calendar


class ContributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (ROOT / "tests/fixtures/graphql_response.json").read_text(encoding="utf-8")
        )

    def test_normalizes_graphql_calendar(self) -> None:
        calendar = normalize_graphql_response(self.payload, "vijaypratap3364")
        self.assertEqual(calendar["totalContributions"], 26)
        self.assertEqual(calendar["stats"]["activeDays"], 6)
        self.assertEqual(calendar["stats"]["maxDailyContributions"], 10)
        validate_normalized_calendar(calendar)

    def test_rejects_total_mismatch(self) -> None:
        calendar = normalize_graphql_response(self.payload, "vijaypratap3364")
        calendar["totalContributions"] += 1
        with self.assertRaises(ValueError):
            validate_normalized_calendar(calendar)


if __name__ == "__main__":
    unittest.main()
