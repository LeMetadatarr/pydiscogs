# Advanced: caching, throttling, rate limits, REST API

## Cache directory

`download(name)` caches a full dump on disk and returns its path. The cache root is `PYDISCOGS_CACHE`, which defaults to `$XDG_CACHE_HOME/pydiscogs` (typically `~/.cache/pydiscogs`).

```bash
export PYDISCOGS_CACHE=/data/discogs-dumps
```

```python
path = pydiscogs.download("labels")          # whole file, cached
for label in pydiscogs.stream("labels", local=path):
    ...
```

`download` writes to a `.part` file and renames it atomically on success. A second call skips the download unless `force=True`.

## Throttling

The transport enforces a minimum delay between requests (default 0.5 s):

```python
pydiscogs.set_delay(2.0)   # be gentler
pydiscogs.set_delay(0.0)   # disable (used by tests)
```

## Rate limits

The Discogs download front rate-limits aggressively and answers a throttled request with HTTP `429` and a small JSON body. The transport raises on any non-2xx response, so a `429` surfaces as `requests.HTTPError`. Back off (raise `set_delay`, retry later) when pulling many objects.

## Transport backend

HTTP runs through `unblock_requests.CloudflareSession` (the dump index is Cloudflare-fronted). For offline or mocked environments:

```python
pydiscogs.use_requests(True)   # force plain requests, drop the session
pydiscogs.reset_session()      # rebuild the session on next call
```

## Optional supplement: the gated REST API

For per-record live lookups, Discogs offers a REST API at `https://api.discogs.com` (exposed as `transport.API_URL`). This API requires a token and is rate limited, so it is not part of the no-key dump pipeline. Use it only as an optional supplement, when you need a single live record rather than a bulk pass. See [live-api.md](live-api.md).

---
[← Dataset](dataset.md) · [Home](README.md) · [Live API →](live-api.md)
