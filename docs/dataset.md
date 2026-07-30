# Dataset: HuggingFace streaming configs and JSONL export

pydiscogs exposes the four dump entities as four dataset configs:

```python
import pydiscogs
pydiscogs.DATASET_CONFIGS
# ['labels', 'artists', 'masters', 'releases']
```

Each config streams directly from the live Discogs dump. No full download is needed to iterate or to build an iterable dataset.

## Iterate records as dicts

```python
from pydiscogs import dataset

for row in dataset.iter_records("masters", limit=1000):
    print(row["id"], row["title"], row["year"])
```

`iter_records` yields each record's `as_dict`, the same shape `export_jsonl` writes.

## Export JSONL

```python
n = dataset.export_jsonl("labels", "labels.jsonl", limit=50_000)
print("wrote", n, "rows")

# or from a cached / local dump, fully offline:
n = dataset.export_jsonl("labels", "labels.jsonl", local="discogs_labels.xml.gz")
```

## HuggingFace streaming

`dataset.streaming_configs()` describes each config: entity, record tag, and canonical id field. A HuggingFace loading script can use `iter_records(config)` as its row generator to build a streaming `IterableDataset` without materializing a dump:

```python
from datasets import IterableDataset
from pydiscogs import dataset

def gen(config="releases"):
    yield from dataset.iter_records(config)

ds = IterableDataset.from_generator(gen, gen_kwargs={"config": "releases"})
```

Because the source is streamed and `limit`-able, building a sample shard never pulls the whole multi-GB dump.

## Schema

Row schemas mirror the dataclass `as_dict` outputs documented in [models.md](models.md). The canonical join id per config:

| config     | id field              |
| ---------- | ---------------------- |
| `artists`  | `discogs_artist_id`   |
| `labels`   | `discogs_label_id`    |
| `masters`  | `discogs_master_id`   |
| `releases` | `discogs_release_id`  |

---
[← Ids](ids.md) · [Home](README.md) · [Advanced →](advanced.md)
