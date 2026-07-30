# Quickstart

## Install

```bash
pip install -e .
```

Quickstart requires Python 3.8 or later and `unblock_requests` (the dump index is Cloudflare-fronted).

## Stream records

```python
import pydiscogs

for label in pydiscogs.stream("labels", limit=20):
    print(label.id, label.name, label.urls)
```

`stream(name, limit)` accepts an entity name (`artists`, `labels`, `masters`, or `releases`) or a full object key. With `limit` set, it stops reading from the network as soon as it has enough records. It never downloads the whole file.

## List what is available

```python
for d in pydiscogs.list_dumps():           # latest year
    print(d.date, d.entity, d.filename)

for d in pydiscogs.list_dumps(year=2024, entity="releases"):
    print(d.key)
```

## Export to JSONL

```python
n = pydiscogs.export_jsonl("masters", "masters_sample.jsonl", limit=1000)
print("wrote", n, "records")
```

## Get the canonical join id

```python
release = next(pydiscogs.stream("releases", limit=1))
print(pydiscogs.release_to_extra(release)["discogs_release_id"])
```

---
[Home](README.md) · [Dumps →](dumps.md)
