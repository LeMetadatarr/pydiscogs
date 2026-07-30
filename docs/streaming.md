# Memory-safe streaming

The Discogs dumps are gzip-compressed XML, multiple gigabytes each. The Releases dump is about 10 GB. pydiscogs never loads a whole file into memory.

`bulk.stream(name, limit)` does this:

1. **Streaming HTTP GET.** `transport.open_stream` opens the object with `stream=True` and reads it in 64 KB chunks through `Response.iter_content`.
2. **Incremental gunzip.** Each compressed chunk goes to `zlib.decompressobj(zlib.MAX_WBITS | 16)` (the `| 16` selects the gzip header window), producing XML bytes as they arrive.
3. **Incremental XML parse.** The XML bytes go to `xml.etree.ElementTree.XMLPullParser`, which emits an `end` event per element.
4. **Clear after yield.** For every completed record element, the parsed dataclass yields and then `elem.clear()` frees its subtree, so the parser's retained tree never grows.
5. **Early stop.** Once `limit` records yield, the generator returns. This closes the HTTP response and stops reading from the socket. A smoke run reads only the first chunk.

```python
import pydiscogs

# memory stays flat whether limit is 5 or 5 million
for i, release in enumerate(pydiscogs.stream("releases", limit=5)):
    print(release.id, release.title)
```

## Why not HTTP Range?

The Discogs download front ignores `Range` headers and always serves the whole object (`200`, not `206`). Memory safety here comes from streaming and early stop, not byte-range requests. The client stops reading once it has enough records, so the rest of the multi-GB body never transfers.

## Local or cached parsing

`stream(name, local="path.xml.gz")` (or `stream_local(path, entity)`) parses a local gzip file with the same incremental, element-clearing parser. This path needs no network.

---
[← Dumps](dumps.md) · [Home](README.md) · [Models →](models.md)
