"""Tests for URI strategy module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from netex2lc.uri import URIStrategy, DEFAULT_TEMPLATES


class TestURIStrategy:
    """Tests for URIStrategy class."""

    def test_default_base_uri(self):
        """Test default base URI."""
        strategy = URIStrategy()
        assert strategy.base_uri == "http://transport.example.org"

    def test_custom_base_uri(self):
        """Test custom base URI."""
        strategy = URIStrategy(base_uri="http://custom.example.org")
        assert strategy.base_uri == "http://custom.example.org"

    def test_stop_uri(self):
        """Test stop URI generation."""
        strategy = URIStrategy(base_uri="http://example.org")
        uri = strategy.stop("NSR:StopPlace:123")

        assert "example.org" in uri
        assert "NSR:StopPlace:123" in uri

    def test_line_uri(self):
        """Test line URI generation."""
        strategy = URIStrategy(base_uri="http://example.org")
        uri = strategy.line("RUT:Line:1")

        assert "example.org" in uri
        assert "RUT:Line:1" in uri

    def test_service_journey_uri(self):
        """Test service journey URI generation."""
        strategy = URIStrategy(base_uri="http://example.org")
        uri = strategy.service_journey("RUT:ServiceJourney:456")

        assert "example.org" in uri
        assert "RUT:ServiceJourney:456" in uri

    def test_operator_uri(self):
        """Test operator URI generation."""
        strategy = URIStrategy(base_uri="http://example.org")
        uri = strategy.operator("RUT:Operator:1")

        assert "example.org" in uri
        assert "RUT:Operator:1" in uri

    def test_connection_uri(self):
        """Test connection URI generation."""
        strategy = URIStrategy(base_uri="http://example.org")
        uri = strategy.connection("20260205", "SJ123", 1)

        assert "example.org" in uri
        assert "20260205" in uri
        assert "SJ123" in uri

    def test_from_json(self):
        """Test loading URI strategy from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "baseUri": "http://custom.example.org",
                "templates": {
                    "stop_place": "{base_uri}/custom/stops/{stop_id}",
                },
            }
            config_path = Path(tmpdir) / "uris.json"
            with open(config_path, "w") as f:
                json.dump(config, f)

            strategy = URIStrategy.from_json(str(config_path))

            assert strategy.base_uri == "http://custom.example.org"
            assert "custom/stops" in strategy.templates.get("stop_place", "")

    def test_default_templates_exist(self):
        """Test that default templates are defined."""
        assert "stop_place" in DEFAULT_TEMPLATES
        assert "line" in DEFAULT_TEMPLATES
        assert "service_journey" in DEFAULT_TEMPLATES
        assert "connection" in DEFAULT_TEMPLATES
        assert "operator" in DEFAULT_TEMPLATES

    def test_custom_templates(self):
        """Test custom templates override defaults."""
        custom_templates = {
            "stop_place": "{base_uri}/v2/stops/{stop_id}",
        }
        strategy = URIStrategy(
            base_uri="http://example.org",
            templates={**DEFAULT_TEMPLATES, **custom_templates},
        )

        uri = strategy.stop("TEST123")
        assert "/v2/stops/" in uri
