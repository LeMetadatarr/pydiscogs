"""Offline tests (gzip fixtures) plus one live smoke test (-m live)."""
import json
import os

import pytest

import pydiscogs
from pydiscogs import bulk, dataset, ids
from pydiscogs.models import Artist, Label, Master, Release


def _fixture(fixtures_dir, name):
    return os.path.join(fixtures_dir, f"sample_{name}.xml.gz")


# ---------------------------------------------------------------------------
# parsing each entity from offline gzip fixtures
# ---------------------------------------------------------------------------

def test_stream_labels_offline(fixtures_dir):
    labels = list(bulk.stream_local(_fixture(fixtures_dir, "labels"), "labels"))
    assert labels, "expected at least one label"
    first = labels[0]
    assert isinstance(first, Label)
    assert first.id == 1
    assert first.name == "Planet E"
    assert any("planet-e" in u for u in first.urls)


def test_stream_artists_offline(fixtures_dir):
    artists = list(bulk.stream_local(_fixture(fixtures_dir, "artists"), "artists"))
    assert artists
    first = artists[0]
    assert isinstance(first, Artist)
    assert first.id == 1
    assert first.name == "The Persuader"
    assert first.real_name == "Jesper Dahlbäck"
    assert "Persuader" in first.name_variations


def test_stream_masters_offline(fixtures_dir):
    masters = list(bulk.stream_local(_fixture(fixtures_dir, "masters"), "masters"))
    assert masters
    m = masters[0]
    assert isinstance(m, Master)
    assert m.id == 18500
    assert m.main_release == 155102
    assert m.year == 2001
    assert m.title == "New Soil"
    assert "Techno" in m.styles
    assert m.artists[0].name == "Samuel L Session"


def test_stream_releases_offline(fixtures_dir):
    releases = list(bulk.stream_local(_fixture(fixtures_dir, "releases"), "releases"))
    assert releases
    r = releases[0]
    assert isinstance(r, Release)
    assert r.id == 1
    assert r.status == "Accepted"
    assert r.master_id == 5427
    assert r.year == 1999
    assert r.title == "Stockholm"
    assert r.labels == ["Svek"]  # de-duped
    assert "SK032" in r.catalog_numbers
    assert r.formats[0].name == "Vinyl"
    assert "12\"" in r.formats[0].descriptions
    assert len(r.tracklist) == 3
    assert r.tracklist[0].title == "Östermalm"
    assert r.extra_artists[0].role.startswith("Music By")


# ---------------------------------------------------------------------------
# limit / memory-safety behaviour
# ---------------------------------------------------------------------------

def test_limit_stops_early(fixtures_dir):
    got = list(bulk.stream_local(_fixture(fixtures_dir, "artists"), "artists", limit=2))
    assert len(got) == 2


def test_elements_are_cleared(fixtures_dir):
    # The generator must not retain prior records; iterating twice independently
    # yields the same first id without state bleed.
    a = next(bulk.stream_local(_fixture(fixtures_dir, "labels"), "labels"))
    b = next(bulk.stream_local(_fixture(fixtures_dir, "labels"), "labels"))
    assert a.id == b.id == 1


# ---------------------------------------------------------------------------
# ids / external ID dict
# ---------------------------------------------------------------------------

def test_release_to_extra(fixtures_dir):
    r = next(bulk.stream_local(_fixture(fixtures_dir, "releases"), "releases"))
    extra = ids.release_to_extra(r)
    assert extra["discogs_release_id"] == "1"
    assert extra["discogs_master_id"] == "5427"
    assert extra["discogs_label"] == "Svek"
    assert extra["discogs_release_url"].endswith("/release/1")


def test_to_extra_dispatch(fixtures_dir):
    label = next(bulk.stream_local(_fixture(fixtures_dir, "labels"), "labels"))
    extra = ids.to_extra(label)
    assert extra["discogs_label_id"] == "1"


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.discogs.com/release/1-Stockholm", ("release", 1)),
        ("https://www.discogs.com/artist/239", ("artist", 239)),
        ("https://www.discogs.com/fr/master/18500-New-Soil", ("master", 18500)),
        ("not a url", None),
    ],
)
def test_id_from_url(url, expected):
    assert ids.id_from_url(url) == expected


# ---------------------------------------------------------------------------
# dataset export
# ---------------------------------------------------------------------------

def test_export_jsonl(fixtures_dir, tmp_path):
    out = tmp_path / "labels.jsonl"
    n = dataset.export_jsonl("labels", str(out), local=_fixture(fixtures_dir, "labels"))
    assert n > 0
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == n
    rec = json.loads(lines[0])
    assert rec["id"] == 1
    assert rec["name"] == "Planet E"


def test_dataset_configs():
    assert set(dataset.DATASET_CONFIGS) == {"artists", "labels", "masters", "releases"}
    cfgs = dataset.streaming_configs()
    assert cfgs["releases"]["id_field"] == "discogs_release_id"


def test_public_api():
    assert pydiscogs.__version__ == "0.0.1"
    for sym in ("stream", "list_dumps", "download", "export_jsonl", "id_from_url"):
        assert hasattr(pydiscogs, sym)


# ---------------------------------------------------------------------------
# live smoke (network) — run with: pytest -m live
# ---------------------------------------------------------------------------

@pytest.mark.live
def test_live_stream_labels_first_records():
    """Partial-read the smallest dump (labels) over HTTP and parse a few records.

    Does NOT download the whole multi-GB file: the stream stops at ``limit``.
    """
    got = list(pydiscogs.stream("labels", limit=3))
    assert len(got) == 3
    assert all(isinstance(x, Label) for x in got)
    assert all(x.id is not None for x in got)
