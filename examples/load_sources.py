#!/usr/bin/env python3
"""
Example: load all sources and show a coverage summary.

Run from the repo root:
    python examples/load_sources.py
"""

from pathlib import Path
from collections import Counter, defaultdict

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"


def load_all_sources() -> list[dict]:
    sources = []
    for f in sorted(SOURCES_DIR.glob("*.yml")):
        if f.name.startswith("_"):
            continue
        with open(f) as fh:
            sources.append(yaml.safe_load(fh))
    return sources


def main() -> None:
    sources = load_all_sources()
    active = [s for s in sources if s["kitsuno_status"] == "active"]
    wishlist = [s for s in sources if s["kitsuno_status"] == "wishlist"]
    inactive = [s for s in sources if s["kitsuno_status"] == "inactive"]

    print(f"=== Total: {len(sources)} sources ===")
    print(f"  active:   {len(active)}")
    print(f"  wishlist: {len(wishlist)}")
    print(f"  inactive: {len(inactive)}")

    print("\n=== Active sources by focus ===")
    focus_counts = Counter(s["focus"] for s in active)
    for focus, n in focus_counts.most_common():
        print(f"  {focus:12} {n}")

    print("\n=== Active sources by access type ===")
    access_counts = Counter(s["access_type"] for s in active)
    for t, n in access_counts.most_common():
        print(f"  {t:10} {n}")

    print("\n=== Country coverage (active only) ===")
    country_to_sources: dict[str, list[str]] = defaultdict(list)
    for s in active:
        for c in s["countries"]:
            country_to_sources[c].append(s["slug"])
    for country in sorted(country_to_sources):
        slugs = country_to_sources[country]
        print(f"  {country}: {len(slugs)} sources — {', '.join(slugs[:4])}"
              + ("..." if len(slugs) > 4 else ""))

    print("\n=== Sources with API docs ===")
    with_docs = [s for s in active if s.get("api_docs_url")]
    for s in with_docs:
        print(f"  {s['name']:25} {s['api_docs_url']}")


if __name__ == "__main__":
    main()
