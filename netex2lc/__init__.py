"""NeTEx to Linked Connections converter."""

from .models import Connection, Stop, Line
from .netex_parser import parse_netex
from .uri import URIStrategy
from .serializers import ConnectionSerializer, serialize_connections
from .config import Config, load_config
from .validation import validate_input, detect_format

__version__ = "0.1.0"

__all__ = [
    "Connection",
    "Stop",
    "Line",
    "URIStrategy",
    "parse_netex",
    "ConnectionSerializer",
    "serialize_connections",
    "Config",
    "load_config",
    "validate_input",
    "detect_format",
]
