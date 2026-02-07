"""Tests for configuration module."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from netex2lc.config import Config, load_config, EXAMPLE_CONFIG


class TestConfig:
    """Tests for Config class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = Config()

        assert config.base_uri == "http://transport.example.org"
        assert config.output_format == "jsonld"
        assert config.pretty is True
        assert config.strict is False
        assert config.verbose is False

    def test_config_from_yaml(self):
        """Test loading config from YAML file."""
        yaml_content = """
input:
  netex:
    files:
      - /path/to/file1.xml
      - /path/to/file2.xml
    validate: true

output:
  format: turtle
  destination: /output/connections.ttl

uris:
  base_uri: http://custom.example.org

strict: true
verbose: true
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)

            config = Config.from_yaml(str(config_path))

            assert len(config.netex_files) == 2
            assert config.output_format == "turtle"
            assert config.base_uri == "http://custom.example.org"
            assert config.strict is True
            assert config.verbose is True

    def test_config_get_uri_strategy(self):
        """Test getting URI strategy from config."""
        config = Config(base_uri="http://test.example.org")
        strategy = config.get_uri_strategy()

        assert strategy.base_uri == "http://test.example.org"

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(
            base_uri="http://test.example.org",
            output_format="turtle",
            strict=True,
        )

        data = config.to_dict()

        assert data["uris"]["base_uri"] == "http://test.example.org"
        assert data["output"]["format"] == "turtle"
        assert data["strict"] is True

    def test_config_to_yaml(self):
        """Test converting config to YAML string."""
        config = Config(base_uri="http://test.example.org")
        yaml_str = config.to_yaml()

        assert "base_uri: http://test.example.org" in yaml_str

    def test_config_with_siri_endpoints(self):
        """Test config with SIRI endpoints."""
        yaml_content = """
input:
  siri:
    endpoints:
      estimated_timetable: https://api.example.org/siri/et
      vehicle_monitoring: https://api.example.org/siri/vm
    poll_interval: 60
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(yaml_content)

            config = Config.from_yaml(str(config_path))

            assert config.siri_et_endpoint == "https://api.example.org/siri/et"
            assert config.siri_vm_endpoint == "https://api.example.org/siri/vm"
            assert config.poll_interval == 60


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_none(self):
        """Test loading config with None path."""
        config = load_config(None)
        assert config is None

    def test_load_config_missing_file(self):
        """Test loading config from missing file."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_load_config_valid_file(self):
        """Test loading config from valid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("output:\n  format: jsonld\n")

            config = load_config(str(config_path))

            assert config is not None
            assert config.output_format == "jsonld"


class TestExampleConfig:
    """Tests for example configuration."""

    def test_example_config_is_valid_yaml(self):
        """Test that example config is valid YAML."""
        import yaml

        # Should not raise an error
        data = yaml.safe_load(EXAMPLE_CONFIG)

        assert "input" in data
        assert "output" in data
        assert "uris" in data
