"""Configuration file support for netex2lc and siri2lc."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .uri import URIStrategy


@dataclass
class InputConfig:
    """Configuration for input files."""

    files: List[str] = field(default_factory=list)
    validate: bool = True


@dataclass
class SiriConfig:
    """Configuration for SIRI endpoints."""

    vehicle_monitoring: Optional[str] = None
    estimated_timetable: Optional[str] = None
    situation_exchange: Optional[str] = None
    poll_interval: int = 30


@dataclass
class OutputConfig:
    """Configuration for output."""

    format: str = "jsonld"
    destination: str = "-"
    pretty: bool = True


@dataclass
class Config:
    """Main configuration for netex2lc/siri2lc."""

    # Input configuration
    netex_files: List[str] = field(default_factory=list)
    siri_file: Optional[str] = None
    siri_type: str = "et"
    service_date: Optional[str] = None

    # Output configuration
    output_path: str = "-"
    output_format: str = "jsonld"
    pretty: bool = True

    # URI configuration
    base_uri: str = "http://transport.example.org"
    uri_templates: Dict[str, str] = field(default_factory=dict)

    # Processing options
    validate: bool = True
    strict: bool = False
    verbose: bool = False
    quiet: bool = False

    # SIRI endpoints (for daemon mode)
    siri_et_endpoint: Optional[str] = None
    siri_vm_endpoint: Optional[str] = None
    siri_sx_endpoint: Optional[str] = None
    poll_interval: int = 30

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from a dictionary."""
        config = cls()

        # Input section
        input_config = data.get("input", {})
        netex_config = input_config.get("netex", {})
        if isinstance(netex_config.get("files"), list):
            config.netex_files = netex_config["files"]
        config.validate = netex_config.get("validate", True)

        siri_config = input_config.get("siri", {})
        endpoints = siri_config.get("endpoints", {})
        config.siri_et_endpoint = endpoints.get("estimated_timetable")
        config.siri_vm_endpoint = endpoints.get("vehicle_monitoring")
        config.siri_sx_endpoint = endpoints.get("situation_exchange")
        config.poll_interval = siri_config.get("poll_interval", 30)

        # Output section
        output_config = data.get("output", {})
        config.output_format = output_config.get("format", "jsonld")
        config.output_path = output_config.get("destination", "-")
        config.pretty = output_config.get("pretty", True)

        # URI section
        uri_config = data.get("uris", {})
        config.base_uri = uri_config.get("base_uri", config.base_uri)
        if "templates" in uri_config:
            config.uri_templates = uri_config["templates"]

        # Processing options
        config.strict = data.get("strict", False)
        config.verbose = data.get("verbose", False)
        config.quiet = data.get("quiet", False)

        # Logging section
        logging_config = data.get("logging", {})
        if logging_config.get("level") == "DEBUG":
            config.verbose = True
        elif logging_config.get("level") == "ERROR":
            config.quiet = True

        return config

    def get_uri_strategy(self) -> URIStrategy:
        """Create a URIStrategy from this configuration."""
        strategy = URIStrategy(base_uri=self.base_uri)
        if self.uri_templates:
            strategy.templates.update(self.uri_templates)
        return strategy

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "input": {
                "netex": {
                    "files": self.netex_files,
                    "validate": self.validate,
                },
                "siri": {
                    "endpoints": {
                        "estimated_timetable": self.siri_et_endpoint,
                        "vehicle_monitoring": self.siri_vm_endpoint,
                        "situation_exchange": self.siri_sx_endpoint,
                    },
                    "poll_interval": self.poll_interval,
                },
            },
            "output": {
                "format": self.output_format,
                "destination": self.output_path,
                "pretty": self.pretty,
            },
            "uris": {
                "base_uri": self.base_uri,
                "templates": self.uri_templates,
            },
            "strict": self.strict,
            "verbose": self.verbose,
            "quiet": self.quiet,
        }

    def to_yaml(self) -> str:
        """Serialize configuration to YAML."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


def load_config(path: Optional[str]) -> Optional[Config]:
    """Load configuration from a file if provided.

    Args:
        path: Path to config file, or None

    Returns:
        Config object or None
    """
    if path is None:
        return None

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    return Config.from_yaml(path)


# Example config template
EXAMPLE_CONFIG = """# netex2lc configuration file

input:
  netex:
    files:
      - /data/netex/stops.xml
      - /data/netex/lines.xml
      - /data/netex/timetables.xml
    validate: true

  siri:
    endpoints:
      vehicle_monitoring: https://api.example.org/siri/vm
      estimated_timetable: https://api.example.org/siri/et
      situation_exchange: https://api.example.org/siri/sx
    poll_interval: 30

output:
  format: jsonld  # jsonld, turtle, ntriples, rdfxml
  destination: /data/output/connections.jsonld
  pretty: true

uris:
  base_uri: http://transport.example.org
  templates:
    stop_place: "{base_uri}/stops/{stop_id}"
    line: "{base_uri}/lines/{line_id}"
    service_journey: "{base_uri}/journeys/{service_journey_id}"
    connection: "{base_uri}/connections/{departure_date}/{service_journey_id}/{sequence}"
    operator: "{base_uri}/operators/{operator_id}"

# Processing options
strict: false
verbose: false
quiet: false

logging:
  level: INFO
"""
