"""Dataset helpers: HuggingFace-streaming configs and JSONL export.

The four dump entities map one-to-one onto four dataset *configs*: ``artists``,
``labels``, ``masters``, ``releases``. Each config streams from the live Discogs
dump through :func:`pydiscogs.bulk.stream`, so no full download is needed to
iterate or to build a ``datasets.IterableDataset``.
"""
from __future__ import annotations

import json
from typing import Dict, Iterator, List, Optional

from pydiscogs import bulk
from pydiscogs.entity import ENTITY_NAMES

#: Dataset config names == entity names.
DATASET_CONFIGS: List[str] = list(ENTITY_NAMES)


def iter_records(config: str, limit: Optional[int] = None) -> Iterator[dict]:
    """Yield ``as_dict`` records for a dataset config, streamed from the dump.

    Args:
        config: One of :data:`DATASET_CONFIGS`.
        limit: Stop after this many records (recommended for smoke tests).
    """
    if config not in DATASET_CONFIGS:
        raise ValueError(f"unknown config {config!r}; expected {DATASET_CONFIGS}")
    for record in bulk.stream(config, limit=limit):
        yield record.as_dict


def export_jsonl(
    config: str, path: str, limit: Optional[int] = None, local: Optional[str] = None
) -> int:
    """Stream a dataset config to a newline-delimited JSON file.

    Args:
        config: One of :data:`DATASET_CONFIGS`.
        path: Output ``.jsonl`` path.
        limit: Max records to write.
        local: Parse a local ``.xml.gz`` instead of fetching over HTTP.

    Returns:
        The number of records written.
    """
    if config not in DATASET_CONFIGS:
        raise ValueError(f"unknown config {config!r}; expected {DATASET_CONFIGS}")
    n = 0
    source = bulk.stream(config, limit=limit, local=local)
    with open(path, "w", encoding="utf-8") as fh:
        for record in source:
            fh.write(json.dumps(record.as_dict, ensure_ascii=False) + "\n")
            n += 1
    return n


def streaming_configs() -> Dict[str, dict]:
    """Describe each HuggingFace streaming config (name -> metadata).

    Returned metadata is informational (the dump tag and the canonical join-id);
    a HF loading script would use :func:`iter_records` as the row generator.
    """
    from pydiscogs.entity import ENTITIES

    return {
        name: {
            "entity": spec.name,
            "record_tag": spec.record_tag,
            "id_field": spec.id_field,
        }
        for name, spec in ENTITIES.items()
    }
