#!/usr/bin/env python3
"""
Validate source YAML files against the schema defined in sources/_schema.yml.

Usage:
    python tools/validate.py                     # validate all sources/*.yml
    python tools/validate.py sources/jobs-ch.yml # validate a single file

Exit code 0 if all files pass, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"
SCHEMA_PATH = SOURCES_DIR / "_schema.yml"

ENUMS: dict[str, set[str]] = {
    "focus": {"general", "tech", "remote", "sector", "aggregator"},
    "access_type": {"api", "rss", "scrape", "hybrid"},
    "auth_type": {"api_key", "oauth", "token", "cookie", "none"},
    "kitsuno_status": {"active", "inactive", "wishlist"},
    "license_posture": {
        "aggregator-friendly", "neutral", "restricted", "hostile", "unknown"
    },
    "update_frequency": {
        "realtime", "hourly", "daily", "weekly", "monthly", "unknown"
    },
}

REQUIRED_FIELDS = {
    "name", "slug", "url", "countries", "languages", "focus",
    "access_type", "requires_auth", "kitsuno_status", "license_posture",
    "last_verified",
}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$|^\*$")
LANGUAGE_RE = re.compile(r"^[a-z]{2}$")
URL_RE = re.compile(r"^https?://")


class ValidationError(Exception):
    pass


def validate_file(path: Path) -> list[str]:
    """Return list of error messages for a single source file. Empty = valid."""
    errors: list[str] = []

    try:
        with open(path) as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        return [f"YAML parse error: {e}"]

    if not isinstance(data, dict):
        return ["Top-level must be a mapping (dict)."]

    # Required fields present
    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")

    # slug format + filename consistency
    slug = data.get("slug")
    if slug is not None:
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            errors.append(
                f"slug must be kebab-case (lowercase alphanumeric + - or _): {slug!r}"
            )
        expected_filename = f"{slug}.yml"
        if path.name != expected_filename:
            errors.append(
                f"Filename '{path.name}' does not match slug. Expected '{expected_filename}'."
            )

    # URL fields
    for field in ("url", "api_docs_url", "terms_url"):
        val = data.get(field)
        if val is not None and not URL_RE.match(str(val)):
            errors.append(f"{field} must be http(s) URL: {val!r}")

    # Countries
    countries = data.get("countries")
    if countries is not None:
        if not isinstance(countries, list) or not countries:
            errors.append("countries must be a non-empty array.")
        else:
            for c in countries:
                if not isinstance(c, str) or not COUNTRY_RE.match(c):
                    errors.append(
                        f"country code must be ISO 3166-1 alpha-2 uppercase or '*': {c!r}"
                    )

    # Languages
    languages = data.get("languages")
    if languages is not None:
        if not isinstance(languages, list) or not languages:
            errors.append("languages must be a non-empty array.")
        else:
            for lang in languages:
                if not isinstance(lang, str) or not LANGUAGE_RE.match(lang):
                    errors.append(
                        f"language code must be ISO 639-1 lowercase: {lang!r}"
                    )

    # Enum fields
    for field, allowed in ENUMS.items():
        val = data.get(field)
        if val is None:
            continue
        if val not in allowed:
            errors.append(
                f"{field} must be one of {sorted(allowed)}, got {val!r}"
            )

    # Booleans
    ra = data.get("requires_auth")
    if ra is not None and not isinstance(ra, bool):
        errors.append(f"requires_auth must be a boolean, got {ra!r}")

    # Conditional: auth_type present when requires_auth=true
    if data.get("requires_auth") is True and not data.get("auth_type"):
        errors.append(
            "auth_type is recommended when requires_auth=true (use 'none' to mark explicit)."
        )

    # Date
    lv = data.get("last_verified")
    if lv is not None and not isinstance(lv, date):
        errors.append(
            f"last_verified must be a date in YYYY-MM-DD format, got {lv!r}"
        )

    # estimated_volume
    ev = data.get("estimated_volume")
    if ev is not None and not isinstance(ev, int):
        errors.append(f"estimated_volume must be an integer, got {ev!r}")

    return errors


def main(argv: list[str]) -> int:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found at {SCHEMA_PATH}")
        return 2

    if len(argv) > 1:
        targets = [Path(p) for p in argv[1:]]
    else:
        targets = [
            p for p in sorted(SOURCES_DIR.glob("*.yml"))
            if not p.name.startswith("_")
        ]

    if not targets:
        print("No source files found.")
        return 0

    fail = 0
    for path in targets:
        errs = validate_file(path)
        if errs:
            fail += 1
            print(f"✗ {path.name}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ {path.name}")

    print(f"\n{len(targets) - fail}/{len(targets)} sources valid.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
