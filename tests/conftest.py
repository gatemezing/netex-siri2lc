"""Pytest fixtures for netex-siri2lc tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from netex2lc.uri import URIStrategy


@pytest.fixture
def testdata_dir() -> Path:
    """Return path to testdata directory."""
    return Path(__file__).parent.parent / "testdata"


@pytest.fixture
def netex_dir(testdata_dir: Path) -> Path:
    """Return path to NeTEx test data directory."""
    return testdata_dir / "netex"


@pytest.fixture
def siri_dir(testdata_dir: Path) -> Path:
    """Return path to SIRI test data directory."""
    return testdata_dir / "siri"


@pytest.fixture
def uri_strategy() -> URIStrategy:
    """Return a default URI strategy for tests."""
    return URIStrategy(base_uri="http://test.example.org")


@pytest.fixture
def simple_timetable_path(netex_dir: Path) -> str:
    """Return path to simple bus timetable NeTEx file."""
    return str(netex_dir / "Netex_01.1_Bus_SimpleTimetable_JourneysOnly.xml")


@pytest.fixture
def siri_et_response_path(siri_dir: Path) -> str:
    """Return path to SIRI-ET response file."""
    return str(siri_dir / "ext_estimatedTimetable_response.xml")


@pytest.fixture
def siri_vm_response_path(siri_dir: Path) -> str:
    """Return path to SIRI-VM response file."""
    return str(siri_dir / "exv_vehicleMonitoring_response.xml")


@pytest.fixture
def siri_sx_response_path(siri_dir: Path) -> str:
    """Return path to SIRI-SX response file."""
    return str(siri_dir / "exx_situationExchange_response.xml")
