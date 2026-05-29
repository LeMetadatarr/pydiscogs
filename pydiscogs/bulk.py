"""Memory-safe access to the Discogs monthly dumps.

The dumps are gzip-compressed XML, multi-GB each (releases is ~10 GB). Nothing
here ever loads a whole file into memory:

- :func:`list_dumps` parses the small HTML directory index at
  ``data.discogs.com``.
- :func:`stream` opens a streaming HTTP response, inflates it incrementally
  with ``zlib`` (gzip window), feeds the bytes to ``xml.etree.iterparse`` and
  ``elem.clear()`` s each record after yielding it. A ``limit`` stops the read
  early, so a smoke test reads only the first few KB off the socket without
  downloading the rest.
- :func:`download` is an opt-in, resumable on-disk cache for callers who really
  want the whole file; everything else streams.
"""
from __future__ import annotations

import gzip
import os
import re
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass
from html import unescape
from typing import Dict, Iterator, List, Optional

from pydiscogs import transport
from pydiscogs.entity import ENTITY_NAMES, get_spec

# gzip member: zlib raw deflate with a 16-bit gzip header offset.
_GZIP_WBITS = zlib.MAX_WBITS | 16

# Rows of the data.discogs.com index look like:
#   2026-01-15 16:42:07  418.0 MB  <a href="?download=data%2F2025%2Fdiscogs_20250101_artists.xml.gz">...</a>
_ROW_RE = re.compile(
    r"\?download=(?P<key>[^\"']+\.xml\.gz)",
)
_FILE_RE = re.compile(
    r"discogs_(?P<date>\d{8})_(?P<entity>artists|labels|masters|releases)\.xml\.gz$"
)


def _cache_dir() -> str:
    """On-disk cache directory (``PYDISCOGS_CACHE`` or ``~/.cache/pydiscogs``)."""
    root = os.environ.get("PYDISCOGS_CACHE")
    if not root:
        root = os.path.join(
            os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
            "pydiscogs",
        )
    os.makedirs(root, exist_ok=True)
    return root


@dataclass
class Dump:
    """One dump object listed in the Discogs index."""

    key: str          # full object key: data/2025/discogs_20250101_labels.xml.gz
    entity: str       # labels | artists | masters | releases
    date: str         # YYYYMMDD release date

    @property
    def filename(self) -> str:
        return self.key.rsplit("/", 1)[-1]

    @property
    def download_url(self) -> str:
        return f"{transport.BASE_URL}?download={self.key}"


def list_dumps(
    year: Optional[int] = None, entity: Optional[str] = None
) -> List[Dump]:
    """List available dump objects from the Discogs directory index.

    Args:
        year: Restrict to a single year (e.g. ``2025``). Defaults to the latest
            year present in the top-level index.
        entity: Restrict to one of ``artists`` / ``labels`` / ``masters`` /
            ``releases``.

    Returns:
        A list of :class:`Dump`, sorted by date then entity.
    """
    if year is None:
        year = _latest_year()
    resp = transport.get(params={"prefix": f"data/{year}/"})
    html = resp.text

    dumps: List[Dump] = []
    seen: set = set()
    for m in _ROW_RE.finditer(html):
        key = unescape(m.group("key")).replace("%2F", "/").replace("%2f", "/")
        if key in seen:
            continue
        seen.add(key)
        fm = _FILE_RE.search(key)
        if not fm:
            continue
        ent = fm.group("entity")
        if entity and ent != entity.strip().lower():
            continue
        dumps.append(Dump(key=key, entity=ent, date=fm.group("date")))
    dumps.sort(key=lambda d: (d.date, ENTITY_NAMES.index(d.entity)))
    return dumps


def _latest_year() -> int:
    resp = transport.get()
    years = [int(y) for y in re.findall(r"\?prefix=data%2F(\d{4})%2F", resp.text)]
    if not years:
        raise RuntimeError("could not parse year list from Discogs index")
    return max(years)


def latest_dump(entity: str, year: Optional[int] = None) -> Dump:
    """Return the most recent dump for ``entity`` (optionally within ``year``)."""
    spec = get_spec(entity)
    dumps = list_dumps(year=year, entity=spec.name)
    if not dumps:
        raise RuntimeError(f"no {spec.name} dump found")
    return dumps[-1]


def resolve(name_or_key: str) -> Dump:
    """Resolve an entity name (``"labels"``) or a full object key to a :class:`Dump`.

    Bare entity names resolve to that entity's latest dump.
    """
    if "/" in name_or_key or name_or_key.endswith(".xml.gz"):
        fm = _FILE_RE.search(name_or_key)
        if not fm:
            raise ValueError(f"not a recognised dump key: {name_or_key!r}")
        return Dump(key=name_or_key, entity=fm.group("entity"), date=fm.group("date"))
    return latest_dump(name_or_key)


