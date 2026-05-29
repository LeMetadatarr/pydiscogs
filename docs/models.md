# Models

All entities are dataclasses with an `as_dict` property (JSON-serialisable) and a
`from_element(elem)` classmethod that maps one parsed XML record onto the model.

## Artist

From `artists.xml.gz`. Fields: `id`, `name`, `real_name`, `profile`,
`data_quality`, `name_variations`, `aliases`, `members`, `groups`, `urls`.

```python
a = next(pydiscogs.stream("artists", limit=1))
a.id, a.name, a.real_name, a.aliases
```

## Label

From `labels.xml.gz`. Fields: `id`, `name`, `contact_info`, `profile`,
`data_quality`, `parent_label`, `sublabels`, `urls`.

## Master

From `masters.xml.gz`. A master groups all variant releases of one recording.
Fields: `id` (`discogs_master_id`), `main_release`, `title`, `year`,
`data_quality`, `artists` (list of `ArtistCredit`), `genres`, `styles`.

## Release

From `releases.xml.gz`. Fields: `id` (`discogs_release_id`), `master_id`,
`title`, `status`, `country`, `released`, `year`, `data_quality`, `artists`,
`extra_artists`, `labels`, `catalog_numbers`, `genres`, `styles`, `formats`
(list of `ReleaseFormat`), `tracklist` (list of `Track`).

```python
r = next(pydiscogs.stream("releases", limit=1))
for t in r.tracklist:
    print(t.position, t.title, t.duration)
```

## Sub-models

- `ArtistCredit` — `id`, `name`, `role`, `join`, `anv` (name as credited).
- `Track` — `position`, `title`, `duration`.
- `ReleaseFormat` — `name`, `qty`, `text`, `descriptions`.

## Notes

- In the `masters` / `releases` dumps the record `id` (and the release `status`)
  are XML **attributes**, not child elements; `from_element` handles both forms.
- `year` is parsed from the Discogs date string; `0` / unknown maps to `None`.
- List fields (`genres`, `styles`, `labels`, `catalog_numbers`) are de-duplicated
  order-preservingly.
