from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.freshness.metrics import FreshnessMetrics
from tools.freshness.reporter import (
    generate_markdown_summary,
    generate_run_log,
    save_markdown_summary,
    save_run_log,
)


class TestReporter(unittest.TestCase):
    def test_markdown_summary_generation(self):
        metrics = FreshnessMetrics(
            total_listings=1500,
            active_listings=1200,
            withdrawn_listings=300,
            median_lifetime_days=42.5,
            survival_30d=0.7523,
            survival_60d=0.4812,
            survival_90d=0.2104,
            stale_active_count=24,
            schema_drift_detected=False,
            drift_warnings=[],
            share_older_90d=12.5,
            share_older_180d=6.0,
            share_older_365d=2.0,
            count_older_90d=150,
            count_older_180d=72,
            count_older_365d=24,
            expiry_coverage_ratio=65.0,
            active_with_expiry=780,
        )

        md = generate_markdown_summary(
            slug="uradprace-cz",
            source_name="Úřad práce ČR",
            endpoint="https://data.mpsv.cz/od/soubory/volna-mista/volna-mista.json",
            metrics=metrics,
            run_date="2026-10-17",
        )

        self.assertIn("Úřad práce ČR (`uradprace-cz`)", md)
        self.assertIn("1,500", md)
        self.assertIn("1,200", md)
        self.assertIn("42.5 days", md)
        self.assertIn("75.2%", md)
        self.assertIn("48.1%", md)
        self.assertIn("21.0%", md)
        self.assertIn("12.50% (150 listings)", md)
        self.assertIn("65.00% (780 listings)", md)
        self.assertIn("24 listings | Count of active vacancies whose stated expiry has passed", md)
        self.assertNotIn("staleness_ratio", md)
        self.assertNotIn("24 listings (2.00%)", md)
        self.assertIn("✅ PASS", md)

    def test_markdown_summary_with_drift(self):
        metrics = FreshnessMetrics(
            total_listings=10,
            active_listings=10,
            withdrawn_listings=0,
            median_lifetime_days=None,
            survival_30d=None,
            survival_60d=None,
            survival_90d=None,
            stale_active_count=0,
            schema_drift_detected=True,
            drift_warnings=["Expected key 'polozky' was renamed to 'items'."],
        )

        md = generate_markdown_summary(
            slug="uradprace-cz",
            source_name="Úřad práce ČR",
            endpoint="https://data.mpsv.cz/",
            metrics=metrics,
            run_date="2026-10-17",
        )

        self.assertIn("⚠️ DRIFT DETECTED", md)
        self.assertIn("Expected key 'polozky' was renamed", md)

    def test_run_log_generation(self):
        metrics = FreshnessMetrics(
            total_listings=50,
            active_listings=40,
            withdrawn_listings=10,
            median_lifetime_days=15.0,
            survival_30d=0.50,
            survival_60d=0.20,
            survival_90d=0.10,
            stale_active_count=2,
            schema_drift_detected=False,
            drift_warnings=[],
        )

        log_data = generate_run_log(
            slug="uradprace-cz",
            run_date="2026-10-17",
            metrics=metrics,
            raw_count=40,
        )

        self.assertEqual(log_data["slug"], "uradprace-cz")
        self.assertEqual(log_data["run_date"], "2026-10-17")
        self.assertEqual(log_data["raw_records_received"], 40)
        self.assertEqual(log_data["active_count"], 40)
        self.assertEqual(log_data["stale_active_count"], 2)
        self.assertNotIn("staleness_ratio", log_data)
        self.assertIn("timestamp_utc", log_data)


if __name__ == "__main__":
    unittest.main()