def download(name: str, force: bool = False, chunk_size: int = 1 << 20) -> str:
    """Download a whole dump to the cache dir and return the local path.

    Resumes / skips if the file already exists (unless ``force``). This pulls
    the entire multi-GB object — prefer :func:`stream` unless you genuinely need
    the file on disk.

    Args:
        name: Entity name or full object key (see :func:`resolve`).
        force: Re-download even if a cached copy exists.
        chunk_size: Streaming write chunk size in bytes.
    """
    dump = resolve(name)
    dest = os.path.join(_cache_dir(), dump.filename)
    if os.path.exists(dest) and not force:
        return dest
    tmp = dest + ".part"
    resp = transport.open_stream(dump.key)
    try:
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size):
                if chunk:
                    fh.write(chunk)
    finally:
        resp.close()
    os.replace(tmp, dest)
    return dest


def _parse_xml_chunks(
    xml_chunks: Iterator[bytes], record_tag: str, model, limit: Optional[int]
) -> Iterator[object]:
    """Yield parsed model records from a stream of *decompressed* XML bytes.

    Only *top-level* records (direct children of the dump root, at depth 1) are
    yielded — the same ``record_tag`` recurs nested inside records (e.g. a
    ``<label>`` sublabel inside a ``<label>``, an ``<artist>`` credit inside an
    ``<artist>``), and those must not be mistaken for records. Depth is tracked
    via start/end events.

    Each record's subtree is cleared right after it is yielded so memory stays
    flat no matter how large the dump is.
    """
    parser = ET.XMLPullParser(events=("start", "end"))
    count = 0
    depth = 0
    root = None
    for data in xml_chunks:
        if not data:
            continue
        parser.feed(data)
        for event, elem in parser.read_events():
            if event == "start":
                if root is None:
                    root = elem  # the dump's <labels>/<releases>/... root
                depth += 1
                continue
            # event == "end"
            depth -= 1
            # A record element sits at depth 1 (root is depth 0 after its end,
            # so a top-level record's end event fires when depth drops to 1).
            if elem.tag != record_tag or depth != 1:
                continue
            yield model.from_element(elem)
            count += 1
            elem.clear()
            # Detach already-processed records from the root so the parser's
            # retained tree does not grow across millions of records.
            if root is not None:
                root.clear()
            if limit is not None and count >= limit:
                return


def _inflate(compressed_chunks: Iterator[bytes]) -> Iterator[bytes]:
    """Incrementally gunzip a stream of compressed chunks into XML bytes."""
    decomp = zlib.decompressobj(_GZIP_WBITS)
    for compressed in compressed_chunks:
        if not compressed:
            continue
        data = decomp.decompress(compressed)
        if data:
            yield data


def stream(name: str, limit: Optional[int] = None, local: Optional[str] = None):
    """Stream-parse a dump and yield typed records one at a time.

    Memory stays flat regardless of file size: bytes are inflated and parsed
    incrementally and each record's XML subtree is cleared right after it is
    yielded.

    Args:
        name: Entity name (``"labels"``) or full object key.
        limit: Stop after this many records (the network read also stops, so a
            smoke test never pulls the whole file).
        local: Parse this local ``.xml.gz`` path instead of fetching over HTTP
            (used for offline fixtures and the cache).

    Yields:
        :class:`~pydiscogs.models.Artist` / ``Label`` / ``Master`` / ``Release``.
    """
    if local:
        # Offline/cached path: the entity is taken from ``name`` (no network),
        # and gzip.open already yields decompressed XML bytes.
        yield from stream_local(local, name, limit=limit)
        return

    dump = resolve(name)
    spec = get_spec(dump.entity)
    resp = transport.open_stream(dump.key)
    try:
        yield from _parse_xml_chunks(
            _inflate(resp.iter_content(1 << 16)), spec.record_tag, spec.model, limit
        )
    finally:
        resp.close()


def stream_local(path: str, entity: str, limit: Optional[int] = None):
    """Stream-parse a local ``.xml.gz`` file for a known ``entity``.

    Convenience wrapper around :func:`stream` for fixtures whose filename does
    not encode the entity.
    """
    spec = get_spec(entity)
    with gzip.open(path, "rb") as fh:
        yield from _parse_xml_chunks(
            iter(lambda: fh.read(1 << 16), b""),
            spec.record_tag,
            spec.model,
            limit,
        )


def checksums(year: Optional[int] = None) -> Dict[str, str]:
    """Return ``{filename: object_key}`` for the CHECKSUM files of a year.

    The contents are not fetched — only the index keys are returned, so callers
    can verify a cached download out of band if they wish.
    """
    if year is None:
        year = _latest_year()
    resp = transport.get(params={"prefix": f"data/{year}/"})
    out: Dict[str, str] = {}
    for m in re.finditer(r"\?download=([^\"']+_CHECKSUM\.txt)", resp.text):
        key = unescape(m.group(1)).replace("%2F", "/").replace("%2f", "/")
        out[key.rsplit("/", 1)[-1]] = key
    return out
