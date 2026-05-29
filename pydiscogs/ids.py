"""Canonical Discogs join-ids for the metadatarr ``ExternalIds.extra`` anchor.

Discogs ids are the de-facto join keys across the music-metadata ecosystem
(MusicBrainz relations, RYM, Bandcamp scrapes, ...). Each entity contributes one
``<site>_id`` anchor under the ``discogs_`` namespace:

- ``discogs_artist_id``  — :class:`~pydiscogs.models.Artist`
- ``discogs_label_id``   — :class:`~pydiscogs.models.Label`
- ``discogs_master_id``  — :class:`~pydiscogs.models.Master`
- ``discogs_release_id`` — :class:`~pydiscogs.models.Release`

``*_to_extra`` builds the flat string dict consumed by ``ExternalIds.extra``;
``id_from_url`` recovers the id from any discogs.com URL.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from pydiscogs.models import Artist, Label, Master, Release

# /artist/123, /label/45-Name, /release/678-Title, /master/90, plus the
# numeric-suffix UI forms (/release/678).
_URL_RE = re.compile(
    r"discogs\.com/(?:[a-z]{2}/)?(?P<type>artist|label|master|release)/(?P<id>\d+)",
    re.IGNORECASE,
)


def id_from_url(url: str) -> Optional[Tuple[str, int]]:
    """Extract ``(entity, id)`` from any discogs.com URL, or ``None``.

    ``entity`` is one of ``artist`` / ``label`` / ``master`` / ``release``.
    """
    m = _URL_RE.search(url or "")
    if not m:
        return None
    return m.group("type").lower(), int(m.group("id"))


def artist_to_extra(artist: Artist) -> Dict[str, str]:
    """Flat ``extra`` dict for an :class:`~pydiscogs.models.Artist`."""
    extra: Dict[str, str] = {}
    if artist.id is not None:
        extra["discogs_artist_id"] = str(artist.id)
        extra["discogs_artist_url"] = f"https://www.discogs.com/artist/{artist.id}"
    if artist.name:
        extra["discogs_artist_name"] = artist.name
    if artist.real_name:
        extra["discogs_artist_realname"] = artist.real_name
    return extra


def label_to_extra(label: Label) -> Dict[str, str]:
    """Flat ``extra`` dict for a :class:`~pydiscogs.models.Label`."""
    extra: Dict[str, str] = {}
    if label.id is not None:
        extra["discogs_label_id"] = str(label.id)
        extra["discogs_label_url"] = f"https://www.discogs.com/label/{label.id}"
    if label.name:
        extra["discogs_label_name"] = label.name
    return extra


def master_to_extra(master: Master) -> Dict[str, str]:
    """Flat ``extra`` dict for a :class:`~pydiscogs.models.Master`."""
    extra: Dict[str, str] = {}
    if master.id is not None:
        extra["discogs_master_id"] = str(master.id)
        extra["discogs_master_url"] = f"https://www.discogs.com/master/{master.id}"
    if master.main_release is not None:
        extra["discogs_release_id"] = str(master.main_release)
    if master.title:
        extra["discogs_title"] = master.title
    if master.year is not None:
        extra["discogs_year"] = str(master.year)
    if master.artists:
        extra["discogs_artist"] = master.artists[0].name
        if master.artists[0].id is not None:
            extra["discogs_artist_id"] = str(master.artists[0].id)
    return extra


def release_to_extra(release: Release) -> Dict[str, str]:
    """Flat ``extra`` dict for a :class:`~pydiscogs.models.Release`."""
    extra: Dict[str, str] = {}
    if release.id is not None:
        extra["discogs_release_id"] = str(release.id)
        extra["discogs_release_url"] = f"https://www.discogs.com/release/{release.id}"
    if release.master_id is not None:
        extra["discogs_master_id"] = str(release.master_id)
    if release.title:
        extra["discogs_title"] = release.title
    if release.year is not None:
        extra["discogs_year"] = str(release.year)
    if release.labels:
        extra["discogs_label"] = release.labels[0]
    if release.artists:
        extra["discogs_artist"] = release.artists[0].name
        if release.artists[0].id is not None:
            extra["discogs_artist_id"] = str(release.artists[0].id)
    return extra


def to_extra(obj) -> Dict[str, str]:
    """Dispatch to the right ``*_to_extra`` for any supported entity."""
    if isinstance(obj, Artist):
        return artist_to_extra(obj)
    if isinstance(obj, Label):
        return label_to_extra(obj)
    if isinstance(obj, Master):
        return master_to_extra(obj)
    if isinstance(obj, Release):
        return release_to_extra(obj)
    raise TypeError(f"unsupported entity type: {type(obj).__name__}")
