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
    staleness_ratio: float  # Percentage of active listings that are expired (0.0 to 100.0)
    schema_drift_detected: bool
    drift_warnings: list[str]


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
    Compute Kaplan-Meier survival curve and median lifetime.
    Returns:
        (survival_curve: {time_days: survival_prob}, median_lifetime_days: float | None)
    """
    run_date = _parse_date(run_date_str)
    if not run_date:
        raise ValueError(f"Invalid run_date: {run_date_str}")

    # (duration_days, is_event)
    observations: list[tuple[int, int]] = []

    for r in records:
        start_d = _parse_date(r.posted) or _parse_date(r.first_seen)
        if not start_d:
            continue

        if r.status == "withdrawn":
            end_d = _parse_date(r.withdrawn_date) or _parse_date(r.last_seen) or run_date
            duration = max(0, (end_d - start_d).days)
            observations.append((duration, 1))
        else:
            end_d = run_date
            duration = max(0, (end_d - start_d).days)
            observations.append((duration, 0))

    if not observations:
        return {}, None

    # Group counts
    # events[t] = count of events at time t
    # total_at[t] = count of all observations with duration == t
    events_at = defaultdict(int)
    all_at = defaultdict(int)

    for duration, is_event in observations:
        all_at[duration] += 1
        if is_event == 1:
            events_at[duration] += 1

    unique_times = sorted(all_at.keys())
    total_n = len(observations)

    # Compute risk set n_t and events d_t
    # n_t is the number of observations with duration >= t
    cum_exited = 0
    at_risk: dict[int, int] = {}
    for t in unique_times:
        at_risk[t] = total_n - cum_exited
        cum_exited += all_at[t]

    # Calculate Kaplan-Meier survival step function
    survival_prob = 1.0
    survival_curve: dict[int, float] = {}
    median_days: float | None = None

    for t in unique_times:
        n_t = at_risk[t]
        d_t = events_at[t]

        if d_t > 0 and n_t > 0:
            survival_prob *= (1.0 - (d_t / n_t))

        survival_curve[t] = round(survival_prob, 4)

        if median_days is None and survival_prob <= 0.50:
            median_days = float(t)

    return survival_curve, median_days


def evaluate_survival_at(survival_curve: dict[int, float], target_day: int) -> float | None:
    if not survival_curve:
        return None
    # Survival is 1.0 before the first event time
    times = sorted(survival_curve.keys())
    if target_day < times[0]:
        return 1.0

    # Step function value: value at the largest event time <= target_day
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

    # Staleness check
    stale_active_count = 0
    active_with_expiry = 0
    for r in active_records:
        if r.expires:
            exp = _parse_date(r.expires)
            if exp:
                active_with_expiry += 1
                if run_date > exp:
                    stale_active_count += 1

    staleness_ratio = (
        round((stale_active_count / len(active_records)) * 100, 2)
        if active_records
        else 0.0
    )

    # Kaplan-Meier survival
    survival_curve, median_days = compute_kaplan_meier(records, run_date_str)

    s30 = evaluate_survival_at(survival_curve, 30)
    s60 = evaluate_survival_at(survival_curve, 60)
    s90 = evaluate_survival_at(survival_curve, 90)

    warnings = list(drift_warnings or [])

    return FreshnessMetrics(
        total_listings=total_listings,
        active_listings=len(active_records),
        withdrawn_listings=len(withdrawn_records),
        median_lifetime_days=median_days,
        survival_30d=s30,
        survival_60d=s60,
        survival_90d=s90,
        stale_active_count=stale_active_count,
        staleness_ratio=staleness_ratio,
        schema_drift_detected=bool(warnings),
        drift_warnings=warnings,
    )
