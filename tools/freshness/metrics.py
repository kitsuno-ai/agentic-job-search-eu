from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .state_tracker import FreshnessState, ListingRecord


@dataclass
class FreshnessMetrics:
    total_listings: int
    active_listings: int
    withdrawn_listings: int
    median_lifetime_days: float | None
    survival_30d: float | None
    survival_60d: float | None
    survival_90d: float | None
    stale_active_count: int
    schema_drift_detected: bool
    drift_warnings: list[str]
    share_older_90d: float = 0.0
    share_older_180d: float = 0.0
    share_older_365d: float = 0.0
    count_older_90d: int = 0
    count_older_180d: int = 0
    count_older_365d: int = 0
    expiry_coverage_ratio: float = 0.0
    active_with_expiry: int = 0


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def compute_kaplan_meier(
    records: list[ListingRecord], run_date_str: str
) -> tuple[dict[int, float], float | None]:
    """
    Compute Kaplan-Meier survival curve with left truncation (delayed entry).
    Listings enter observation at first_seen (entry_time = first_seen - posted).
    This avoids survivor bias where long-lived listings already online at the baseline
    run are counted in early risk sets before they could have been observed.

    Returns:
        (survival_curve: {time_days: survival_prob}, median_lifetime_days: float | None)
    """
    run_date = _parse_date(run_date_str)
    if not run_date:
        raise ValueError(f"Invalid run_date: {run_date_str}")

    # (entry_age_days, exit_age_days, is_event)
    observations: list[tuple[int, int, int]] = []

    for r in records:
        posted_d = _parse_date(r.posted) or _parse_date(r.first_seen)
        if not posted_d:
            continue
        first_seen_d = _parse_date(r.first_seen) or posted_d

        entry_age = max(0, (first_seen_d - posted_d).days)

        if r.status == "withdrawn":
            end_d = _parse_date(r.withdrawn_date) or _parse_date(r.last_seen) or first_seen_d
            exit_age = max(entry_age, (end_d - posted_d).days)
            observations.append((entry_age, exit_age, 1))
        else:
            end_d = run_date
            exit_age = max(entry_age, (end_d - posted_d).days)
            observations.append((entry_age, exit_age, 0))

    if not observations:
        return {}, None

    # Find all unique discrete event times
    event_times = sorted({exit_age for _, exit_age, is_event in observations if is_event == 1})
    if not event_times:
        return {}, None

    events_at = defaultdict(int)
    for _, exit_age, is_event in observations:
        if is_event == 1:
            events_at[exit_age] += 1

    survival_prob = 1.0
    survival_curve: dict[int, float] = {}
    median_days: float | None = None

    for t in event_times:
        d_t = events_at[t]
        # Risk set n_t with left truncation:
        # Subject must have entered by time t (entry_age <= t) and not yet exited before t (exit_age >= t)
        n_t = sum(1 for entry_age, exit_age, _ in observations if entry_age <= t <= exit_age)

        if d_t > 0 and n_t > 0:
            survival_prob *= (1.0 - (d_t / n_t))

        survival_curve[t] = round(survival_prob, 4)

        if median_days is None and survival_prob <= 0.50:
            median_days = float(t)

    return survival_curve, median_days


def evaluate_survival_at(survival_curve: dict[int, float], target_day: int) -> float | None:
    if not survival_curve:
        return None
    times = sorted(survival_curve.keys())
    if target_day < times[0]:
        return 1.0

    prob = 1.0
    for t in times:
        if t <= target_day:
            prob = survival_curve[t]
        else:
            break
    return prob


def calculate_metrics(
    state: FreshnessState,
    run_date_str: str,
    drift_warnings: list[str] | None = None,
) -> FreshnessMetrics:
    records = list(state.listings.values())
    total_listings = len(records)
    active_records = [r for r in records if r.status == "active"]
    withdrawn_records = [r for r in records if r.status == "withdrawn"]

    run_date = _parse_date(run_date_str) or date.today()

    # Active listings age distribution (based on posted date / datumVlozeni)
    count_older_90d = 0
    count_older_180d = 0
    count_older_365d = 0
    stale_active_count = 0
    active_with_expiry = 0

    for r in active_records:
        posted_d = _parse_date(r.posted) or _parse_date(r.first_seen)
        if posted_d:
            age_days = (run_date - posted_d).days
            if age_days > 90:
                count_older_90d += 1
            if age_days > 180:
                count_older_180d += 1
            if age_days > 365:
                count_older_365d += 1

        if r.expires:
            exp = _parse_date(r.expires)
            if exp:
                active_with_expiry += 1
                if run_date > exp:
                    stale_active_count += 1

    total_active = len(active_records)
    share_90d = round((count_older_90d / total_active) * 100, 2) if total_active else 0.0
    share_180d = round((count_older_180d / total_active) * 100, 2) if total_active else 0.0
    share_365d = round((count_older_365d / total_active) * 100, 2) if total_active else 0.0
    expiry_cov = round((active_with_expiry / total_active) * 100, 2) if total_active else 0.0
    # Kaplan-Meier survival with delayed entry
    survival_curve, median_days = compute_kaplan_meier(records, run_date_str)

    s30 = evaluate_survival_at(survival_curve, 30)
    s60 = evaluate_survival_at(survival_curve, 60)
    s90 = evaluate_survival_at(survival_curve, 90)

    warnings = list(drift_warnings or [])

    return FreshnessMetrics(
        total_listings=total_listings,
        active_listings=total_active,
        withdrawn_listings=len(withdrawn_records),
        median_lifetime_days=median_days,
        survival_30d=s30,
        survival_60d=s60,
        survival_90d=s90,
        share_older_90d=share_90d,
        share_older_180d=share_180d,
        share_older_365d=share_365d,
        count_older_90d=count_older_90d,
        count_older_180d=count_older_180d,
        count_older_365d=count_older_365d,
        expiry_coverage_ratio=expiry_cov,
        active_with_expiry=active_with_expiry,
        stale_active_count=stale_active_count,
        schema_drift_detected=bool(warnings),
        drift_warnings=warnings,
    )
