# Canonical ids & external ID dict

Discogs ids are the de-facto join keys across the music-metadata ecosystem. Each
entity contributes one canonical `<site>_id` anchor under the `discogs_`
namespace:

| entity   | canonical id          |
| -------- | --------------------- |
| Artist   | `discogs_artist_id`   |
| Label    | `discogs_label_id`    |
| Master   | `discogs_master_id`   |
| Release  | `discogs_release_id`  |

## Building the external ID dict

`*_to_extra` produces a flat `str -> str` dict of namespaced external IDs,
anchor key `discogs_id`, for cross-referencing across sources:

```python
import pydiscogs

release = next(pydiscogs.stream("releases", limit=1))
pydiscogs.release_to_extra(release)
# {
#   'discogs_release_id': '1',
#   'discogs_release_url': 'https://www.discogs.com/release/1',
#   'discogs_master_id': '5427',
#   'discogs_title': 'Stockholm',
#   'discogs_year': '1999',
#   'discogs_label': 'Svek',
#   'discogs_artist': 'The Persuader',
#   'discogs_artist_id': '1',
# }
```

`to_extra(obj)` dispatches to the right builder for any supported entity.

Beyond the anchor id, `release_to_extra` / `master_to_extra` also cross-link the
master <-> release relationship (a release carries its `discogs_master_id`; a
master carries its main `discogs_release_id`), so a downstream join can hop
either way.

## From a URL

```python
pydiscogs.id_from_url("https://www.discogs.com/release/1-Stockholm")
# ('release', 1)
pydiscogs.id_from_url("https://www.discogs.com/fr/master/18500-New-Soil")
# ('master', 18500)
```
