from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ALLOWLIST_PATH = REPO_ROOT / "checks" / "allowlist.yml"
SOURCES_DIR = REPO_ROOT / "sources"

PERMITTED_POSTURES = {"aggregator-friendly", "neutral"}
FORBIDDEN_POSTURES = {"restricted", "hostile", "unknown"}


class AllowlistSecurityError(Exception):
    """Raised when an allowlist entry violates licensing or governance policies."""
    pass


def load_allowlist(path: Path | None = None) -> list[dict[str, Any]]:
    target_path = path or ALLOWLIST_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Allowlist file not found at {target_path}")

    if yaml is None:
        raise RuntimeError("PyYAML is required to parse the allowlist.")

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "allowed_sources" not in data:
        raise ValueError("Allowlist must contain top-level 'allowed_sources' list.")

    sources = data.get("allowed_sources", [])
    if not isinstance(sources, list):
        raise ValueError("'allowed_sources' must be a list.")

    return sources


def verify_source_policy(slug: str, sources_dir: Path | None = None) -> dict[str, Any]:
    """Verify that a source YAML exists and has an acceptable license posture."""
    s_dir = sources_dir or SOURCES_DIR
    source_file = s_dir / f"{slug}.yml"
    if not source_file.exists():
        raise AllowlistSecurityError(
            f"Allowlisted slug '{slug}' does not correspond to an existing source at {source_file}."
        )

    if yaml is None:
        raise RuntimeError("PyYAML is required to parse source definitions.")

    with open(source_file, "r", encoding="utf-8") as f:
        source_data = yaml.safe_load(f)

    posture = source_data.get("license_posture")
    if posture in FORBIDDEN_POSTURES:
        raise AllowlistSecurityError(
            f"Source '{slug}' has forbidden license posture '{posture}'. "
            f"Automated checks are prohibited for restricted, hostile, or unknown sources."
        )

    if posture not in PERMITTED_POSTURES:
        raise AllowlistSecurityError(
            f"Source '{slug}' has unapproved license posture '{posture}'. "
            f"Must be one of {sorted(PERMITTED_POSTURES)}."
        )

    return source_data


def get_allowlisted_source(slug: str, allowlist_path: Path | None = None) -> dict[str, Any]:
    """Get the configuration for a specific allowlisted source after verification."""
    sources = load_allowlist(allowlist_path)
    entry = next((s for s in sources if s.get("slug") == slug), None)
    if not entry:
        raise AllowlistSecurityError(f"Slug '{slug}' is not present in checks/allowlist.yml.")

    if not entry.get("enabled", True):
        raise AllowlistSecurityError(f"Source '{slug}' is disabled in checks/allowlist.yml.")

    # Verify against the source definition
    verify_source_policy(slug)
    return entry


def validate_allowlist(allowlist_path: Path | None = None) -> list[str]:
    """Validate all entries in the allowlist. Returns list of error messages (empty if valid)."""
    errors: list[str] = []
    try:
        sources = load_allowlist(allowlist_path)
    except Exception as e:
        return [f"Failed to load allowlist: {e}"]

    for entry in sources:
        slug = entry.get("slug")
        if not slug:
            errors.append(f"Allowlist entry missing 'slug': {entry}")
            continue

        try:
            verify_source_policy(slug)
        except AllowlistSecurityError as e:
            errors.append(str(e))

    return errors
