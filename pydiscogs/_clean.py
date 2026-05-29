"""Internal cleaning / coercion helpers for Discogs XML values."""
from __future__ import annotations

import re
import unicodedata
from typing import List, Optional


def clean_str(text: Optional[str]) -> str:
    """Normalise unicode, collapse whitespace, strip."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_or_none(text: Optional[str]) -> Optional[str]:
    """Like :func:`clean_str` but returns ``None`` for empty / placeholder values."""
    val = clean_str(text)
    if not val or val.lower() in ("none", "n/a", "-", "unknown"):
        return None
    return val


def to_int(value, default: Optional[int] = None) -> Optional[int]:
    """Coerce a value to int, tolerating strings, blanks and None."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def parse_year(value: Optional[str]) -> Optional[int]:
    """Extract a 4-digit year from a Discogs date string (``YYYY`` / ``YYYY-MM-DD``).

    Discogs uses ``0`` or empty to mean "unknown"; those map to ``None``.
    """
    if not value:
        return None
    m = re.search(r"(\d{4})", str(value))
    if not m:
        return None
    year = int(m.group(1))
    return year if year else None


def dedupe(items: List[str]) -> List[str]:
    """Order-preserving de-duplication of a string list (case-insensitive)."""
    seen: set = set()
    out: List[str] = []
    for it in items:
        val = clean_str(it)
        if not val:
            continue
        low = val.lower()
        if low in seen:
            continue
        seen.add(low)
        out.append(val)
    return out
