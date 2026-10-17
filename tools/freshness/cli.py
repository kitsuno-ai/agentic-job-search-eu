from __future__ import annotations

import argparse
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .allowlist import AllowlistSecurityError, get_allowlisted_source
from .metrics import calculate_metrics
from .parser import parse_payload
from .reporter import (
    generate_markdown_summary,
    generate_run_log,
    save_markdown_summary,
    save_run_log,
)
from .state_tracker import load_state, save_state, update_state

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def download_to_temp(url: str, dest_path: Path, timeout: int = 300) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "agentic-job-search-eu/freshness-bot (research; open-data-tracker)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        with open(dest_path, "wb") as f:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)


def run_freshness_pipeline(
    slug: str,
    input_file: Path | None = None,
    run_date_str: str | None = None,
    state_dir: Path | None = None,
    checks_dir: Path | None = None,
    allowlist_path: Path | None = None,
    is_incremental: bool = False,
    window_days: int = 365,
    strict_drift: bool = False,
) -> int:
    run_date = run_date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s_dir = state_dir or (REPO_ROOT / "reports" / "freshness")
    c_dir = checks_dir or (REPO_ROOT / "reports" / "checks")

    print(f"=== Starting Freshness Check: {slug} [{run_date}] ===")

    # 1. Allowlist verification
    try:
        source_config = get_allowlisted_source(slug, allowlist_path)
    except AllowlistSecurityError as e:
        print(f"SECURITY ERROR: {e}", file=sys.stderr)
        return 2

    source_name = source_config.get("name", slug)
    endpoint = source_config.get("endpoint", "")
    format_hint = source_config.get("data_format", "json")

    # 2. Acquire payload
    temp_download_path: Path | None = None
    if input_file:
        print(f"Loading local data fixture from: {input_file}")
        if not input_file.exists():
            print(f"ERROR: Input file not found: {input_file}", file=sys.stderr)
            return 1
        payload_source: Path = input_file
    else:
        print(f"Fetching open data bulk from: {endpoint}")
        import tempfile
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="freshness_", suffix=f".{format_hint}")
        import os
        os.close(tmp_fd)
        temp_download_path = Path(tmp_name)
        try:
            download_to_temp(endpoint, temp_download_path)
            payload_source = temp_download_path
        except Exception as e:
            if temp_download_path.exists():
                temp_download_path.unlink()
            print(f"ERROR: Failed to fetch data from {endpoint}: {e}", file=sys.stderr)
            return 1

    try:
        # 3. Parse payload
        parse_result = parse_payload(payload_source, format_hint=format_hint)
    finally:
        if temp_download_path and temp_download_path.exists():
            temp_download_path.unlink()

    print(f"Parsed {len(parse_result.listings):,} listings from {parse_result.raw_count:,} raw records.")
    if parse_result.drift_warnings:
        print("Schema Drift Warnings:")
        for w in parse_result.drift_warnings:
            print(f"  ⚠️  {w}")

    # 4. State Management
    state_path = s_dir / f"{slug}-state.json"
    state = load_state(state_path, slug=slug)
    updated_state = update_state(
        state=state,
        parsed_listings=parse_result.listings,
        run_date=run_date,
        is_incremental=is_incremental,
        window_days=window_days,
    )
    save_state(state_path, updated_state)
    print(f"Updated state saved to {state_path}")

    # 5. Calculate Metrics
    metrics = calculate_metrics(
        state=updated_state,
        run_date_str=run_date,
        drift_warnings=parse_result.drift_warnings,
    )

    # 6. Generate Summary & Logs
    summary_path = s_dir / f"{slug}-summary.md"
    summary_md = generate_markdown_summary(
        slug=slug,
        source_name=source_name,
        endpoint=endpoint,
        metrics=metrics,
        run_date=run_date,
    )
    save_markdown_summary(summary_path, summary_md)
    print(f"Summary report generated at {summary_path}")

    log_path = c_dir / f"{run_date}-{slug}.json"
    run_log = generate_run_log(
        slug=slug,
        run_date=run_date,
        metrics=metrics,
        raw_count=parse_result.raw_count,
    )
    save_run_log(log_path, run_log)
    print(f"Raw run log saved at {log_path}")

    print("\n=== Freshness Summary ===")
    print(f"Total Tracked:   {metrics.total_listings}")
    print(f"Currently Active:{metrics.active_listings}")
    print(f"Withdrawn:       {metrics.withdrawn_listings}")
    print(f"Median Lifetime: {metrics.median_lifetime_days} days")
    print(f"Survival 30d:    {metrics.survival_30d}")
    print(f"Survival 60d:    {metrics.survival_60d}")
    print(f"Survival 90d:    {metrics.survival_90d}")
    print(f"Age > 90d:       {metrics.share_older_90d}% ({metrics.count_older_90d} listings)")
    print(f"Age > 180d:      {metrics.share_older_180d}% ({metrics.count_older_180d} listings)")
    print(f"Age > 365d:      {metrics.share_older_365d}% ({metrics.count_older_365d} listings)")
    print(f"Expiry Coverage: {metrics.expiry_coverage_ratio}% ({metrics.active_with_expiry} listings)")
    print(f"Expired Active:  {metrics.stale_active_count} listings")
    print(f"Schema Drift:    {'YES' if metrics.schema_drift_detected else 'NO'}")

    if strict_drift and metrics.schema_drift_detected:
        print("Failing due to --strict-drift flag.")
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Listing Freshness & Persistence Tracker")
    parser.add_argument("--slug", default="uradprace-cz", help="Source slug to process")
    parser.add_argument("--input-file", type=Path, default=None, help="Path to input JSON/XML file")
    parser.add_argument("--run-date", type=str, default=None, help="Execution date (YYYY-MM-DD)")
    parser.add_argument("--state-dir", type=Path, default=None, help="Directory for state files")
    parser.add_argument("--checks-dir", type=Path, default=None, help="Directory for raw check logs")
    parser.add_argument("--allowlist-file", type=Path, default=None, help="Path to allowlist.yml")
    parser.add_argument("--incremental", action="store_true", help="Process as incremental diff")
    parser.add_argument("--window-days", type=int, default=365, help="Observation window in days")
    parser.add_argument("--strict-drift", action="store_true", help="Fail if schema drift is detected")

    args = parser.parse_args(argv)
    return run_freshness_pipeline(
        slug=args.slug,
        input_file=args.input_file,
        run_date_str=args.run_date,
        state_dir=args.state_dir,
        checks_dir=args.checks_dir,
        allowlist_path=args.allowlist_file,
        is_incremental=args.incremental,
        window_days=args.window_days,
        strict_drift=args.strict_drift,
    )


if __name__ == "__main__":
    sys.exit(main())
