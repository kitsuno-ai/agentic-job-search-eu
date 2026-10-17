from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from tools.freshness.allowlist import (
    AllowlistSecurityError,
    get_allowlisted_source,
    load_allowlist,
    validate_allowlist,
    verify_source_policy,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestAllowlist(unittest.TestCase):
    def test_repo_allowlist_is_valid(self):
        """Verify the repository's checks/allowlist.yml has no policy violations."""
        errors = validate_allowlist()
        self.assertEqual(errors, [], f"Allowlist validation errors: {errors}")

    def test_uradprace_cz_is_permitted(self):
        entry = get_allowlisted_source("uradprace-cz")
        self.assertEqual(entry["slug"], "uradprace-cz")
        self.assertTrue(entry.get("enabled", True))
        self.assertEqual(entry.get("data_format"), "json")

    def test_reject_unlisted_source(self):
        with self.assertRaises(AllowlistSecurityError) as ctx:
            get_allowlisted_source("non-existent-source")
        self.assertIn("not present in checks/allowlist.yml", str(ctx.exception))

    def test_reject_restricted_posture(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            sources_dir = tmp_path / "sources"
            sources_dir.mkdir()

            # Create a mock source with restricted posture
            restricted_source = sources_dir / "restricted-board.yml"
            with open(restricted_source, "w", encoding="utf-8") as f:
                yaml.dump(
                    {
                        "slug": "restricted-board",
                        "name": "Restricted Board",
                        "license_posture": "restricted",
                    },
                    f,
                )

            with self.assertRaises(AllowlistSecurityError) as ctx:
                verify_source_policy("restricted-board", sources_dir=sources_dir)
            self.assertIn("forbidden license posture 'restricted'", str(ctx.exception))

    def test_reject_hostile_posture(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            sources_dir = tmp_path / "sources"
            sources_dir.mkdir()

            hostile_source = sources_dir / "hostile-board.yml"
            with open(hostile_source, "w", encoding="utf-8") as f:
                yaml.dump(
                    {
                        "slug": "hostile-board",
                        "name": "Hostile Board",
                        "license_posture": "hostile",
                    },
                    f,
                )

            with self.assertRaises(AllowlistSecurityError) as ctx:
                verify_source_policy("hostile-board", sources_dir=sources_dir)
            self.assertIn("forbidden license posture 'hostile'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
