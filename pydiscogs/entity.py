"""Entity registry: maps each dataset name to its dump tag and model.

The four Discogs dumps are addressed by the same short names everywhere in the
library (``list_dumps`` filters, ``stream`` selects, dataset configs): ``artists``,
``labels``, ``masters``, ``releases``. This module is the single source of truth
for the mapping between a name, the XML element tag for one record, and the
dataclass that record parses into.
"""
from __future__ import annotations

from typing import Dict, NamedTuple, Type

from pydiscogs.models import Artist, Label, Master, Release


class EntitySpec(NamedTuple):
    name: str           # dataset / dump short name, e.g. "labels"
    record_tag: str     # XML tag of a single record, e.g. "label"
    model: Type         # dataclass with .from_element / .as_dict
    id_field: str       # canonical join-id key emitted by ids.py


ENTITIES: Dict[str, EntitySpec] = {
    "artists": EntitySpec("artists", "artist", Artist, "discogs_artist_id"),
    "labels": EntitySpec("labels", "label", Label, "discogs_label_id"),
    "masters": EntitySpec("masters", "master", Master, "discogs_master_id"),
    "releases": EntitySpec("releases", "release", Release, "discogs_release_id"),
}

#: Stable ordering, smallest dump first (labels ~75 MB ... releases ~10 GB).
ENTITY_NAMES = ["labels", "artists", "masters", "releases"]


def get_spec(name: str) -> EntitySpec:
    """Return the :class:`EntitySpec` for a dataset name, or raise ``KeyError``."""
    key = name.strip().lower()
    if key not in ENTITIES:
        raise KeyError(
            f"unknown entity {name!r}; expected one of {sorted(ENTITIES)}"
        )
    return ENTITIES[key]
