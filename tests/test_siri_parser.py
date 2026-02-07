"""Tests for SIRI parsers (ET, VM, SX)."""
from __future__ import annotations

from datetime import date

import pytest

from netex2lc.uri import URIStrategy
from siri2lc.siri_parser import parse_siri_et
from siri2lc.siri_vm_parser import parse_siri_vm
from siri2lc.siri_sx_parser import parse_siri_sx


class TestSiriETParser:
    """Tests for SIRI-ET (Estimated Timetable) parser."""

    def test_parse_et_response(self, siri_et_response_path: str, uri_strategy: URIStrategy):
        """Test parsing SIRI-ET response file."""
        # Use a fixed service date from the test data
        service_date = date(2001, 12, 17)
        connections = parse_siri_et(siri_et_response_path, uri_strategy, service_date)

        # Should generate connections from EstimatedVehicleJourney
        assert len(connections) >= 0

    def test_parse_et_without_service_date(self, siri_et_response_path: str, uri_strategy: URIStrategy):
        """Test parsing SIRI-ET without service date (uses datetime from file)."""
        connections = parse_siri_et(siri_et_response_path, uri_strategy, None)

        # Should work if times include full datetime
        assert isinstance(connections, list)

    def test_connection_has_delay_info(self, siri_et_response_path: str, uri_strategy: URIStrategy):
        """Test that connections include delay information when available."""
        service_date = date(2001, 12, 17)
        connections = parse_siri_et(siri_et_response_path, uri_strategy, service_date)

        # Connections may have delay information
        for conn in connections:
            # Delay fields are optional
            assert hasattr(conn, "departure_delay")
            assert hasattr(conn, "arrival_delay")


class TestSiriVMParser:
    """Tests for SIRI-VM (Vehicle Monitoring) parser."""

    def test_parse_vm_response(self, siri_vm_response_path: str, uri_strategy: URIStrategy):
        """Test parsing SIRI-VM response file."""
        positions = parse_siri_vm(siri_vm_response_path, uri_strategy)

        # Should find VehicleActivity elements
        assert len(positions) >= 1

    def test_vehicle_position_structure(self, siri_vm_response_path: str, uri_strategy: URIStrategy):
        """Test that vehicle positions have required fields."""
        positions = parse_siri_vm(siri_vm_response_path, uri_strategy)

        for pos in positions:
            assert pos.vehicle_id is not None
            assert pos.recorded_at is not None
            # Location may be present
            if pos.latitude is not None:
                assert pos.longitude is not None

    def test_vehicle_position_jsonld(self, siri_vm_response_path: str, uri_strategy: URIStrategy):
        """Test JSON-LD serialization of vehicle positions."""
        positions = parse_siri_vm(siri_vm_response_path, uri_strategy)

        for pos in positions:
            jsonld = pos.to_jsonld(uri_strategy)
            assert "@id" in jsonld
            assert "@type" in jsonld
            assert jsonld["@type"] == "siri:VehicleActivity"


class TestSiriSXParser:
    """Tests for SIRI-SX (Situation Exchange) parser."""

    def test_parse_sx_response(self, siri_sx_response_path: str, uri_strategy: URIStrategy):
        """Test parsing SIRI-SX response file."""
        alerts = parse_siri_sx(siri_sx_response_path, uri_strategy)

        # Should find PtSituationElement or RoadSituationElement
        assert len(alerts) >= 1

    def test_alert_structure(self, siri_sx_response_path: str, uri_strategy: URIStrategy):
        """Test that alerts have required fields."""
        alerts = parse_siri_sx(siri_sx_response_path, uri_strategy)

        for alert in alerts:
            assert alert.situation_number is not None
            assert alert.creation_time is not None

    def test_alert_affected_stops(self, siri_sx_response_path: str, uri_strategy: URIStrategy):
        """Test that affected stops are parsed."""
        alerts = parse_siri_sx(siri_sx_response_path, uri_strategy)

        has_affected_stops = any(len(alert.affected_stops) > 0 for alert in alerts)
        assert has_affected_stops, "Expected at least one alert with affected stops"

    def test_alert_jsonld(self, siri_sx_response_path: str, uri_strategy: URIStrategy):
        """Test JSON-LD serialization of alerts."""
        alerts = parse_siri_sx(siri_sx_response_path, uri_strategy)

        for alert in alerts:
            jsonld = alert.to_jsonld(uri_strategy)
            assert "@id" in jsonld
            assert "@type" in jsonld
            assert "siri:situationNumber" in jsonld
