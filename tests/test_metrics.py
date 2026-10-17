from __future__ import annotations

import unittest

from tools.freshness.metrics import (
    calculate_metrics,
    compute_kaplan_meier,
    evaluate_survival_at,
)
from tools.freshness.state_tracker import FreshnessState, ListingRecord


class TestMetrics(unittest.TestCase):
    def test_kaplan_meier_mathematical_precision(self):
        """
        Verify Kaplan-Meier against an exact hand-calculated benchmark:
        10 listings observed starting at 2026-09-01:
        - 2 withdrawn at t=10 (withdrawn_date: 2026-09-11)
        - 2 active (censored) at t=15 (run_date: 2026-09-16) -> we set their run date for observation
        - 3 withdrawn at t=20 (withdrawn_date: 2026-09-21)
        - 3 active (censored) at t=30 (run_date: 2026-10-01)
        """
        run_date = "2026-10-01"
        records: list[ListingRecord] = []

        # 2 withdrawn at day 10
        for i in range(2):
            records.append(
                ListingRecord(
                    listing_id=f"W10_{i}",
                    first_seen="2026-09-01",
                    last_seen="2026-09-11",
                    posted="2026-09-01",
                    expires=None,
                    status="withdrawn",
                    withdrawn_date="2026-09-11",
                )
            )

        # 2 censored at day 15 (e.g. posted on 2026-09-16, active at 2026-10-01 -> duration 15)
        for i in range(2):
            records.append(
                ListingRecord(
                    listing_id=f"C15_{i}",
                    first_seen="2026-09-16",
                    last_seen="2026-10-01",
                    posted="2026-09-16",
                    expires=None,
                    status="active",
                )
            )

        # 3 withdrawn at day 20 (posted 2026-09-01, withdrawn 2026-09-21)
        for i in range(3):
            records.append(
                ListingRecord(
                    listing_id=f"W20_{i}",
                    first_seen="2026-09-01",
                    last_seen="2026-09-21",
                    posted="2026-09-01",
                    expires=None,
                    status="withdrawn",
                    withdrawn_date="2026-09-21",
                )
            )

        # 3 censored at day 30 (posted 2026-09-01, active at 2026-10-01)
        for i in range(3):
            records.append(
                ListingRecord(
                    listing_id=f"C30_{i}",
                    first_seen="2026-09-01",
                    last_seen="2026-10-01",
                    posted="2026-09-01",
                    expires=None,
                    status="active",
                )
            )

        curve, median_days = compute_kaplan_meier(records, run_date_str=run_date)

        # Hand calculations:
        # At t=10: n=10, d=2 -> S(10) = 1 - 2/10 = 0.8000
        # At t=15: 2 censored. At t=20, risk set is 10 - 2 - 2 = 6.
        # At t=20: n=6, d=3 -> S(20) = 0.8000 * (1 - 3/6) = 0.4000
        # At t=30: 3 censored -> S(30) = 0.4000
        # Median survival: first time S(t) <= 0.50 -> t=20
        self.assertAlmostEqual(curve[10], 0.8000, places=4)
        self.assertAlmostEqual(curve[20], 0.4000, places=4)
        self.assertEqual(median_days, 20.0)

        # Step function evaluations
        self.assertAlmostEqual(evaluate_survival_at(curve, 5), 1.0, places=4)
        self.assertAlmostEqual(evaluate_survival_at(curve, 10), 0.8000, places=4)
        self.assertAlmostEqual(evaluate_survival_at(curve, 15), 0.8000, places=4)
        self.assertAlmostEqual(evaluate_survival_at(curve, 20), 0.4000, places=4)
        self.assertAlmostEqual(evaluate_survival_at(curve, 30), 0.4000, places=4)

    def test_staleness_calculation(self):
        state = FreshnessState(slug="uradprace-cz", last_updated="2026-10-17", listings={})
        # 1 active unexpired
        state.listings["A1"] = ListingRecord("A1", "2026-10-01", "2026-10-17", "2026-10-01", "2026-10-31", "active")
        # 1 active expired (stale)
        state.listings["A2"] = ListingRecord("A2", "2026-09-01", "2026-10-17", "2026-09-01", "2026-10-10", "active")
        # 1 withdrawn (should not count in staleness)
        state.listings["W1"] = ListingRecord("W1", "2026-09-01", "2026-10-05", "2026-09-01", "2026-10-01", "withdrawn", "2026-10-05")

        metrics = calculate_metrics(state, run_date_str="2026-10-17")
        self.assertEqual(metrics.total_listings, 3)
        self.assertEqual(metrics.active_listings, 2)
        self.assertEqual(metrics.withdrawn_listings, 1)
        self.assertEqual(metrics.stale_active_count, 1)
        self.assertEqual(metrics.staleness_ratio, 50.0)

    def test_kaplan_meier_left_truncation_delayed_entry(self):
        """
        Verify that a listing posted prior to first_seen enters observation with delayed entry
        and does not inflate the risk set before its entry age.
        """
        run_date = "2026-10-01"
        # Listing 1: posted 2026-09-01, first_seen 2026-09-01 (entry_age=0), withdrawn 2026-09-11 (exit_age=10) -> event
        r1 = ListingRecord(
            listing_id="R1",
            first_seen="2026-09-01",
            posted="2026-09-01",
            status="withdrawn",
            withdrawn_date="2026-09-11",
        )
        # Listing 2: posted 2026-08-01, first_seen 2026-09-01 (entry_age=31), active at 2026-10-01 (exit_age=61)
        # R2 enters at t=31, so at t=10 it is NOT at risk.
        r2 = ListingRecord(
            listing_id="R2",
            first_seen="2026-09-01",
            posted="2026-08-01",
            status="active",
        )

        curve, median_days = compute_kaplan_meier([r1, r2], run_date_str=run_date)
        # At t=10: only R1 was at risk (n=1, d=1), so S(10) = 1 - 1/1 = 0.0000
        # If R2 were naively in the risk set without delayed entry, n would be 2 and S(10) would be 0.5000 (biased!)
        self.assertIn(10, curve)
        self.assertAlmostEqual(curve[10], 0.0000, places=4)
        self.assertEqual(median_days, 10.0)

    def test_age_distribution_and_expiry_coverage(self):
        state = FreshnessState(slug="uradprace-cz", last_updated="2026-10-17", listings={})
        # 1 listing posted 100 days ago (older than 90d) with expiry
        state.listings["A1"] = ListingRecord("A1", "2026-07-09", posted="2026-07-09", expires="2026-12-31", status="active")
        # 1 listing posted 200 days ago (older than 90d, 180d) without expiry
        state.listings["A2"] = ListingRecord("A2", "2026-03-31", posted="2026-03-31", expires=None, status="active")
        # 1 listing posted 400 days ago (older than 90d, 180d, 365d) without expiry
        state.listings["A3"] = ListingRecord("A3", "2025-09-12", posted="2025-09-12", expires=None, status="active")

        metrics = calculate_metrics(state, run_date_str="2026-10-17")
        self.assertEqual(metrics.active_listings, 3)
        self.assertEqual(metrics.count_older_90d, 3)
        self.assertEqual(metrics.count_older_180d, 2)
        self.assertEqual(metrics.count_older_365d, 1)
        self.assertAlmostEqual(metrics.share_older_90d, 100.0, places=2)
        self.assertAlmostEqual(metrics.share_older_180d, 66.67, places=2)
        self.assertAlmostEqual(metrics.share_older_365d, 33.33, places=2)
        self.assertAlmostEqual(metrics.expiry_coverage_ratio, 33.33, places=2)
        self.assertEqual(metrics.active_with_expiry, 1)


if __name__ == "__main__":
    unittest.main()
