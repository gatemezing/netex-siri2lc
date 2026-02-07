"""Tests for serializers module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from netex2lc.models import Connection
from netex2lc.serializers import ConnectionSerializer, serialize_connections


@pytest.fixture
def sample_connections():
    """Create sample connections for testing."""
    return [
        Connection(
            id="http://example.org/connections/1",
            departure_stop="http://example.org/stops/A",
            arrival_stop="http://example.org/stops/B",
            departure_time="2026-02-05T10:00:00+00:00",
            arrival_time="2026-02-05T10:30:00+00:00",
            route="http://example.org/lines/L1",
        ),
        Connection(
            id="http://example.org/connections/2",
            departure_stop="http://example.org/stops/B",
            arrival_stop="http://example.org/stops/C",
            departure_time="2026-02-05T10:35:00+00:00",
            arrival_time="2026-02-05T11:00:00+00:00",
            route="http://example.org/lines/L1",
        ),
    ]


class TestConnectionSerializer:
    """Tests for ConnectionSerializer class."""

    def test_to_jsonld(self, sample_connections):
        """Test JSON-LD serialization."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_jsonld()

        # Should be valid JSON
        data = json.loads(output)

        assert "@context" in data
        assert "@graph" in data
        assert len(data["@graph"]) == 2

    def test_to_jsonld_dict(self, sample_connections):
        """Test JSON-LD dictionary output."""
        serializer = ConnectionSerializer(sample_connections)
        data = serializer.to_jsonld_dict()

        assert "@context" in data
        assert "lc" in data["@context"]
        assert "netex" in data["@context"]

    def test_to_turtle(self, sample_connections):
        """Test Turtle serialization."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_turtle()

        # Should contain namespace prefixes
        assert "@prefix" in output or "PREFIX" in output.upper()
        # Should contain connection URIs
        assert "example.org" in output

    def test_to_ntriples(self, sample_connections):
        """Test N-Triples serialization."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_ntriples()

        # N-Triples format: each line is a triple
        lines = [l for l in output.strip().split("\n") if l.strip()]
        assert len(lines) >= 2  # At least some triples

        # Each line should end with a period
        for line in lines:
            assert line.strip().endswith(".")

    def test_to_rdfxml(self, sample_connections):
        """Test RDF/XML serialization."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_rdfxml()

        # Should be valid XML
        assert "<?xml" in output or "<rdf:RDF" in output

    def test_to_format_jsonld(self, sample_connections):
        """Test to_format with jsonld."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_format("jsonld")

        data = json.loads(output)
        assert "@context" in data

    def test_to_format_turtle(self, sample_connections):
        """Test to_format with turtle."""
        serializer = ConnectionSerializer(sample_connections)
        output = serializer.to_format("turtle")
        output_ttl = serializer.to_format("ttl")

        assert output == output_ttl

    def test_to_format_invalid(self, sample_connections):
        """Test to_format with invalid format."""
        serializer = ConnectionSerializer(sample_connections)

        with pytest.raises(ValueError):
            serializer.to_format("invalid_format")


class TestSerializeConnections:
    """Tests for serialize_connections function."""

    def test_serialize_to_file(self, sample_connections):
        """Test serializing connections to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonld"

            serialize_connections(sample_connections, str(output_path), format_name="jsonld")

            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert "@context" in data
            assert len(data["@graph"]) == 2

    def test_serialize_turtle_to_file(self, sample_connections):
        """Test serializing connections as Turtle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.ttl"

            serialize_connections(sample_connections, str(output_path), format_name="turtle")

            assert output_path.exists()
            content = output_path.read_text()
            assert "example.org" in content

    def test_serialize_compact_json(self, sample_connections):
        """Test compact JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.jsonld"

            serialize_connections(
                sample_connections, str(output_path), format_name="jsonld", pretty=False
            )

            content = output_path.read_text()
            # Compact output should have no newlines within the JSON structure
            # (or minimal newlines)
            assert content.count("\n") < 10
