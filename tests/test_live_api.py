"""Tests for the live Discogs API client (pydiscogs.live).

Offline tests use the JSON fixtures captured from api.discogs.com and
never touch the network.  The ``@pytest.mark.live`` tests require a valid
``DISCOGS_TOKEN`` env var and will be skipped otherwise.
"""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import pytest

from pydiscogs import live
from pydiscogs.models import Artist, Label, Master, Release

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name: str) -> dict:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Offline: parse captured fixture JSON through the model mappers
# ---------------------------------------------------------------------------

class TestArtistFromApi:
    def setup_method(self):
        self.data = _load("live_artist_1.json")

    def test_returns_artist_instance(self):
        artist = live._artist_from_api(self.data)
        assert isinstance(artist, Artist)

    def test_id(self):
        assert live._artist_from_api(self.data).id == 1

    def test_name(self):
        assert live._artist_from_api(self.data).name == "The Persuader"

    def test_real_name(self):
        assert "Dahlbäck" in live._artist_from_api(self.data).real_name

    def test_name_variations(self):
        a = live._artist_from_api(self.data)
        assert "Persuader" in a.name_variations

    def test_aliases_are_names(self):
        a = live._artist_from_api(self.data)
        assert "Jesper Dahlbäck" in a.aliases

    def test_data_quality(self):
        assert live._artist_from_api(self.data).data_quality == "Needs Vote"


class TestReleaseFromApi:
    def setup_method(self):
        self.data = _load("live_release_1.json")

    def test_returns_release_instance(self):
        assert isinstance(live._release_from_api(self.data), Release)

    def test_id(self):
        assert live._release_from_api(self.data).id == 1

    def test_title(self):
        assert live._release_from_api(self.data).title == "Stockholm"

    def test_status(self):
        assert live._release_from_api(self.data).status == "Accepted"

    def test_year(self):
        assert live._release_from_api(self.data).year == 1999

    def test_labels(self):
        r = live._release_from_api(self.data)
        assert "Svek" in r.labels

    def test_catalog_numbers(self):
        r = live._release_from_api(self.data)
        assert "SK032" in r.catalog_numbers

    def test_genres(self):
        assert "Electronic" in live._release_from_api(self.data).genres

    def test_formats(self):
        r = live._release_from_api(self.data)
        assert r.formats[0].name == "Vinyl"

    def test_tracklist(self):
        r = live._release_from_api(self.data)
        assert len(r.tracklist) > 0
        titles = [t.title for t in r.tracklist]
        assert "Östermalm" in titles

    def test_extra_artists(self):
        r = live._release_from_api(self.data)
        roles = [a.role for a in r.extra_artists]
        assert any("Written" in role for role in roles)

    def test_artists(self):
        r = live._release_from_api(self.data)
        assert r.artists[0].name == "The Persuader"
        assert r.artists[0].id == 1


class TestMasterFromApi:
    def setup_method(self):
        self.data = _load("live_master_18500.json")

    def test_returns_master(self):
        assert isinstance(live._master_from_api(self.data), Master)

    def test_id(self):
        assert live._master_from_api(self.data).id == 18500

    def test_title(self):
        assert live._master_from_api(self.data).title == "New Soil"

    def test_year(self):
        assert live._master_from_api(self.data).year == 2001

    def test_main_release(self):
        assert live._master_from_api(self.data).main_release == 155102

    def test_styles(self):
        m = live._master_from_api(self.data)
        assert "Techno" in m.styles

    def test_artists(self):
        m = live._master_from_api(self.data)
        assert m.artists[0].name == "Samuel L Session"


class TestLabelFromApi:
    def setup_method(self):
        self.data = _load("live_label_5.json")

    def test_returns_label(self):
        assert isinstance(live._label_from_api(self.data), Label)

    def test_id(self):
        assert live._label_from_api(self.data).id == 5

    def test_name(self):
        assert live._label_from_api(self.data).name == "Svek"

    def test_profile(self):
        assert "Swedish" in live._label_from_api(self.data).profile

    def test_parent_label(self):
        lb = live._label_from_api(self.data)
        assert lb.parent_label == "Goldhead Music"

    def test_sublabels(self):
        lb = live._label_from_api(self.data)
        assert "Birdy" in lb.sublabels

    def test_urls(self):
        lb = live._label_from_api(self.data)
        assert any("wikipedia" in u for u in lb.urls)


