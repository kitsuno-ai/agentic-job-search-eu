from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .parser import ParsedListing


@dataclass
class ListingRecord:
    listing_id: str
    first_seen: str
    last_seen: str | None = None
    posted: str | None = None
    expires: str | None = None
    status: str = "active"
    withdrawn_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "listing_id": self.listing_id,
            "first_seen": self.first_seen,
            "posted": self.posted,
            "expires": self.expires,
            "status": self.status,
        }
        if self.status == "withdrawn":
            d["withdrawn_date"] = self.withdrawn_date
            if self.last_seen:
                d["last_seen"] = self.last_seen
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ListingRecord:
        status = str(data.get("status", "active"))
        first_seen = str(data["first_seen"])
        last_seen = data.get("last_seen") or first_seen
        return cls(
            listing_id=str(data["listing_id"]),
            first_seen=first_seen,
            last_seen=last_seen,
            posted=data.get("posted"),
            expires=data.get("expires"),
            status=status,
            withdrawn_date=data.get("withdrawn_date"),
        )


@dataclass
class FreshnessState:
    slug: str
    last_updated: str
    listings: dict[str, ListingRecord]
    pruned_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "last_updated": self.last_updated,
            "pruned_count": self.pruned_count,
            "total_active": sum(1 for r in self.listings.values() if r.status == "active"),
            "total_withdrawn": sum(1 for r in self.listings.values() if r.status == "withdrawn"),
            "listings": {k: v.to_dict() for k, v in sorted(self.listings.items())},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FreshnessState:
        raw_listings = data.get("listings", {})
        listings = {k: ListingRecord.from_dict(v) for k, v in raw_listings.items()}
        return cls(
            slug=str(data.get("slug", "unknown")),
            last_updated=str(data.get("last_updated", "")),
            listings=listings,
            pruned_count=int(data.get("pruned_count", 0)),
        )


def load_state(path: Path, slug: str) -> FreshnessState:
    if not path.exists():
        return FreshnessState(slug=slug, last_updated="", listings={}, pruned_count=0)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return FreshnessState.from_dict(data)


def save_state(path: Path, state: FreshnessState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_listings = sorted(state.listings.items(), key=lambda x: x[0])
    total_active = sum(1 for r in state.listings.values() if r.status == "active")
    total_withdrawn = sum(1 for r in state.listings.values() if r.status == "withdrawn")

    with open(path, "w", encoding="utf-8") as f:
        f.write("{\n")
        f.write(f'  "slug": {json.dumps(state.slug)},\n')
        f.write(f'  "last_updated": {json.dumps(state.last_updated)},\n')
        f.write(f'  "pruned_count": {state.pruned_count},\n')
        f.write(f'  "total_active": {total_active},\n')
        f.write(f'  "total_withdrawn": {total_withdrawn},\n')
        f.write('  "listings": {\n')
        for i, (lid, rec) in enumerate(sorted_listings):
            line_data = rec.to_dict()
            comma = "," if i < len(sorted_listings) - 1 else ""
            f.write(f'    {json.dumps(lid)}: {json.dumps(line_data, ensure_ascii=False, sort_keys=True)}{comma}\n')
        f.write("  }\n")
        f.write("}\n")


def _parse_iso_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def update_state(
    state: FreshnessState,
    parsed_listings: list[ParsedListing],
    run_date: str,
    is_incremental: bool = False,
    window_days: int = 365,
    retention_days: int | None = None,
) -> FreshnessState:
    """Update state with parsed listings for the given run_date with fixed window retention."""
    if retention_days is not None:
        effective_window = retention_days
    else:
        effective_window = window_days

    previous_run_date = state.last_updated
    state.last_updated = run_date
    current_listings = state.listings

    run_dt = _parse_iso_date(run_date) or date.today()
    cutoff_dt = date.fromordinal(run_dt.toordinal() - effective_window)

    if is_incremental:
        for item in parsed_listings:
            lid = item.listing_id
            posted_dt = _parse_iso_date(item.posted)
            if posted_dt and posted_dt < cutoff_dt:
                continue

            if item.operation == "delete":
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "withdrawn"
                    rec.withdrawn_date = run_date
                    rec.last_seen = run_date
            else:
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "active"
                    rec.last_seen = run_date
                    rec.withdrawn_date = None
                    if item.expires:
                        rec.expires = item.expires
                else:
                    current_listings[lid] = ListingRecord(
                        listing_id=lid,
                        first_seen=run_date,
                        posted=item.posted or run_date,
                        expires=item.expires,
                        status="active",
                        last_seen=run_date,
                        withdrawn_date=None,
                    )
    else:
        # Full snapshot: any missing active listing is withdrawn
        seen_ids = set()
        for item in parsed_listings:
            lid = item.listing_id
            posted_dt = _parse_iso_date(item.posted)
            if posted_dt and posted_dt < cutoff_dt:
                continue

            seen_ids.add(lid)
            if item.operation == "delete":
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "withdrawn"
                    rec.withdrawn_date = previous_run_date or rec.first_seen
                    rec.last_seen = rec.withdrawn_date
            else:
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "active"
                    rec.last_seen = run_date
                    rec.withdrawn_date = None
                    if item.expires:
                        rec.expires = item.expires
                else:
                    current_listings[lid] = ListingRecord(
                        listing_id=lid,
                        first_seen=run_date,
                        posted=item.posted or run_date,
                        expires=item.expires,
                        status="active",
                        last_seen=run_date,
                        withdrawn_date=None,
                    )

        # Mark previously active listings absent from snapshot as withdrawn.
        # Withdrawal date is set to previous_run_date (last day known present)
        for lid, rec in current_listings.items():
            if rec.status == "active" and lid not in seen_ids:
                rec.status = "withdrawn"
                rec.withdrawn_date = previous_run_date or rec.first_seen
                rec.last_seen = rec.withdrawn_date

    # Prune both active and withdrawn listings outside the fixed window
    to_delete = []
    for lid, rec in current_listings.items():
        ref_date_str = rec.posted or rec.first_seen
        ref_dt = _parse_iso_date(ref_date_str)
        if ref_dt and ref_dt < cutoff_dt:
            to_delete.append(lid)

    for lid in to_delete:
        del current_listings[lid]
        state.pruned_count += 1

    return state
