from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .metrics import FreshnessMetrics

SUMMARY_TEMPLATE = r"""# Listing Freshness & Persistence Report: {source_name} (`{slug}`)

* **Source Slug:** `{slug}`
* **Upstream Endpoint:** [{endpoint}]({endpoint})
* **Monitoring Cadence:** Daily bulk open data
* **Last Checked:** {run_date} ({timestamp_utc} UTC)
* **Status:** {overall_status}

## 1. Summary Metrics

| Metric | Measured Value | Methodology |
| :--- | :--- | :--- |
| **Total Tracked Listings** | {total_listings:,} | Cumulative state tracking within 365-day observation window |
| **Currently Active** | {active_listings:,} | Present in latest snapshot / active stream |
| **Withdrawn / Closed** | {withdrawn_listings:,} | Observed departures from register |
| **Median Listing Lifetime** | {median_lifetime} | Kaplan-Meier 50% survival threshold with left-truncation |
| **30-Day Survival Probability** | {survival_30d} | Kaplan-Meier $S(30)$ accounting for delayed entry & right-censoring |
| **60-Day Survival Probability** | {survival_60d} | Kaplan-Meier $S(60)$ accounting for delayed entry & right-censoring |
| **90-Day Survival Probability** | {survival_90d} | Kaplan-Meier $S(90)$ accounting for delayed entry & right-censoring |
| **Active Age > 90 Days** | {share_older_90d} ({count_older_90d:,} listings) | Share of active vacancies posted > 90 days ago (`datumVlozeni`) |
| **Active Age > 180 Days** | {share_older_180d} ({count_older_180d:,} listings) | Share of active vacancies posted > 180 days ago (`datumVlozeni`) |
| **Active Age > 365 Days** | {share_older_365d} ({count_older_365d:,} listings) | Share of active vacancies posted > 365 days ago (`datumVlozeni`) |
| **Expiry Date Coverage** | {expiry_coverage_ratio} ({active_with_expiry:,} listings) | Proportion of active vacancies with explicit expiration date |
| **Active Past Stated Expiry** | {stale_active_count:,} listings ({staleness_ratio}) | Overdue vacancies still active in upstream register |
| **Schema Contract Integrity** | {drift_badge} | Structural validation of upstream response schema |

{drift_section}

## 2. Statistical Methodology

* **Left-Truncation & Right-Censoring (Kaplan-Meier):** Listings already online at baseline enter observation at `first_seen` (delayed entry: entry time $a_i = \text{{first\_seen}} - \text{{posted}}$). Counting them from `posted` without left truncation biases early survival upwards. This report implements the left-truncated Kaplan-Meier estimator ($S(t) = \prod_{{t_i \le t}} (1 - d_i/n_i)$) where risk set $n_i$ requires $a_k \le t_i \le \text{{exit}}_k$.
* **Discrete Day Resolution:** Upstream timestamps operate on discrete calendar days (`YYYY-MM-DD`). Lifetimes are bounded to non-negative integer days.
* **Fixed Observation Window (365 Days):** To prevent survivor bias from asymmetric retention, both active and withdrawn listings outside the 365-day window from run date are pruned equally.
* **Git Diff Minimization:** Active listings do not store mutable `last_seen` timestamps (implicit in run date). State records are stored in sorted single-line JSON format, restricting daily git commits strictly to newly added and withdrawn records.
* **Raw Logs:** Ephemeral run logs are stored as 90-day GitHub Actions artifacts rather than polluting git history.
"""


def format_survival(val: float | None) -> str:
    if val is None:
        return "N/A (insufficient sample)"
    return f"{val * 100:.1f}%"


def generate_markdown_summary(
    slug: str,
    source_name: str,
    endpoint: str,
    metrics: FreshnessMetrics,
    run_date: str,
) -> str:
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    overall_status = "🟢 Healthy" if not metrics.schema_drift_detected else "⚠️ Schema Drift Detected"
    drift_badge = "✅ PASS" if not metrics.schema_drift_detected else "⚠️ DRIFT DETECTED"

    if metrics.median_lifetime_days is not None:
        median_str = f"{metrics.median_lifetime_days:.1f} days"
    else:
        median_str = "N/A (> 50% remain active)"

    if metrics.schema_drift_detected:
        drift_section = "## ⚠️ Upstream Schema Drift Warnings\n\n" + "\n".join(
            f"- {w}" for w in metrics.drift_warnings
        )
    else:
        drift_section = "## Upstream Schema Integrity\n\nNo structural schema drift detected. Upstream payload conforms to expected contract."

    return SUMMARY_TEMPLATE.format(
        source_name=source_name,
        slug=slug,
        endpoint=endpoint,
        run_date=run_date,
        timestamp_utc=now_utc,
        overall_status=overall_status,
        total_listings=metrics.total_listings,
        active_listings=metrics.active_listings,
        withdrawn_listings=metrics.withdrawn_listings,
        median_lifetime=median_str,
        survival_30d=format_survival(metrics.survival_30d),
        survival_60d=format_survival(metrics.survival_60d),
        survival_90d=format_survival(metrics.survival_90d),
        share_older_90d=f"{metrics.share_older_90d:.2f}%",
        count_older_90d=metrics.count_older_90d,
        share_older_180d=f"{metrics.share_older_180d:.2f}%",
        count_older_180d=metrics.count_older_180d,
        share_older_365d=f"{metrics.share_older_365d:.2f}%",
        count_older_365d=metrics.count_older_365d,
        expiry_coverage_ratio=f"{metrics.expiry_coverage_ratio:.2f}%",
        active_with_expiry=metrics.active_with_expiry,
        stale_active_count=metrics.stale_active_count,
        staleness_ratio=f"{metrics.staleness_ratio:.2f}%",
        drift_badge=drift_badge,
        drift_section=drift_section,
    )


def save_markdown_summary(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_run_log(
    slug: str,
    run_date: str,
    metrics: FreshnessMetrics,
    raw_count: int,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "run_date": run_date,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "raw_records_received": raw_count,
        "total_tracked": metrics.total_listings,
        "active_count": metrics.active_listings,
        "withdrawn_count": metrics.withdrawn_listings,
        "median_lifetime_days": metrics.median_lifetime_days,
        "survival_30d": metrics.survival_30d,
        "survival_60d": metrics.survival_60d,
        "survival_90d": metrics.survival_90d,
        "share_older_90d": metrics.share_older_90d,
        "count_older_90d": metrics.count_older_90d,
        "share_older_180d": metrics.share_older_180d,
        "count_older_180d": metrics.count_older_180d,
        "share_older_365d": metrics.share_older_365d,
        "count_older_365d": metrics.count_older_365d,
        "expiry_coverage_ratio": metrics.expiry_coverage_ratio,
        "active_with_expiry": metrics.active_with_expiry,
        "stale_active_count": metrics.stale_active_count,
        "staleness_ratio": metrics.staleness_ratio,
        "schema_drift_detected": metrics.schema_drift_detected,
        "drift_warnings": metrics.drift_warnings,
    }


def save_run_log(path: Path, log_data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