class TestSearchResponseParsing:
    def setup_method(self):
        self.data = _load("live_search_stockholm.json")

    def test_has_results(self):
        assert len(self.data["results"]) >= 1

    def test_pagination_present(self):
        assert "pagination" in self.data
        pg = self.data["pagination"]
        assert "page" in pg and "pages" in pg and "items" in pg

    def test_first_result_has_id(self):
        assert "id" in self.data["results"][0]

    def test_first_result_is_stockholm(self):
        titles = [r.get("title", "") for r in self.data["results"]]
        assert any("Stockholm" in t for t in titles)


# ---------------------------------------------------------------------------
# Offline: mock _api_get to test public function plumbing without network
# ---------------------------------------------------------------------------

class TestGetFunctionsOffline:
    """Verify that get_* functions pass correct paths and route data through
    the mappers, without making any real HTTP calls."""

    def _patch(self, monkeypatch, fixture_name: str):
        data = _load(fixture_name)
        monkeypatch.setattr(live, "_api_get", lambda path, **kw: data)
        return data

    def test_get_artist_calls_correct_path(self, monkeypatch):
        calls = []
        monkeypatch.setattr(live, "_api_get",
                            lambda path, **kw: (calls.append(path), _load("live_artist_1.json"))[1])
        live.get_artist(1)
        assert calls[0] == "/artists/1"

    def test_get_artist_returns_artist(self, monkeypatch):
        self._patch(monkeypatch, "live_artist_1.json")
        a = live.get_artist(1)
        assert isinstance(a, Artist)
        assert a.id == 1

    def test_get_release_returns_release(self, monkeypatch):
        self._patch(monkeypatch, "live_release_1.json")
        r = live.get_release(1)
        assert isinstance(r, Release)
        assert r.id == 1

    def test_get_master_returns_master(self, monkeypatch):
        self._patch(monkeypatch, "live_master_18500.json")
        m = live.get_master(18500)
        assert isinstance(m, Master)
        assert m.id == 18500

    def test_get_label_returns_label(self, monkeypatch):
        self._patch(monkeypatch, "live_label_5.json")
        lb = live.get_label(5)
        assert isinstance(lb, Label)
        assert lb.id == 5

    def test_search_builds_params(self, monkeypatch):
        params_captured = {}
        search_data = _load("live_search_stockholm.json")

        def fake_api_get(path, params=None, **kw):
            params_captured.update(params or {})
            return search_data

        monkeypatch.setattr(live, "_api_get", fake_api_get)
        live.search("Stockholm", type="release", genre="Electronic", per_page=2)
        assert params_captured.get("q") == "Stockholm"
        assert params_captured.get("type") == "release"
        assert params_captured.get("genre") == "Electronic"
        assert params_captured.get("per_page") == 2

    def test_search_iter_yields_results(self, monkeypatch):
        search_data = _load("live_search_stockholm.json")
        # Make it look like a single page so iteration stops
        paged = dict(search_data)
        paged["pagination"] = dict(search_data["pagination"], page=1, pages=1)
        monkeypatch.setattr(live, "_api_get", lambda path, **kw: paged)
        results = list(live.search_iter("Stockholm", limit=2))
        assert len(results) == 2

    def test_search_iter_respects_limit(self, monkeypatch):
        search_data = _load("live_search_stockholm.json")
        paged = dict(search_data)
        paged["pagination"] = dict(search_data["pagination"], page=1, pages=1)
        monkeypatch.setattr(live, "_api_get", lambda path, **kw: paged)
        results = list(live.search_iter("Stockholm", limit=1))
        assert len(results) == 1


# ---------------------------------------------------------------------------
# live smoke tests (require DISCOGS_TOKEN)
# ---------------------------------------------------------------------------

_needs_token = pytest.mark.skipif(
    not os.environ.get("DISCOGS_TOKEN"),
    reason="DISCOGS_TOKEN not set — skip live tests",
)


@pytest.mark.live
@_needs_token
def test_live_get_artist():
    a = live.get_artist(1)
    assert isinstance(a, Artist)
    assert a.name == "The Persuader"
    assert a.id == 1


@pytest.mark.live
@_needs_token
def test_live_get_release():
    r = live.get_release(1)
    assert isinstance(r, Release)
    assert r.title == "Stockholm"
    assert r.year == 1999


@pytest.mark.live
@_needs_token
def test_live_get_master():
    m = live.get_master(18500)
    assert isinstance(m, Master)
    assert m.title == "New Soil"
    assert m.main_release == 155102


@pytest.mark.live
@_needs_token
def test_live_get_label():
    lb = live.get_label(5)
    assert isinstance(lb, Label)
    assert lb.name == "Svek"


@pytest.mark.live
@_needs_token
def test_live_search():
    resp = live.search("Stockholm", type="release", per_page=3)
    assert "results" in resp
    assert len(resp["results"]) >= 1
    assert "pagination" in resp
