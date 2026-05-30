"""pydiscogs — streaming client for the Discogs monthly data dumps (no API key).

Reads the official CC0 monthly dumps from ``data.discogs.com`` — Artist, Label,
Master and Release — by stream-parsing the multi-GB gzip XML without ever loading
a whole file into memory.
"""
from __future__ import annotations

from pydiscogs.version import __version__
from pydiscogs import transport, bulk, dataset, ids
from pydiscogs.transport import set_delay, reset_session, use_requests, get_session
from pydiscogs.models import (
    Artist,
    Label,
    Master,
    Release,
    ArtistCredit,
    Track,
    ReleaseFormat,
)
from pydiscogs.entity import ENTITIES, ENTITY_NAMES, get_spec
from pydiscogs.bulk import (
    Dump,
    list_dumps,
    latest_dump,
    download,
    stream,
    stream_local,
    resolve,
    checksums,
)
from pydiscogs.dataset import (
    DATASET_CONFIGS,
    iter_records,
    export_jsonl,
    streaming_configs,
)
from pydiscogs.ids import (
    id_from_url,
    to_extra,
    artist_to_extra,
    label_to_extra,
    master_to_extra,
    release_to_extra,
)
from pydiscogs import live
from pydiscogs.live import (
    get_artist,
    get_release,
    get_master,
    get_label,
    search,
    search_iter,
)

__all__ = [
    "__version__",
    # transport
    "transport",
    "set_delay",
    "reset_session",
    "use_requests",
    "get_session",
    # models
    "Artist",
    "Label",
    "Master",
    "Release",
    "ArtistCredit",
    "Track",
    "ReleaseFormat",
    # entity registry
    "ENTITIES",
    "ENTITY_NAMES",
    "get_spec",
    # bulk
    "bulk",
    "Dump",
    "list_dumps",
    "latest_dump",
    "download",
    "stream",
    "stream_local",
    "resolve",
    "checksums",
    # dataset
    "dataset",
    "DATASET_CONFIGS",
    "iter_records",
    "export_jsonl",
    "streaming_configs",
    # ids
    "ids",
    "id_from_url",
    "to_extra",
    "artist_to_extra",
    "label_to_extra",
    "master_to_extra",
    "release_to_extra",
    # live API
    "live",
    "get_artist",
    "get_release",
    "get_master",
    "get_label",
    "search",
    "search_iter",
]
