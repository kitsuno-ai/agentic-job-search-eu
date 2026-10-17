from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _extract_date(val: Any) -> str | None:
    if not val:
        return None
    s = str(val).strip()
    m = DATE_RE.match(s)
    if m:
        return m.group(1)
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


@dataclass(frozen=True)
class ParsedListing:
    listing_id: str
    posted: str | None
    updated: str | None
    expires: str | None
    operation: str = "active"  # "active", "add", "update", "delete"


@dataclass
class ParseResult:
    listings: list[ParsedListing]
    drift_warnings: list[str]
    raw_count: int


def parse_mpsv_json(content: str | bytes | dict[str, Any] | Path) -> ParseResult:
    drift_warnings: list[str] = []

    if isinstance(content, Path):
        try:
            with open(content, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return ParseResult(
                listings=[],
                drift_warnings=[f"JSON read error: {e}"],
                raw_count=0,
            )
    elif isinstance(content, (str, bytes)):
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return ParseResult(
                listings=[],
                drift_warnings=[f"JSON syntax error: {e}"],
                raw_count=0,
            )
    else:
        data = content


    if not isinstance(data, dict):
        return ParseResult(
            listings=[],
            drift_warnings=["Top-level payload is not a JSON object."],
            raw_count=0,
        )

    # Schema drift checks
    if "polozky" not in data:
        drift_warnings.append("Expected top-level array 'polozky' was missing from payload.")
        # Fallback check for alternative root keys
        items_raw = data.get("items") or data.get("vacancies") or data.get("data")
        if not isinstance(items_raw, list):
            return ParseResult(listings=[], drift_warnings=drift_warnings, raw_count=0)
    else:
        items_raw = data["polozky"]

    if not isinstance(items_raw, list):
        drift_warnings.append("'polozky' is not a list.")
        return ParseResult(listings=[], drift_warnings=drift_warnings, raw_count=0)

    listings: list[ParsedListing] = []
    missing_id_count = 0
    missing_date_count = 0

    for idx, item in enumerate(items_raw):
        if not isinstance(item, dict):
            drift_warnings.append(f"Item at index {idx} is not a dictionary.")
            continue

        raw_id = item.get("id") or item.get("portalId") or item.get("referencniCislo")
        if not raw_id:
            missing_id_count += 1
            continue

        listing_id = str(raw_id).strip()
        posted = _extract_date(item.get("datumVlozeni"))
        updated = _extract_date(item.get("datumZmeny"))
        expires = _extract_date(item.get("expirace") or item.get("platnostDo"))

        if not posted:
            missing_date_count += 1

        op_raw = str(item.get("operace") or item.get("stav") or "active").lower()
        if op_raw in {"smaz", "zruseno", "withdrawn", "delete", "deleted"}:
            operation = "delete"
        elif op_raw in {"vloz", "add", "new"}:
            operation = "add"
        elif op_raw in {"zmena", "update", "updated"}:
            operation = "update"
        else:
            operation = "active"

        listings.append(
            ParsedListing(
                listing_id=listing_id,
                posted=posted,
                updated=updated,
                expires=expires,
                operation=operation,
            )
        )

    if items_raw and missing_id_count / len(items_raw) > 0.05:
        drift_warnings.append(
            f"Over 5% of records ({missing_id_count}/{len(items_raw)}) lacked an identifiable ID."
        )

    if items_raw and missing_date_count / len(items_raw) > 0.20:
        drift_warnings.append(
            f"Over 20% of records ({missing_date_count}/{len(items_raw)}) lacked 'datumVlozeni'."
        )

    return ParseResult(
        listings=listings,
        drift_warnings=drift_warnings,
        raw_count=len(items_raw),
    )


def parse_mpsv_xml(content: str | bytes) -> ParseResult:
    drift_warnings: list[str] = []
    try:
        if isinstance(content, str):
            root = ET.fromstring(content.encode("utf-8"))
        else:
            root = ET.fromstring(content)
    except ET.ParseError as e:
        return ParseResult(
            listings=[],
            drift_warnings=[f"XML parse error: {e}"],
            raw_count=0,
        )

    # Look for items
    items = root.findall(".//polozka")
    if not items:
        items = root.findall(".//volne_misto") or root.findall(".//item")
        if items:
            drift_warnings.append("Root did not contain '<polozka>' elements; parsed alternative items.")
        else:
            drift_warnings.append("No vacancy items found in XML payload.")
            return ParseResult(listings=[], drift_warnings=drift_warnings, raw_count=0)

    listings: list[ParsedListing] = []
    missing_id_count = 0
    missing_date_count = 0

    for idx, el in enumerate(items):
        def _get_text(*tags: str) -> str | None:
            for tag in tags:
                child = el.find(tag)
                if child is not None and child.text:
                    return child.text.strip()
            return None

        raw_id = _get_text("id", "portalId", "referencniCislo", "referencni_cislo")
        if not raw_id:
            missing_id_count += 1
            continue

        listing_id = raw_id
        posted = _extract_date(_get_text("datumVlozeni", "datum_vlozeni", "datumZverejneni"))
        updated = _extract_date(_get_text("datumZmeny", "datum_zmeny"))
        expires = _extract_date(_get_text("expirace", "platnostDo", "platnost_do"))

        if not posted:
            missing_date_count += 1

        op_raw = str(_get_text("operace", "stav") or "active").lower()
        if op_raw in {"smaz", "zruseno", "withdrawn", "delete", "deleted"}:
            operation = "delete"
        elif op_raw in {"vloz", "add", "new"}:
            operation = "add"
        elif op_raw in {"zmena", "update", "updated"}:
            operation = "update"
        else:
            operation = "active"

        listings.append(
            ParsedListing(
                listing_id=listing_id,
                posted=posted,
                updated=updated,
                expires=expires,
                operation=operation,
            )
        )

    if items and missing_id_count / len(items) > 0.05:
        drift_warnings.append(
            f"Over 5% of records ({missing_id_count}/{len(items)}) lacked an identifiable ID."
        )

    if items and missing_date_count / len(items) > 0.20:
        drift_warnings.append(
            f"Over 20% of records ({missing_date_count}/{len(items)}) lacked posted date."
        )

    return ParseResult(
        listings=listings,
        drift_warnings=drift_warnings,
        raw_count=len(items),
    )


def parse_payload(content: str | bytes | dict[str, Any] | Path, format_hint: str = "json") -> ParseResult:
    """Parse payload based on format_hint or auto-detection."""
    hint = format_hint.lower().strip()
    if isinstance(content, Path):
        if hint in {"xml", "application/xml", "text/xml"} or content.suffix.lower() == ".xml":
            with open(content, "r", encoding="utf-8") as f:
                return parse_mpsv_xml(f.read())
        return parse_mpsv_json(content)

    if hint == "json":
        return parse_mpsv_json(content)
    elif hint in {"xml", "application/xml", "text/xml"}:
        return parse_mpsv_xml(content)
    else:
        # Auto-detect
        stripped = (content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else str(content)).lstrip()
        if stripped.startswith("<"):
            return parse_mpsv_xml(content)
        return parse_mpsv_json(content)

