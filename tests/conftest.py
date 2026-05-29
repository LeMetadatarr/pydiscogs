"""Shared pytest configuration for pydiscogs tests."""
import os

import pytest

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir() -> str:
    return FIXTURES


@pytest.fixture(autouse=True)
def _no_throttle():
    """Drop the inter-request delay so the live smoke test is not slowed."""
    import pydiscogs

    pydiscogs.set_delay(0.0)
    yield
