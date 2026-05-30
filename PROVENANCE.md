# PROVENANCE — pydiscogs

## Source

Discogs official monthly **data dumps** — the bulk export of the Discogs music
database.

- Directory index (Cloudflare-fronted): `https://data.discogs.com/?prefix=data/<YYYY>/`
- Object download: `https://data.discogs.com/?download=data/<YYYY>/<file>`
- Underlying bucket: `https://discogs-data-dumps.s3.us-west-2.amazonaws.com/`
  (object GETs are public; anonymous **listing is disabled**, which is why the
  HTML index above is used to enumerate dumps)

Four dumps are published per month, named
`discogs_<YYYYMMDD>_{artists,labels,masters,releases}.xml.gz`, alongside a
`_CHECKSUM.txt` per release date. Files are gzip-compressed XML formatted per the
Discogs API spec (https://www.discogs.com/developers/).

## Access & legality

- **No API key.** The dumps are served openly over HTTPS.
- The Discogs data is released under **CC0 1.0 (No Rights Reserved)**:
  https://creativecommons.org/about/cc0
- The download front rate-limits aggressively (HTTP 429 with a JSON body). This
  client throttles requests and surfaces non-2xx responses to the caller.

## What this client reads

- `artists.xml.gz`  -> `Artist`  (id, name, realname, profile, aliases, members, groups, urls)
- `labels.xml.gz`   -> `Label`   (id, name, contact info, profile, parent/sublabels, urls)
- `masters.xml.gz`  -> `Master`  (id, main_release, title, year, artists, genres, styles)
- `releases.xml.gz` -> `Release` (id, master_id, title, status, country, year, artists, extra credits, labels, catalog numbers, genres, styles, formats, tracklist)

Canonical join ids (flat `str -> str` dict, anchor key `discogs_id`): `discogs_artist_id`,
`discogs_label_id`, `discogs_master_id`, `discogs_release_id`.

## Reading method (memory safety)

Dumps are multi-GB (releases ~10 GB). The client never buffers a whole file:

1. Streaming HTTP GET (`Response.iter_content`).
2. Incremental gunzip via `zlib.decompressobj(zlib.MAX_WBITS | 16)`.
3. Incremental XML parse via `xml.etree.ElementTree.XMLPullParser`.
4. `elem.clear()` after each yielded record.
5. `limit` stops the network read early — smoke tests read only the first chunk.

An opt-in `download(name)` caches a full dump under `PYDISCOGS_CACHE`
(default `~/.cache/pydiscogs`); everything else streams.

## Verification

The single live smoke test (`pytest -m live`) partial-reads the **smallest**
dump (`labels`, ~75 MB compressed) and parses the first records over HTTP without
downloading the whole file. Offline tests run against small gzipped fixtures
captured from the live `2025` dumps (`labels`, `artists`) and hand-authored from
the Discogs XML spec (`masters`, `releases`).

## Optional supplement

Discogs also offers a gated REST API at `https://api.discogs.com` (token
required, rate limited) for per-record live lookups. It is documented here as an
optional supplement and is not part of the no-key dump pipeline.
