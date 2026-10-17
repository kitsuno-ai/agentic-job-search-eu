from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.freshness.cli import run_freshness_pipeline


class TestCliAndPathGuard(unittest.TestCase):
    def test_cli_end_to_end_with_fixture(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            state_dir = tmp_path / "reports" / "freshness"
            checks_dir = tmp_path / "reports" / "checks"
            fixture_file = tmp_path / "mpsv_sample.json"

            sample_data = {
                "polozky": [
                    {
                        "id": "FIXTURE-1",
                        "datumVlozeni": "2026-09-01",
                        "expirace": "2026-12-01",
                    },
                    {
                        "id": "FIXTURE-2",
                        "datumVlozeni": "2026-09-15",
                        "expirace": "2026-09-30",
                    },
                ]
            }
            with open(fixture_file, "w", encoding="utf-8") as f:
                json.dump(sample_data, f)

            exit_code = run_freshness_pipeline(
                slug="uradprace-cz",
                input_file=fixture_file,
                run_date_str="2026-10-17",
                state_dir=state_dir,
                checks_dir=checks_dir,
            )

            self.assertEqual(exit_code, 0)

            # Verify files were generated
            state_file = state_dir / "uradprace-cz-state.json"
            summary_file = state_dir / "uradprace-cz-summary.md"
            log_file = checks_dir / "2026-10-17-uradprace-cz.json"

            self.assertTrue(state_file.exists())
            self.assertTrue(summary_file.exists())
            self.assertTrue(log_file.exists())

            # Verify state contents
            with open(state_file, "r", encoding="utf-8") as f:
                state_json = json.load(f)
            self.assertEqual(state_json["slug"], "uradprace-cz")
            self.assertEqual(len(state_json["listings"]), 2)
            self.assertIn("FIXTURE-1", state_json["listings"])
            self.assertIn("FIXTURE-2", state_json["listings"])

            # FIXTURE-2 expired on 2026-09-30, run_date is 2026-10-17 -> should be stale
            with open(summary_file, "r", encoding="utf-8") as f:
                summary_content = f.read()
            self.assertIn("uradprace-cz", summary_content)
            self.assertIn("50.00%", summary_content)  # 1 out of 2 is stale

    def test_path_confinement_security_logic(self):
        """Simulate GHA path boundary verification logic."""
        def check_violations(paths: list[str]) -> list[str]:
            return [p for p in paths if not p.startswith("reports/freshness/")]

        # Safe changes
        safe_changes = [
            "reports/freshness/uradprace-cz-state.json",
            "reports/freshness/uradprace-cz-summary.md",
        ]
        self.assertEqual(check_violations(safe_changes), [])

        # Unsafe changes attempting to mutate sources or workflows
        unsafe_changes = [
            "reports/freshness/uradprace-cz-state.json",
            "sources/uradprace-cz.yml",
        ]
        violations = check_violations(unsafe_changes)
        self.assertEqual(violations, ["sources/uradprace-cz.yml"])


if __name__ == "__main__":
    unittest.main()
