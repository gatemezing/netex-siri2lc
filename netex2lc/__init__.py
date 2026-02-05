"""Minimal NeTEx to Linked Connections converter (MVP)."""

from .models import Connection
from .netex_parser import parse_netex
from .uri import URIStrategy

__all__ = ["Connection", "URIStrategy", "parse_netex"]
