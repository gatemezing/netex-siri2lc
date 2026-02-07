"""Tests for data models."""
from __future__ import annotations

import pytest

from netex2lc.models import Connection, Stop, Line


class TestConnection:
    """Tests for Connection model."""

    def test_connection_creation(self):
        """Test creating a Connection with required fields."""
        conn = Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:00:00+00:00",
            arrival_time="2026-02-05T10:30:00+00:00",
        )

        assert conn.id == "http://example.org/connections/1"
        assert conn.departure_stop == "http://example.org/stops/A"
        assert conn.arrival_stop == "http://example.org/stops/B"

    def test_connection_with_optional_fields(self):
        """Test creating a Connection with optional fields."""
        conn = Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:00:00+00:00",
            arrival_time="2026-02-05T10:30:00+00:00",
            route="http://example.org/lines/L1",
            trip="http://example.org/journeys/J1",
            operator="http://example.org/operators/OP1",
            headsign="City Center",
            transport_mode="bus",
            wheelchair_accessible=True,
        )

        assert conn.route == "http://example.org/lines/L1"
        assert conn.headsign == "City Center"
        assert conn.transport_mode == "bus"
        assert conn.wheelchair_accessible is True

    def test_connection_to_jsonld_basic(self):
        """Test JSON-LD serialization with basic fields."""
        conn = Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:00:00+00:00",
            arrival_time="2026-02-05T10:30:00+00:00",
        )

        jsonld = conn.to_jsonld()

        assert jsonld["@id"] == "http://example.org/connections/1"
        assert jsonld["@type"] == "lc:Connection"
        assert "lc:departureStop" in jsonld
        assert "lc:arrivalStop" in jsonld
        assert "lc:departureTime" in jsonld
        assert "lc:arrivalTime" in jsonld

    def test_connection_to_jsonld_with_delay(self):
        """Test JSON-LD serialization includes delay info."""
        conn = Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:02:00+00:00",
            arrival_time="2026-02-05T10:32:00+00:00",
            departure_delay=120,
            arrival_delay=120,
            departure_status="delayed",
        )

        jsonld = conn.to_jsonld()

        assert "lc:departureDelay" in jsonld
        assert jsonld["lc:departureDelay"]["@value"] == "120"
        assert jsonld["siri:departureStatus"] == "delayed"

    def test_connection_to_jsonld_with_coordinates(self):
        """Test JSON-LD serialization includes stop coordinates."""
        conn = Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:00:00+00:00",
            arrival_time="2026-02-05T10:30:00+00:00",
            departure_lat=59.9127,
            departure_lon=10.7501,
            departure_stop_name="Oslo Central",
        )

        jsonld = conn.to_jsonld()

        assert jsonld["lc:departureStop"]["geo:lat"] == 59.9127
        assert jsonld["lc:departureStop"]["geo:long"] == 10.7501
        assert jsonld["lc:departureStop"]["netex:Name"] == "Oslo Central"


class TestStop:
    """Tests for Stop model."""

    def test_stop_creation(self):
        """Test creating a Stop."""
        stop = Stop(
            id="NSR:StopPlace:123",
            name="Oslo Central Station",
            latitude=59.9127,
            longitude=10.7501,
            stop_type="StopPlace",
        )

        assert stop.id == "NSR:StopPlace:123"
        assert stop.name == "Oslo Central Station"

    def test_stop_to_jsonld(self):
        """Test Stop JSON-LD serialization."""
        stop = Stop(
            id="NSR:StopPlace:123",
            name="Oslo Central Station",
            latitude=59.9127,
            longitude=10.7501,
        )

        jsonld = stop.to_jsonld(base_uri="http://example.org")

        assert "@id" in jsonld
        assert jsonld["netex:Name"] == "Oslo Central Station"
        assert jsonld["geo:lat"] == 59.9127


class TestLine:
    """Tests for Line model."""

    def test_line_creation(self):
        """Test creating a Line."""
        line = Line(
            id="RUT:Line:1",
            name="Frognerseteren - Bergkrystallen",
            public_code="1",
            transport_mode="metro",
        )

        assert line.id == "RUT:Line:1"
        assert line.public_code == "1"
        assert line.transport_mode == "metro"

    def test_line_to_jsonld(self):
        """Test Line JSON-LD serialization."""
        line = Line(
            id="RUT:Line:1",
            name="Line 1",
            public_code="1",
            transport_mode="bus",
        )

        jsonld = line.to_jsonld(base_uri="http://example.org")

        assert "@id" in jsonld
        assert jsonld["@type"] == "netex:Line"
        assert jsonld["netex:PublicCode"] == "1"
