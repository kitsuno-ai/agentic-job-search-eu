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
    last_seen: str
    posted: str | None
    expires: str | None
    status: str  # "active" or "withdrawn"
    withdrawn_date: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ListingRecord:
        return cls(
            listing_id=str(data["listing_id"]),
            first_seen=str(data["first_seen"]),
            last_seen=str(data["last_seen"]),
            posted=data.get("posted"),
            expires=data.get("expires"),
            status=str(data.get("status", "active")),
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)


def update_state(
    state: FreshnessState,
    parsed_listings: list[ParsedListing],
    run_date: str,
    is_incremental: bool = False,
    retention_days: int = 180,
) -> FreshnessState:
    """Update state with parsed listings for the given run_date."""
    state.last_updated = run_date
    current_listings = state.listings

    if is_incremental:
        for item in parsed_listings:
            lid = item.listing_id
            if item.operation == "delete":
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "withdrawn"
                    rec.withdrawn_date = run_date
                    rec.last_seen = run_date
            else:
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.last_seen = run_date
                    rec.status = "active"
                    rec.withdrawn_date = None
                    if item.expires:
                        rec.expires = item.expires
                else:
                    current_listings[lid] = ListingRecord(
                        listing_id=lid,
                        first_seen=run_date,
                        last_seen=run_date,
                        posted=item.posted or run_date,
                        expires=item.expires,
                        status="active",
                        withdrawn_date=None,
                    )
    else:
        # Full snapshot: any missing active listing is withdrawn
        seen_ids = set()
        for item in parsed_listings:
            lid = item.listing_id
            seen_ids.add(lid)
            if item.operation == "delete":
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.status = "withdrawn"
                    rec.withdrawn_date = run_date
                    rec.last_seen = run_date
            else:
                if lid in current_listings:
                    rec = current_listings[lid]
                    rec.last_seen = run_date
                    rec.status = "active"
                    rec.withdrawn_date = None
                    if item.expires:
                        rec.expires = item.expires
                else:
                    current_listings[lid] = ListingRecord(
                        listing_id=lid,
                        first_seen=run_date,
                        last_seen=run_date,
                        posted=item.posted or run_date,
                        expires=item.expires,
                        status="active",
                        withdrawn_date=None,
                    )

        # Mark previously active listings absent from snapshot as withdrawn
        for lid, rec in current_listings.items():
            if rec.status == "active" and lid not in seen_ids:
                rec.status = "withdrawn"
                rec.withdrawn_date = run_date

    # Prune historical withdrawn records older than retention_days
    run_dt = datetime.strptime(run_date, "%Y-%m-%d").date()
    to_delete = []
    for lid, rec in current_listings.items():
        if rec.status == "withdrawn" and rec.withdrawn_date:
            try:
                w_dt = datetime.strptime(rec.withdrawn_date, "%Y-%m-%d").date()
                if (run_dt - w_dt).days > retention_days:
                    to_delete.append(lid)
            except ValueError:
                pass

    for lid in to_delete:
        del current_listings[lid]
        state.pruned_count += 1

    return state
