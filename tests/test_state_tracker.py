from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.freshness.parser import ParsedListing
from tools.freshness.state_tracker import (
    FreshnessState,
    ListingRecord,
    load_state,
    save_state,
    update_state,
)


class TestStateTracker(unittest.TestCase):
    def test_full_snapshot_addition_and_withdrawal(self):
        state = FreshnessState(slug="uradprace-cz", last_updated="", listings={})

        # Day 1: 3 listings
        day1_listings = [
            ParsedListing("L1", posted="2026-09-01", updated=None, expires=None),
            ParsedListing("L2", posted="2026-09-01", updated=None, expires=None),
            ParsedListing("L3", posted="2026-09-01", updated=None, expires=None),
        ]
        update_state(state, day1_listings, run_date="2026-09-01", is_incremental=False)

        self.assertEqual(len(state.listings), 3)
        self.assertTrue(all(r.status == "active" for r in state.listings.values()))

        # Day 2: L1 and L3 still present, L2 absent (withdrawn)
        day2_listings = [
            ParsedListing("L1", posted="2026-09-01", updated="2026-09-02", expires=None),
            ParsedListing("L3", posted="2026-09-01", updated="2026-09-02", expires=None),
        ]
        update_state(state, day2_listings, run_date="2026-09-02", is_incremental=False)

        self.assertEqual(state.listings["L1"].status, "active")
        self.assertEqual(state.listings["L1"].last_seen, "2026-09-02")
        self.assertEqual(state.listings["L2"].status, "withdrawn")
        self.assertEqual(state.listings["L2"].withdrawn_date, "2026-09-02")
        self.assertEqual(state.listings["L3"].status, "active")

    def test_incremental_deletion(self):
        state = FreshnessState(slug="uradprace-cz", last_updated="", listings={})

        # Insert L1
        update_state(
            state,
            [ParsedListing("L1", posted="2026-09-01", updated=None, expires=None, operation="add")],
            run_date="2026-09-01",
            is_incremental=True,
        )
        self.assertEqual(state.listings["L1"].status, "active")

        # Explicit delete L1
        update_state(
            state,
            [ParsedListing("L1", posted=None, updated=None, expires=None, operation="delete")],
            run_date="2026-09-10",
            is_incremental=True,
        )
        self.assertEqual(state.listings["L1"].status, "withdrawn")
        self.assertEqual(state.listings["L1"].withdrawn_date, "2026-09-10")

    def test_pruning_retention(self):
        state = FreshnessState(slug="uradprace-cz", last_updated="", listings={})
        # L_old withdrawn 200 days ago
        state.listings["L_old"] = ListingRecord(
            listing_id="L_old",
            first_seen="2026-01-01",
            last_seen="2026-01-10",
            posted="2026-01-01",
            expires=None,
            status="withdrawn",
            withdrawn_date="2026-01-10",
        )
        # L_recent withdrawn 10 days ago
        state.listings["L_recent"] = ListingRecord(
            listing_id="L_recent",
            first_seen="2026-09-01",
            last_seen="2026-09-10",
            posted="2026-09-01",
            expires=None,
            status="withdrawn",
            withdrawn_date="2026-09-10",
        )

        update_state(state, [], run_date="2026-09-20", is_incremental=False, retention_days=180)
        self.assertNotIn("L_old", state.listings)
        self.assertIn("L_recent", state.listings)
        self.assertEqual(state.pruned_count, 1)

    def test_save_and_load_roundtrip(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            state = FreshnessState(slug="uradprace-cz", last_updated="2026-10-17", listings={})
            state.listings["X1"] = ListingRecord(
                listing_id="X1",
                first_seen="2026-10-01",
                last_seen="2026-10-17",
                posted="2026-10-01",
                expires="2026-11-01",
                status="active",
            )
            save_state(path, state)
            loaded = load_state(path, slug="uradprace-cz")
            self.assertEqual(loaded.slug, "uradprace-cz")
            self.assertEqual(loaded.last_updated, "2026-10-17")
            self.assertEqual(len(loaded.listings), 1)
            self.assertEqual(loaded.listings["X1"].listing_id, "X1")


if __name__ == "__main__":
    unittest.main()
