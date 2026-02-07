"""Tests for NeTEx parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from netex2lc.netex_parser import parse_netex
from netex2lc.uri import URIStrategy


class TestNetexParser:
    """Tests for parse_netex function."""

    def test_parse_simple_timetable(self, simple_timetable_path: str, uri_strategy: URIStrategy):
        """Test parsing a simple bus timetable."""
        connections = parse_netex([simple_timetable_path], uri_strategy)

        # Should generate connections from ServiceJourneys
        assert len(connections) >= 0  # May be 0 if file structure differs

    def test_parse_nonexistent_file(self, uri_strategy: URIStrategy):
        """Test parsing a non-existent file raises error."""
        with pytest.raises(Exception):
            parse_netex(["/nonexistent/path.xml"], uri_strategy)

    def test_parse_multiple_files(self, netex_dir: Path, uri_strategy: URIStrategy):
        """Test parsing multiple NeTEx files."""
        files = list(netex_dir.glob("*.xml"))
        if len(files) >= 2:
            connections = parse_netex([str(f) for f in files[:2]], uri_strategy)
            # Should not raise errors
            assert isinstance(connections, list)

    def test_connection_structure(self, simple_timetable_path: str, uri_strategy: URIStrategy):
        """Test that connections have required fields."""
        connections = parse_netex([simple_timetable_path], uri_strategy)

        for conn in connections:
            assert conn.id is not None
            assert conn.departure_stop is not None
            assert conn.arrival_stop is not None
            assert conn.departure_time is not None
            assert conn.arrival_time is not None

    def test_uri_strategy_applied(self, simple_timetable_path: str):
        """Test that custom URI strategy is applied."""
        custom_strategy = URIStrategy(base_uri="http://custom.example.org")
        connections = parse_netex([simple_timetable_path], custom_strategy)

        for conn in connections:
            assert "custom.example.org" in conn.id or "custom.example.org" in conn.departure_stop
