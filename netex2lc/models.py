"""Data models for Linked Connections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Connection:
    """A connection between two stops in the Linked Connections model.

    This represents a single leg of a journey, from one stop to the next,
    on a specific service journey.
    """

    # Required fields
    id: str
    departure_stop: str
    arrival_stop: str
    departure_time: str
    arrival_time: str

    # Journey/route information
    route: Optional[str] = None
    trip: Optional[str] = None
    operator: Optional[str] = None
    headsign: Optional[str] = None

    # Real-time delay information (from SIRI-ET)
    departure_delay: Optional[int] = None
    arrival_delay: Optional[int] = None
    departure_status: Optional[str] = None
    arrival_status: Optional[str] = None

    # Extended metadata
    transport_mode: Optional[str] = None  # bus, tram, metro, rail, ferry, etc.
    wheelchair_accessible: Optional[bool] = None
    bikes_allowed: Optional[bool] = None

    # Stop coordinates (from NeTEx StopPlace/Quay)
    departure_lat: Optional[float] = None
    departure_lon: Optional[float] = None
    arrival_lat: Optional[float] = None
    arrival_lon: Optional[float] = None

    # Additional metadata
    departure_stop_name: Optional[str] = None
    arrival_stop_name: Optional[str] = None
    line_name: Optional[str] = None
    line_public_code: Optional[str] = None

    def to_jsonld(self) -> Dict[str, Any]:
        """Convert to JSON-LD representation."""
        data: Dict[str, Any] = {
            "@id": self.id,
            "@type": "lc:Connection",
            "lc:departureStop": self._stop_jsonld(
                self.departure_stop,
                self.departure_stop_name,
                self.departure_lat,
                self.departure_lon,
            ),
            "lc:arrivalStop": self._stop_jsonld(
                self.arrival_stop,
                self.arrival_stop_name,
                self.arrival_lat,
                self.arrival_lon,
            ),
            "lc:departureTime": {
                "@value": self.departure_time,
                "@type": "xsd:dateTime",
            },
            "lc:arrivalTime": {
                "@value": self.arrival_time,
                "@type": "xsd:dateTime",
            },
        }

        if self.route:
            route_data: Dict[str, Any] = {"@id": self.route}
            if self.line_name:
                route_data["netex:Name"] = self.line_name
            if self.line_public_code:
                route_data["netex:PublicCode"] = self.line_public_code
            data["netex:line"] = route_data

        if self.trip:
            data["netex:serviceJourney"] = {"@id": self.trip}

        if self.operator:
            data["netex:operator"] = {"@id": self.operator}

        if self.headsign:
            data["gtfs:headsign"] = self.headsign

        if self.departure_delay is not None:
            data["lc:departureDelay"] = {
                "@value": str(self.departure_delay),
                "@type": "xsd:integer",
            }

        if self.arrival_delay is not None:
            data["lc:arrivalDelay"] = {
                "@value": str(self.arrival_delay),
                "@type": "xsd:integer",
            }

        if self.departure_status:
            data["siri:departureStatus"] = self.departure_status

        if self.arrival_status:
            data["siri:arrivalStatus"] = self.arrival_status

        if self.transport_mode:
            data["netex:transportMode"] = self.transport_mode

        if self.wheelchair_accessible is not None:
            data["netex:wheelchairAccessible"] = {
                "@value": str(self.wheelchair_accessible).lower(),
                "@type": "xsd:boolean",
            }

        if self.bikes_allowed is not None:
            data["gtfs:bikesAllowed"] = {
                "@value": str(self.bikes_allowed).lower(),
                "@type": "xsd:boolean",
            }

        return data

    def _stop_jsonld(
        self,
        stop_id: str,
        name: Optional[str],
        lat: Optional[float],
        lon: Optional[float],
    ) -> Dict[str, Any]:
        """Create JSON-LD representation for a stop."""
        stop_data: Dict[str, Any] = {"@id": stop_id}

        if name:
            stop_data["netex:Name"] = name

        if lat is not None and lon is not None:
            stop_data["geo:lat"] = lat
            stop_data["geo:long"] = lon

        return stop_data


@dataclass(frozen=True)
class Stop:
    """A stop place or quay."""

    id: str
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stop_type: Optional[str] = None  # stopPlace, quay
    parent_stop: Optional[str] = None  # for quays, reference to parent StopPlace
    wheelchair_accessible: Optional[bool] = None
    transport_mode: Optional[str] = None

    def to_jsonld(self, base_uri: str = "") -> Dict[str, Any]:
        """Convert to JSON-LD representation."""
        uri = f"{base_uri}/stops/{self.id}" if base_uri else self.id

        data: Dict[str, Any] = {
            "@id": uri,
            "@type": f"netex:{self.stop_type or 'StopPlace'}",
        }

        if self.name:
            data["netex:Name"] = self.name

        if self.latitude is not None and self.longitude is not None:
            data["geo:lat"] = self.latitude
            data["geo:long"] = self.longitude

        if self.parent_stop:
            data["netex:parentStopPlace"] = {"@id": self.parent_stop}

        if self.wheelchair_accessible is not None:
            data["netex:wheelchairAccessible"] = self.wheelchair_accessible

        if self.transport_mode:
            data["netex:transportMode"] = self.transport_mode

        return data


@dataclass(frozen=True)
class Line:
    """A transit line/route."""

    id: str
    name: Optional[str] = None
    public_code: Optional[str] = None
    transport_mode: Optional[str] = None
    operator: Optional[str] = None

    def to_jsonld(self, base_uri: str = "") -> Dict[str, Any]:
        """Convert to JSON-LD representation."""
        uri = f"{base_uri}/lines/{self.id}" if base_uri else self.id

        data: Dict[str, Any] = {
            "@id": uri,
            "@type": "netex:Line",
        }

        if self.name:
            data["netex:Name"] = self.name

        if self.public_code:
            data["netex:PublicCode"] = self.public_code

        if self.transport_mode:
            data["netex:transportMode"] = self.transport_mode

        if self.operator:
            data["netex:operator"] = {"@id": self.operator}

        return data
