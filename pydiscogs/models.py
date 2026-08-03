"""Typed dataclasses for the four Discogs dump entities.

Each model has an ``as_dict`` property (flat-ish, JSON-serialisable) and a
``from_element(elem)`` classmethod that maps a parsed
``xml.etree.ElementTree.Element`` (one top-level entity node from the dump)
onto the dataclass. The element shapes follow the Discogs dump XML, which
mirrors the API spec at https://www.discogs.com/developers/.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pydiscogs._clean import clean_str, dedupe, parse_year, to_int


def _texts(elem, path: str) -> List[str]:
    """Collect non-empty stripped text from every node matching ``path``."""
    if elem is None:
        return []
    return [clean_str(n.text) for n in elem.findall(path) if clean_str(n.text)]


def _text(elem, path: str) -> str:
    if elem is None:
        return ""
    node = elem.find(path)
    return clean_str(node.text) if node is not None else ""


def _children(elem, path: str) -> list:
    """Return the child elements at ``path``, or ``[]`` if absent.

    ``elem.find(path) or []`` is unsafe: an ``Element``'s truth value is
    based on ``len()`` today (and raises a ``DeprecationWarning``; a future
    Python drops the check and always treats it as truthy), so an empty-but-
    present node silently falls through the same way a missing one does, and
    a truthy-but-empty edge case would try to iterate a non-list.
    """
    node = elem.find(path)
    return list(node) if node is not None else []


# ---------------------------------------------------------------------------
# Sub-dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ArtistCredit:
    """An artist reference on a release/master (the ``<artists>`` entries)."""

    id: Optional[int] = None
    name: str = ""
    role: str = ""
    join: str = ""
    anv: str = ""  # artist name variation as credited

    @property
    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "join": self.join,
            "anv": self.anv,
        }

    @classmethod
    def from_element(cls, elem) -> "ArtistCredit":
        return cls(
            id=to_int(_text(elem, "id")),
            name=_text(elem, "name"),
            role=_text(elem, "role"),
            join=_text(elem, "join"),
            anv=_text(elem, "anv"),
        )


@dataclass
class Track:
    """A single tracklist entry on a release."""

    position: str = ""
    title: str = ""
    duration: str = ""

    @property
    def as_dict(self) -> dict:
        return {
            "position": self.position,
            "title": self.title,
            "duration": self.duration,
        }

    @classmethod
    def from_element(cls, elem) -> "Track":
        return cls(
            position=_text(elem, "position"),
            title=_text(elem, "title"),
            duration=_text(elem, "duration"),
        )


@dataclass
class ReleaseFormat:
    """A physical/digital format descriptor (vinyl, CD, file, ...)."""

    name: str = ""
    qty: Optional[int] = None
    text: str = ""
    descriptions: List[str] = field(default_factory=list)

    @property
    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "qty": self.qty,
            "text": self.text,
            "descriptions": self.descriptions,
        }

    @classmethod
    def from_element(cls, elem) -> "ReleaseFormat":
        descs_node = elem.find("descriptions")
        return cls(
            name=clean_str(elem.get("name")),
            qty=to_int(elem.get("qty")),
            text=clean_str(elem.get("text")),
            descriptions=_texts(descs_node, "description"),
        )


# ---------------------------------------------------------------------------
# Top-level entities
# ---------------------------------------------------------------------------

@dataclass
class Artist:
    """A Discogs artist (from ``discogs_<date>_artists.xml.gz``)."""

    id: Optional[int] = None
    name: str = ""
    real_name: str = ""
    profile: str = ""
    data_quality: str = ""
    name_variations: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.name or (str(self.id) if self.id is not None else "")

    @property
    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "real_name": self.real_name,
            "profile": self.profile,
            "data_quality": self.data_quality,
            "name_variations": self.name_variations,
            "aliases": self.aliases,
            "members": self.members,
            "groups": self.groups,
            "urls": self.urls,
        }

    @classmethod
    def from_element(cls, elem) -> "Artist":
        return cls(
            id=to_int(_text(elem, "id")),
            name=_text(elem, "name"),
            real_name=_text(elem, "realname"),
            profile=_text(elem, "profile"),
            data_quality=_text(elem, "data_quality"),
            name_variations=_texts(elem.find("namevariations"), "name"),
            aliases=_texts(elem.find("aliases"), "name"),
            members=_texts(elem.find("members"), "name"),
            groups=_texts(elem.find("groups"), "name"),
            urls=_texts(elem.find("urls"), "url"),
        )


@dataclass
class Label:
    """A Discogs label (from ``discogs_<date>_labels.xml.gz``)."""

    id: Optional[int] = None
    name: str = ""
    contact_info: str = ""
    profile: str = ""
    data_quality: str = ""
    parent_label: str = ""
    sublabels: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.name or (str(self.id) if self.id is not None else "")

    @property
    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info,
            "profile": self.profile,
            "data_quality": self.data_quality,
            "parent_label": self.parent_label,
            "sublabels": self.sublabels,
            "urls": self.urls,
        }

    @classmethod
    def from_element(cls, elem) -> "Label":
        return cls(
            id=to_int(_text(elem, "id")),
            name=_text(elem, "name"),
            contact_info=_text(elem, "contactinfo"),
            profile=_text(elem, "profile"),
            data_quality=_text(elem, "data_quality"),
            parent_label=_text(elem, "parentLabel"),
            sublabels=_texts(elem.find("sublabels"), "label"),
            urls=_texts(elem.find("urls"), "url"),
        )


@dataclass
class Master:
    """A Discogs master release (from ``discogs_<date>_masters.xml.gz``).

    A master groups all variant releases of the same recording. ``id`` is the
    ``discogs_master_id``; ``main_release`` points at the canonical release.
    """

    id: Optional[int] = None
    main_release: Optional[int] = None
    title: str = ""
    year: Optional[int] = None
    data_quality: str = ""
    artists: List[ArtistCredit] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.title or (str(self.id) if self.id is not None else "")

    @property
    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "main_release": self.main_release,
            "title": self.title,
            "year": self.year,
            "data_quality": self.data_quality,
            "artists": [a.as_dict for a in self.artists],
            "genres": self.genres,
            "styles": self.styles,
        }

    @classmethod
    def from_element(cls, elem) -> "Master":
        # In the dump, master id is an attribute on <master id="...">.
        mid = to_int(elem.get("id")) if elem.get("id") else to_int(_text(elem, "id"))
        return cls(
            id=mid,
            main_release=to_int(_text(elem, "main_release")),
            title=_text(elem, "title"),
            year=parse_year(_text(elem, "year")),
            data_quality=_text(elem, "data_quality"),
            artists=[
                ArtistCredit.from_element(a)
                for a in _children(elem, "artists")
            ],
            genres=dedupe(_texts(elem.find("genres"), "genre")),
            styles=dedupe(_texts(elem.find("styles"), "style")),
        )


@dataclass
class Release:
    """A Discogs release (from ``discogs_<date>_releases.xml.gz``).

    ``id`` is the ``discogs_release_id``; ``master_id`` links to its
    :class:`Master`. Carries credits, genres, styles, year, formats, labels and
    the full tracklist.
    """

    id: Optional[int] = None
    master_id: Optional[int] = None
    title: str = ""
    status: str = ""
    country: str = ""
    released: str = ""
    year: Optional[int] = None
    data_quality: str = ""
    artists: List[ArtistCredit] = field(default_factory=list)
    extra_artists: List[ArtistCredit] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    catalog_numbers: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    styles: List[str] = field(default_factory=list)
    formats: List[ReleaseFormat] = field(default_factory=list)
    tracklist: List[Track] = field(default_factory=list)

    def __str__(self) -> str:
        return self.title or (str(self.id) if self.id is not None else "")

    @property
    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "master_id": self.master_id,
            "title": self.title,
            "status": self.status,
            "country": self.country,
            "released": self.released,
            "year": self.year,
            "data_quality": self.data_quality,
            "artists": [a.as_dict for a in self.artists],
            "extra_artists": [a.as_dict for a in self.extra_artists],
            "labels": self.labels,
            "catalog_numbers": self.catalog_numbers,
            "genres": self.genres,
            "styles": self.styles,
            "formats": [f.as_dict for f in self.formats],
            "tracklist": [t.as_dict for t in self.tracklist],
        }

    @classmethod
    def from_element(cls, elem) -> "Release":
        # Release id and status are attributes on <release id="..." status="...">.
        rid = to_int(elem.get("id")) if elem.get("id") else to_int(_text(elem, "id"))

        master_node = elem.find("master_id")
        master_id = to_int(master_node.text) if master_node is not None else None

        labels = []
        catnos = []
        labels_node = elem.find("labels")
        if labels_node is not None:
            for ln in labels_node.findall("label"):
                name = clean_str(ln.get("name"))
                if name:
                    labels.append(name)
                catno = clean_str(ln.get("catno"))
                if catno:
                    catnos.append(catno)

        released = _text(elem, "released")
        return cls(
            id=rid,
            master_id=master_id,
            title=_text(elem, "title"),
            status=clean_str(elem.get("status")),
            country=_text(elem, "country"),
            released=released,
            year=parse_year(released),
            data_quality=_text(elem, "data_quality"),
            artists=[
                ArtistCredit.from_element(a)
                for a in _children(elem, "artists")
            ],
            extra_artists=[
                ArtistCredit.from_element(a)
                for a in _children(elem, "extraartists")
            ],
            labels=dedupe(labels),
            catalog_numbers=dedupe(catnos),
            genres=dedupe(_texts(elem.find("genres"), "genre")),
            styles=dedupe(_texts(elem.find("styles"), "style")),
            formats=[
                ReleaseFormat.from_element(f)
                for f in _children(elem, "formats")
            ],
            tracklist=[
                Track.from_element(t)
                for t in _children(elem, "tracklist")
            ],
        )
