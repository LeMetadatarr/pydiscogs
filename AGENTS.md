# AGENTS.md — pydiscogs

Streaming Python client for the Discogs monthly data dumps (`https://data.discogs.com/`, no API key, CC0 data). Stream-parses the multi-GB gzip XML dumps (Artist / Label / Master / Release) into typed dataclasses without ever loading a whole file into memory.

## Setup

```bash
pip install -e .              # requests + unblock_requests
pip install -e ".[lxml]"     # optional faster XML
pip install -e ".[dataset]"  # optional HuggingFace datasets
pip install -e ".[test]"     # pytest
```

Pure-Python, Python >= 3.8. HTTP goes through `unblock_requests.CloudflareSession`; the dump index sits behind Cloudflare.

## Test

```bash
pytest -m "not live"   # offline: gzip fixtures under tests/fixtures/
pytest -m live         # one network smoke test (partial-reads the labels dump)
```

The offline suite parses small gzipped fixtures and makes no network call. The single `live` test stream-parses the first few records of the smallest dump over HTTP with a `limit`, so it never downloads the whole file.

If the shared venv has broken third-party pytest plugins, run with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

## Layout

- `pydiscogs/__init__.py` — public API surface; re-exports transport, models, entity, bulk, dataset, ids.
- `pydiscogs/transport.py` — single shared HTTP session (`CloudflareSession`, throttled via `set_delay`), `get` (index) and `open_stream` (streaming object GET). `use_requests(True)` forces plain `requests`.
- `pydiscogs/models.py` — `Artist`, `Label`, `Master`, `Release` plus `ArtistCredit`, `Track`, `ReleaseFormat`. Each has `as_dict` and `from_element(elem)`.
- `pydiscogs/entity.py` — `ENTITIES` registry mapping dataset name -> XML record tag -> model -> canonical id field.
- `pydiscogs/bulk.py` — `list_dumps`, `latest_dump`, `download` (cached on-disk), `stream(name, limit)` (memory-safe gzip+iterparse), `stream_local`, `checksums`.
- `pydiscogs/dataset.py` — `DATASET_CONFIGS`, `iter_records`, `export_jsonl`, `streaming_configs`.
- `pydiscogs/ids.py` — `*_to_extra` (build a flat `str -> str` dict of namespaced external IDs, anchor key `discogs_id`, for cross-referencing across sources) and `id_from_url`.
- `pydiscogs/_clean.py` — internal string/number/year cleaning helpers.
- `examples/` — runnable one-call scripts; `docs/` — usage docs; `dataset.py` + `docs/dataset.md` cover HF streaming + JSONL export.

## Memory safety (hard rule)

Never load a dump into memory. `bulk.stream` inflates the gzip stream with `zlib.decompressobj` (gzip window), feeds bytes to `xml.etree.ElementTree.XMLPullParser`, and calls `elem.clear()` on every record after yielding it. `limit` stops the network read early. `download()` is opt-in and only for callers that truly need the file on disk; the cache dir is `PYDISCOGS_CACHE` (default `~/.cache/pydiscogs`).

## Conventions (org hard rules)

- Branches: work on `dev`, stable on `master`. Never use `main`. `dev` is the GitHub default branch.
- Never edit `pydiscogs/version.py`; gh-automations bumps semver from conventional-commit prefixes.
- New repos are private by default.
- Commit identity: JarbasAi <jarbasai@mailfence.com>.
- Reference `OpenVoiceOS/gh-automations` reusable workflows at `@dev`.
- No Neon / `neon-*` references.
- No meta-commentary in code/docs/commits/PRs.

## Gotchas

- The dump index is browsed via `?prefix=data/<YYYY>/` and objects fetched via `?download=<key>`; the underlying S3 bucket has anonymous **listing disabled**, so the HTML index is the only listing path.
- Object GETs ignore HTTP `Range`; memory-safety comes from streaming + early `limit`, not byte-range requests.
- Discogs rate-limits the download front (HTTP 429 with a JSON body); `transport` raises on non-2xx, so back off between heavy pulls.
- In `release`/`master` dumps, the record `id` (and release `status`) are XML **attributes**, not child elements; the models handle both forms.
- Releases dump is ~10 GB; always pass `limit` for tests/exploration.
