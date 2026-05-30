"""Live Discogs REST API client (api.discogs.com).

Supplements the bulk-dump streaming path with real-time lookups and search
against the official Discogs database API.

Authentication
--------------
A **personal access token** is required for most endpoints.  Obtain one from
https://www.discogs.com/settings/developers and export it::

    export DISCOGS_TOKEN=your_token_here

Unauthenticated requests are accepted (rate-limited to 25 req/min); with a
token the limit rises to 60 req/min.  The token is read from the
``DISCOGS_TOKEN`` environment variable at module import time and can be
overridden by passing ``token=`` to any function.

Rate limiting
-------------
When the API returns HTTP 429 the client backs off for ``_RETRY_DELAY`` seconds
and retries once.  For sustained high-volume usage, set ``PYDISCOGS_ANON=1`` to
route through rotating proxies (requires ``anon_requests``).

User-Agent
----------
Discogs requires a meaningful User-Agent string.  This module sends::

    pydiscogs/<version> +https://github.com/TigreGotico/pydiscogs

Verified live
-------------
The following endpoints were verified by direct HTTP calls during development
(no token required for individual-entity GETs):

- ``GET /artists/{id}``
- ``GET /releases/{id}``
- ``GET /masters/{id}``
- ``GET /labels/{id}``
- ``GET /database/search``  (unauthenticated, returns paginated results)
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Iterator, List, Optional

from pydiscogs.models import Artist, ArtistCredit, Label, Master, Release, ReleaseFormat, Track
from pydiscogs._clean import clean_str, dedupe, parse_year, to_int

# ---------------------------------------------------------------------------
# Module-level config
# ---------------------------------------------------------------------------

API_BASE = "https://api.discogs.com"

_USER_AGENT = "pydiscogs/0.0.1 +https://github.com/TigreGotico/pydiscogs"

_RETRY_DELAY: float = 5.0   # seconds to wait after a 429
_REQUEST_DELAY: float = 1.1  # polite default: ~54 req/min (below the 60 authed limit)

_last_request: float = 0.0


def _throttle() -> None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _REQUEST_DELAY:
        time.sleep(_REQUEST_DELAY - elapsed)
    _last_request = time.time()


def _get_session():
    """Return a requests Session (CloudflareSession if available)."""
    try:
        from unblock_requests import CloudflareSession
        s = CloudflareSession()
        s.headers["User-Agent"] = _USER_AGENT
        return s
    except ImportError:
        import requests
        s = requests.Session()
        s.headers["User-Agent"] = _USER_AGENT
        return s


_session = None


def _session_get() -> Any:
    global _session
    if _session is None:
        _session = _get_session()
    return _session


def _api_get(path: str, params: Optional[Dict[str, Any]] = None,
             token: Optional[str] = None) -> Dict[str, Any]:
    """GET ``API_BASE + path``, inject auth, handle 429 with one retry."""
    tok = token or os.environ.get("DISCOGS_TOKEN")

    hdrs: Dict[str, str] = {}
    if tok:
        hdrs["Authorization"] = f"Discogs token={tok}"

    _throttle()
    sess = _session_get()
    url = API_BASE + path

    resp = sess.get(url, params=params or {}, headers=hdrs, timeout=30)

    if resp.status_code == 429:
        time.sleep(_RETRY_DELAY)
        _throttle()
        resp = sess.get(url, params=params or {}, headers=hdrs, timeout=30)

    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Response → model mappers
# ---------------------------------------------------------------------------

def _artist_from_api(data: Dict[str, Any]) -> Artist:
    """Map a ``GET /artists/{id}`` response dict to an :class:`Artist`."""
    aliases_raw = data.get("aliases") or []
    aliases = [a["name"] for a in aliases_raw if isinstance(a, dict)]

    members_raw = data.get("members") or []
    members = [m["name"] for m in members_raw if isinstance(m, dict)]

    groups_raw = data.get("groups") or []
    groups = [g["name"] for g in groups_raw if isinstance(g, dict)]

    name_variations = data.get("namevariations") or []

    return Artist(
        id=to_int(data.get("id")),
        name=clean_str(data.get("name")),
        real_name=clean_str(data.get("realname")),
        profile=clean_str(data.get("profile")),
        data_quality=clean_str(data.get("data_quality")),
        name_variations=list(name_variations),
        aliases=aliases,
        members=members,
        groups=groups,
        urls=list(data.get("urls") or []),
    )


def _label_from_api(data: Dict[str, Any]) -> Label:
    """Map a ``GET /labels/{id}`` response dict to a :class:`Label`."""
    parent = data.get("parent_label")
    parent_name = ""
    if isinstance(parent, dict):
        parent_name = clean_str(parent.get("name"))
    elif isinstance(parent, str):
        parent_name = clean_str(parent)

    sublabels_raw = data.get("sublabels") or []
    sublabels = [clean_str(s.get("name")) for s in sublabels_raw
                 if isinstance(s, dict) and s.get("name")]

    return Label(
        id=to_int(data.get("id")),
        name=clean_str(data.get("name")),
        contact_info=clean_str(data.get("contact_info")),
        profile=clean_str(data.get("profile")),
        data_quality=clean_str(data.get("data_quality")),
        parent_label=parent_name,
        sublabels=sublabels,
        urls=list(data.get("urls") or []),
    )


def _master_from_api(data: Dict[str, Any]) -> Master:
    """Map a ``GET /masters/{id}`` response dict to a :class:`Master`."""
    artists_raw = data.get("artists") or []
    artists = [
        ArtistCredit(
            id=to_int(a.get("id")),
            name=clean_str(a.get("name")),
            role=clean_str(a.get("role")),
            join=clean_str(a.get("join")),
            anv=clean_str(a.get("anv")),
        )
        for a in artists_raw if isinstance(a, dict)
    ]

    return Master(
        id=to_int(data.get("id")),
        main_release=to_int(data.get("main_release")),
        title=clean_str(data.get("title")),
        year=parse_year(str(data.get("year") or "")),
        data_quality=clean_str(data.get("data_quality")),
        artists=artists,
        genres=dedupe(data.get("genres") or []),
        styles=dedupe(data.get("styles") or []),
    )


def _release_from_api(data: Dict[str, Any]) -> Release:
    """Map a ``GET /releases/{id}`` response dict to a :class:`Release`."""
    artists_raw = data.get("artists") or []
    artists = [
        ArtistCredit(
            id=to_int(a.get("id")),
            name=clean_str(a.get("name")),
            role=clean_str(a.get("role")),
            join=clean_str(a.get("join")),
            anv=clean_str(a.get("anv")),
        )
        for a in artists_raw if isinstance(a, dict)
    ]

    extra_artists_raw = data.get("extraartists") or []
    extra_artists = [
        ArtistCredit(
            id=to_int(a.get("id")),
            name=clean_str(a.get("name")),
            role=clean_str(a.get("role")),
            join=clean_str(a.get("join")),
            anv=clean_str(a.get("anv")),
        )
        for a in extra_artists_raw if isinstance(a, dict)
    ]

    labels_raw = data.get("labels") or []
    labels = dedupe([clean_str(lb.get("name")) for lb in labels_raw
                     if isinstance(lb, dict) and lb.get("name")])
    catnos = dedupe([clean_str(lb.get("catno")) for lb in labels_raw
                     if isinstance(lb, dict) and lb.get("catno")])

    formats_raw = data.get("formats") or []
    formats = [
        ReleaseFormat(
            name=clean_str(f.get("name")),
            qty=to_int(f.get("qty")),
            text=clean_str(f.get("text")),
            descriptions=list(f.get("descriptions") or []),
        )
        for f in formats_raw if isinstance(f, dict)
    ]

    tracklist_raw = data.get("tracklist") or []
    tracklist = [
        Track(
            position=clean_str(t.get("position")),
            title=clean_str(t.get("title")),
            duration=clean_str(t.get("duration")),
        )
        for t in tracklist_raw if isinstance(t, dict)
    ]

    released = clean_str(data.get("released") or "")

    return Release(
        id=to_int(data.get("id")),
        master_id=to_int(data.get("master_id")),
        title=clean_str(data.get("title")),
        status=clean_str(data.get("status")),
        country=clean_str(data.get("country")),
        released=released,
        year=parse_year(released) or parse_year(str(data.get("year") or "")),
        data_quality=clean_str(data.get("data_quality")),
        artists=artists,
        extra_artists=extra_artists,
        labels=labels,
        catalog_numbers=catnos,
        genres=dedupe(data.get("genres") or []),
        styles=dedupe(data.get("styles") or []),
        formats=formats,
        tracklist=tracklist,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_artist(artist_id: int, *, token: Optional[str] = None) -> Artist:
    """Fetch a single artist by Discogs ID.

    Args:
        artist_id: Discogs artist ID (e.g. ``1`` for The Persuader).
        token: Discogs personal access token.  Falls back to ``DISCOGS_TOKEN``
            env var.

    Returns:
        An :class:`~pydiscogs.models.Artist` populated from the live API.

    Example::

        artist = get_artist(1)
        print(artist.name)  # "The Persuader"
    """
    data = _api_get(f"/artists/{artist_id}", token=token)
    return _artist_from_api(data)


def get_release(release_id: int, *, token: Optional[str] = None) -> Release:
    """Fetch a single release by Discogs ID.

    Args:
        release_id: Discogs release ID (e.g. ``1`` for Stockholm by The Persuader).
        token: Discogs personal access token.

    Returns:
        A :class:`~pydiscogs.models.Release` populated from the live API.
    """
    data = _api_get(f"/releases/{release_id}", token=token)
    return _release_from_api(data)


def get_master(master_id: int, *, token: Optional[str] = None) -> Master:
    """Fetch a single master release by Discogs ID.

    Args:
        master_id: Discogs master ID (e.g. ``18500``).
        token: Discogs personal access token.

    Returns:
        A :class:`~pydiscogs.models.Master` populated from the live API.
    """
    data = _api_get(f"/masters/{master_id}", token=token)
    return _master_from_api(data)


def get_label(label_id: int, *, token: Optional[str] = None) -> Label:
    """Fetch a single label by Discogs ID.

    Args:
        label_id: Discogs label ID (e.g. ``5`` for Svek).
        token: Discogs personal access token.

    Returns:
        A :class:`~pydiscogs.models.Label` populated from the live API.
    """
    data = _api_get(f"/labels/{label_id}", token=token)
    return _label_from_api(data)


def search(
    query: str = "",
    *,
    type: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    label: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[str] = None,
    format: Optional[str] = None,
    per_page: int = 50,
    page: int = 1,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Search the Discogs database.

    Maps to ``GET /database/search``.  Returns the raw paginated response dict
    with ``"results"`` (list of search result dicts) and ``"pagination"``.

    Args:
        query: Free-text search query (``q`` parameter).
        type: Entity type filter: ``"release"``, ``"master"``, ``"artist"``,
            or ``"label"``.
        title: Search in title field only.
        artist: Filter by artist name.
        label: Filter by label name.
        genre: Filter by genre (e.g. ``"Electronic"``).
        style: Filter by style (e.g. ``"Techno"``).
        country: Filter by country.
        year: Filter by year string (e.g. ``"1999"``).
        format: Filter by format name (e.g. ``"Vinyl"``).
        per_page: Results per page (1–100, default 50).
        page: Page number (default 1).
        token: Discogs personal access token.  Search **requires** a token;
            unauthenticated requests are accepted by the API but return fewer
            results and are more aggressively rate-limited.

    Returns:
        Dict with keys ``"results"`` (list of result dicts) and
        ``"pagination"`` (paging metadata).

    Example::

        results = search("Stockholm", type="release", genre="Electronic")
        for r in results["results"]:
            print(r["id"], r["title"])
    """
    params: Dict[str, Any] = {"per_page": per_page, "page": page}
    if query:
        params["q"] = query
    if type:
        params["type"] = type
    if title:
        params["title"] = title
    if artist:
        params["artist"] = artist
    if label:
        params["label"] = label
    if genre:
        params["genre"] = genre
    if style:
        params["style"] = style
    if country:
        params["country"] = country
    if year:
        params["year"] = year
    if format:
        params["format"] = format

    return _api_get("/database/search", params=params, token=token)


def search_iter(
    query: str = "",
    *,
    type: Optional[str] = None,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    label: Optional[str] = None,
    genre: Optional[str] = None,
    style: Optional[str] = None,
    country: Optional[str] = None,
    year: Optional[str] = None,
    format: Optional[str] = None,
    per_page: int = 50,
    limit: Optional[int] = None,
    token: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Paginated search, yielding individual result dicts across all pages.

    Stops when all pages are consumed or ``limit`` results have been yielded.

    Args:
        See :func:`search` for parameter descriptions.
        limit: Stop after this many results (``None`` = all pages).

    Yields:
        Raw search result dicts from the API.
    """
    page = 1
    yielded = 0
    while True:
        resp = search(
            query=query,
            type=type,
            title=title,
            artist=artist,
            label=label,
            genre=genre,
            style=style,
            country=country,
            year=year,
            format=format,
            per_page=per_page,
            page=page,
            token=token,
        )
        results = resp.get("results") or []
        if not results:
            break
        for r in results:
            yield r
            yielded += 1
            if limit is not None and yielded >= limit:
                return
        pagination = resp.get("pagination") or {}
        if page >= pagination.get("pages", 1):
            break
        page += 1
