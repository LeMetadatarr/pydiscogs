"""HTTP transport for the Discogs monthly data dumps.

Discogs publishes its monthly Release / Artist / Label / Master dumps behind a
Cloudflare-fronted directory index at ``https://data.discogs.com/``.  The index
is browsed with ``?prefix=data/<YYYY>/`` and individual objects are downloaded
with ``?download=data/<YYYY>/<file>``.  No API key is required; the data is
released under CC0.

Because the index sits behind Cloudflare, this module routes traffic through
``unblock_requests.CloudflareSession`` (the org HTTP transport) so the anti-bot
challenge is handled transparently, with a plain ``requests`` fallback for
offline / test environments.

The dump objects are multi-GB gzip files.  This transport never buffers a whole
object: :func:`open_stream` returns a streaming ``Response`` whose body is read
in chunks by the bulk parser, so a caller can stop after the first N records
without pulling the entire file.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

# Cloudflare-fronted directory index + download front for the dumps bucket.
BASE_URL = "https://data.discogs.com/"

# The underlying public S3 bucket (object GETs only; anonymous listing is
# disabled, which is why the index above is used instead).
BUCKET_URL = "https://discogs-data-dumps.s3.us-west-2.amazonaws.com/"

# The gated Discogs REST API (token required) — see ids.py / docs for the
# optional supplement path. Not used by the dump pipeline.
API_URL = "https://api.discogs.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
    ),
    "Accept": "*/*",
}

_session: Optional[Any] = None
_last_request: float = 0.0
_min_delay: float = 0.5
_force_requests: bool = False


def set_delay(seconds: float) -> None:
    """Set the minimum delay between HTTP requests (default: 0.5 s)."""
    global _min_delay
    _min_delay = max(0.0, seconds)


def use_requests(enabled: bool = True) -> None:
    """Force the plain ``requests`` backend instead of ``CloudflareSession``.

    Useful for offline tests, where no Cloudflare bypass is needed and the
    network is mocked. Resets any existing session.
    """
    global _force_requests
    _force_requests = enabled
    reset_session()


def _make_session() -> Any:
    if not _force_requests:
        try:
            from unblock_requests import CloudflareSession

            session = CloudflareSession()
            session.headers.update(_HEADERS)
            return session
        except ImportError:
            pass
    import requests

    session = requests.Session()
    session.headers.update(_HEADERS)
    return session


def get_session() -> Any:
    global _session
    if _session is None:
        _session = _make_session()
    return _session


def reset_session() -> None:
    """Force a new HTTP session on the next request."""
    global _session
    _session = None


def _throttle() -> None:
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < _min_delay:
        time.sleep(_min_delay - elapsed)
    _last_request = time.time()


def get(path: str = "", params: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    """GET ``BASE_URL`` (optionally a sub-path) and return the ``Response``.

    Args:
        path: Path appended to :data:`BASE_URL` (usually empty — the index is
            driven entirely by query params).
        params: Query parameters, e.g. ``{"prefix": "data/2025/"}``.
        **kwargs: Passed through to ``Session.get`` (``stream``, ``headers`` ...).
    """
    _throttle()
    session = get_session()
    url = BASE_URL + path.lstrip("/")
    resp = session.get(url, params=params, **kwargs)
    resp.raise_for_status()
    return resp


def open_stream(download_key: str, timeout: int = 120) -> Any:
    """Open a streaming GET on a dump object and return the raw ``Response``.

    The caller is responsible for closing the response. The body is *not*
    consumed here — use ``Response.iter_content`` to read it incrementally.

    Args:
        download_key: The object key, e.g.
            ``"data/2025/discogs_20250101_labels.xml.gz"``.
        timeout: Connect/read timeout in seconds.
    """
    _throttle()
    session = get_session()
    resp = session.get(
        BASE_URL, params={"download": download_key}, stream=True, timeout=timeout
    )
    resp.raise_for_status()
    return resp
