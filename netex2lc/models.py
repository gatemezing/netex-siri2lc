from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Connection:
    id: str
    departure_stop: str
    arrival_stop: str
    departure_time: str
    arrival_time: str
    route: Optional[str] = None
    trip: Optional[str] = None
    operator: Optional[str] = None
    headsign: Optional[str] = None
    departure_delay: Optional[int] = None
    arrival_delay: Optional[int] = None
    departure_status: Optional[str] = None
    arrival_status: Optional[str] = None

    def to_jsonld(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "@id": self.id,
            "@type": "lc:Connection",
            "lc:departureStop": {"@id": self.departure_stop},
            "lc:arrivalStop": {"@id": self.arrival_stop},
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
            data["netex:line"] = {"@id": self.route}
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

        return data
