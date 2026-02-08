"""Tests for the benchmark module."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

# Import benchmark components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))

from benchmark import (
    BenchmarkResult,
    BenchmarkSummary,
    calculate_completeness,
    validate_jsonld,
    validate_uris,
    validate_datetimes,
    benchmark_netex_file,
    benchmark_siri_file,
)
from netex2lc.models import Connection
from netex2lc.uri import URIStrategy


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
            operator="http://example.org/operators/OP1",
            transport_mode="bus",
        ),
        Connection(
            id="http://example.org/connections/2",
            departure_stop="http://example.org/stops/B",
            arrival_stop="http://example.org/stops/C",
            departure_time="2026-02-05T10:35:00+00:00",
            arrival_time="2026-02-05T11:00:00+00:00",
            # Fewer optional fields
        ),
    ]


class TestBenchmarkResult:
    """Tests for BenchmarkResult dataclass."""

    def test_default_values(self):
        """Test default values for BenchmarkResult."""
        result = BenchmarkResult(
            file_path="test.xml",
            file_size_kb=10.5,
            format_type="netex",
        )

        assert result.parse_success is False
        assert result.connections_count == 0
        assert result.completeness_score == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = BenchmarkResult(
            file_path="test.xml",
            file_size_kb=10.5,
            format_type="netex",
            parse_success=True,
            connections_count=5,
            parse_time_ms=50.5,
        )

        data = result.to_dict()

        assert data["file"] == "test.xml"
        assert data["file_size_kb"] == 10.5
        assert data["parsing"]["success"] is True
        assert data["yield"]["connections"] == 5


class TestBenchmarkSummary:
    """Tests for BenchmarkSummary dataclass."""

    def test_summary_calculation(self):
        """Test summary statistics."""
        summary = BenchmarkSummary(
            total_files=10,
            netex_files=6,
            siri_files=4,
            parse_success_rate=0.9,
            total_connections=100,
        )

        data = summary.to_dict()

        assert data["summary"]["total_files"] == 10
        assert data["summary"]["parse_success_rate"] == 90.0


class TestCalculateCompleteness:
    """Tests for calculate_completeness function."""

    def test_completeness_with_connections(self, sample_connections):
        """Test completeness calculation."""
        result = calculate_completeness(sample_connections)

        assert "score" in result
        assert 0 <= result["score"] <= 1

        # First connection has route, second doesn't
        assert result.get("route", 0) == 0.5

    def test_completeness_empty_list(self):
        """Test completeness with empty list."""
        result = calculate_completeness([])

        assert result == {"score": 0.0}


class TestValidateJsonld:
    """Tests for validate_jsonld function."""

    def test_valid_jsonld(self):
        """Test valid JSON-LD structure."""
        data = {
            "@context": {"lc": "http://example.org/"},
            "@graph": [
                {"@id": "http://example.org/1", "@type": "Connection"}
            ]
        }

        assert validate_jsonld(data) is True

    def test_missing_context(self):
        """Test JSON-LD without context."""
        data = {
            "@graph": [{"@id": "http://example.org/1"}]
        }

        assert validate_jsonld(data) is False

    def test_missing_id_in_graph(self):
        """Test JSON-LD with missing @id in graph items."""
        data = {
            "@context": {},
            "@graph": [{"type": "Connection"}]  # Missing @id
        }

        assert validate_jsonld(data) is False


class TestValidateUris:
    """Tests for validate_uris function."""

    def test_valid_uris(self, sample_connections):
        """Test valid HTTP URIs."""
        assert validate_uris(sample_connections) is True

    def test_invalid_uris(self):
        """Test invalid URIs (not HTTP)."""
        connections = [
            Connection(
                id="invalid-uri",  # Not HTTP
                departure_stop="http://example.org/stops/A",
                arrival_stop="http://example.org/stops/B",
                departure_time="2026-02-05T10:00:00+00:00",
                arrival_time="2026-02-05T10:30:00+00:00",
            )
        ]

        assert validate_uris(connections) is False


class TestValidateDatetimes:
    """Tests for validate_datetimes function."""

    def test_valid_datetimes(self, sample_connections):
        """Test valid ISO 8601 datetimes."""
        assert validate_datetimes(sample_connections) is True

    def test_invalid_datetimes(self):
        """Test invalid datetime format."""
        connections = [
            Connection(
                id="http://example.org/1",
                departure_stop="http://example.org/stops/A",
                arrival_stop="http://example.org/stops/B",
                departure_time="10:00:00",  # Missing date part with T
                arrival_time="2026-02-05T10:30:00+00:00",
            )
        ]

        assert validate_datetimes(connections) is False


class TestBenchmarkNetexFile:
    """Tests for benchmark_netex_file function."""

    def test_benchmark_valid_file(self, simple_timetable_path):
        """Test benchmarking a valid NeTEx file."""
        uri_strategy = URIStrategy(base_uri="http://test.example.org")
        result = benchmark_netex_file(Path(simple_timetable_path), uri_strategy)

        assert result.format_type == "netex"
        assert result.parse_time_ms > 0
        assert result.file_size_kb > 0


class TestBenchmarkSiriFile:
    """Tests for benchmark_siri_file function."""

    def test_benchmark_siri_et(self, siri_et_response_path):
        """Test benchmarking a SIRI-ET file."""
        uri_strategy = URIStrategy(base_uri="http://test.example.org")
        result = benchmark_siri_file(Path(siri_et_response_path), uri_strategy)

        assert result.format_type == "siri"
        assert result.siri_profile == "et"

    def test_benchmark_siri_vm(self, siri_vm_response_path):
        """Test benchmarking a SIRI-VM file."""
        uri_strategy = URIStrategy(base_uri="http://test.example.org")
        result = benchmark_siri_file(Path(siri_vm_response_path), uri_strategy)

        assert result.format_type == "siri"
        assert result.siri_profile == "vm"
        assert result.vehicles_count >= 0

    def test_benchmark_siri_sx(self, siri_sx_response_path):
        """Test benchmarking a SIRI-SX file."""
        uri_strategy = URIStrategy(base_uri="http://test.example.org")
        result = benchmark_siri_file(Path(siri_sx_response_path), uri_strategy)

        assert result.format_type == "siri"
        assert result.siri_profile == "sx"
        assert result.alerts_count >= 0
