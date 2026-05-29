# Dumps: listing, downloading, layout

## File layout

Discogs publishes, once a month, four gzip-XML dumps plus a checksum file:

```
data/<YYYY>/discogs_<YYYYMMDD>_artists.xml.gz
data/<YYYY>/discogs_<YYYYMMDD>_labels.xml.gz
data/<YYYY>/discogs_<YYYYMMDD>_masters.xml.gz
data/<YYYY>/discogs_<YYYYMMDD>_releases.xml.gz
data/<YYYY>/discogs_<YYYYMMDD>_CHECKSUM.txt
```

Approximate compressed sizes: labels ~75 MB, artists ~420 MB, masters ~530 MB,
releases ~10 GB.

## Listing

```python
import pydiscogs

pydiscogs.list_dumps()                       # latest year, all entities
pydiscogs.list_dumps(year=2024)              # a specific year
pydiscogs.list_dumps(entity="labels")        # one entity, latest year
pydiscogs.latest_dump("releases")            # the most recent releases dump
```

Each result is a `Dump` with `.key`, `.entity`, `.date`, `.filename`,
`.download_url`.

Listing reads the Cloudflare-fronted HTML index at
`https://data.discogs.com/?prefix=data/<YYYY>/`. The underlying S3 bucket has
anonymous listing disabled, so this HTML index is the canonical enumeration path.

## Downloading (opt-in cache)

```python
path = pydiscogs.download("labels")          # caches the whole file, returns path
path = pydiscogs.download("labels", force=True)
```

The cache dir is `PYDISCOGS_CACHE` (default `~/.cache/pydiscogs`). `download`
pulls the **entire** multi-GB object — prefer `stream()` unless you genuinely
need the file on disk. A cached file can then be streamed offline:

```python
for label in pydiscogs.stream("labels", local=path):
    ...
```

## Checksums

```python
pydiscogs.checksums(year=2025)   # {filename: object_key} for the CHECKSUM files
```
