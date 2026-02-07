"""SIRI-VM (Vehicle Monitoring) parser for real-time vehicle positions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from netex2lc.uri import URIStrategy
from netex2lc.xml_utils import ET, find_ref, find_text, iter_elements, local_name


@dataclass
class VehiclePosition:
    """Real-time vehicle position data."""

    vehicle_id: str
    recorded_at: str
    latitude: Optional[float]
    longitude: Optional[float]
    bearing: Optional[float]
    speed: Optional[float]
    delay: Optional[str]
    progress_rate: Optional[str]
    line_ref: Optional[str]
    journey_ref: Optional[str]
    operator_ref: Optional[str]
    origin_name: Optional[str]
    destination_name: Optional[str]
    destination_ref: Optional[str]
    monitored: bool
    in_congestion: bool
    current_stop_ref: Optional[str]
    next_stop_ref: Optional[str]
    occupancy: Optional[str]

    def to_jsonld(self, uri_strategy: URIStrategy) -> dict:
        """Convert to JSON-LD representation."""
        vehicle_uri = f"{uri_strategy.base_uri}/vehicles/{self.vehicle_id}"

        data = {
            "@id": vehicle_uri,
            "@type": "siri:VehicleActivity",
            "siri:recordedAtTime": {
                "@value": self.recorded_at,
                "@type": "xsd:dateTime",
            },
            "siri:monitored": self.monitored,
        }

        if self.latitude is not None and self.longitude is not None:
            data["siri:vehicleLocation"] = {
                "geo:lat": self.latitude,
                "geo:long": self.longitude,
            }

        if self.bearing is not None:
            data["siri:bearing"] = self.bearing

        if self.speed is not None:
            data["siri:speed"] = self.speed

        if self.delay:
            data["siri:delay"] = self.delay

        if self.progress_rate:
            data["siri:progressRate"] = self.progress_rate

        if self.line_ref:
            data["netex:line"] = {"@id": uri_strategy.line(self.line_ref)}

        if self.journey_ref:
            data["netex:serviceJourney"] = {"@id": uri_strategy.service_journey(self.journey_ref)}

        if self.operator_ref:
            data["netex:operator"] = {"@id": uri_strategy.operator(self.operator_ref)}

        if self.origin_name:
            data["siri:originName"] = self.origin_name

        if self.destination_name:
            data["siri:destinationName"] = self.destination_name

        if self.destination_ref:
            data["siri:destinationRef"] = {"@id": uri_strategy.stop(self.destination_ref)}

        if self.in_congestion:
            data["siri:inCongestion"] = True

        if self.current_stop_ref:
            data["siri:currentStopPoint"] = {"@id": uri_strategy.stop(self.current_stop_ref)}

        if self.next_stop_ref:
            data["siri:nextStopPoint"] = {"@id": uri_strategy.stop(self.next_stop_ref)}

        if self.occupancy:
            data["siri:occupancy"] = self.occupancy

        return data


def parse_siri_vm(path: str, uri_strategy: URIStrategy) -> List[VehiclePosition]:
    """Parse SIRI-VM (Vehicle Monitoring) XML file.

    Args:
        path: Path to SIRI-VM XML file
        uri_strategy: URI generation strategy

    Returns:
        List of VehiclePosition objects
    """
    tree = ET.parse(path)
    root = tree.getroot()

    positions: List[VehiclePosition] = []

    for activity in iter_elements(root, "VehicleActivity"):
        position = _parse_vehicle_activity(activity)
        if position:
            positions.append(position)

    return positions


def _parse_vehicle_activity(activity) -> Optional[VehiclePosition]:
    """Parse a single VehicleActivity element."""
    recorded_at = find_text(activity, ["RecordedAtTime"])
    if not recorded_at:
        return None

    # Find MonitoredVehicleJourney element
    journey = None
    for child in activity.iter():
        if local_name(child.tag) == "MonitoredVehicleJourney":
            journey = child
            break

    if journey is None:
        return None

    # Extract vehicle reference
    vehicle_id = find_text(journey, ["VehicleRef"])
    if not vehicle_id:
        vehicle_id = find_text(activity, ["VehicleMonitoringRef", "ItemIdentifier"])

    if not vehicle_id:
        return None

    # Extract location
    latitude = None
    longitude = None
    for loc in journey.iter():
        if local_name(loc.tag) == "VehicleLocation":
            lat_text = find_text(loc, ["Latitude"])
            lon_text = find_text(loc, ["Longitude"])
            if lat_text:
                try:
                    latitude = float(lat_text)
                except ValueError:
                    pass
            if lon_text:
                try:
                    longitude = float(lon_text)
                except ValueError:
                    pass
            break

    # Extract bearing
    bearing = None
    bearing_text = find_text(journey, ["Bearing"])
    if bearing_text:
        try:
            bearing = float(bearing_text)
        except ValueError:
            pass

    # Extract journey reference
    journey_ref = find_text(journey, ["DatedVehicleJourneyRef", "VehicleJourneyRef"])
    if not journey_ref:
        for ref_elem in journey.iter():
            if local_name(ref_elem.tag) == "FramedVehicleJourneyRef":
                journey_ref = find_text(ref_elem, ["DatedVehicleJourneyRef"])
                break

    # Extract next stop from OnwardCalls
    next_stop_ref = None
    for calls in journey.iter():
        if local_name(calls.tag) == "OnwardCalls":
            for call in calls.iter():
                if local_name(call.tag) == "OnwardCall":
                    next_stop_ref = find_ref(call, ["StopPointRef"])
                    break
            break

    # Extract monitored flag
    monitored_text = find_text(journey, ["Monitored"])
    monitored = monitored_text and monitored_text.lower() == "true"

    # Extract congestion flag
    congestion_text = find_text(journey, ["InCongestion"])
    in_congestion = congestion_text and congestion_text.lower() == "true"

    return VehiclePosition(
        vehicle_id=vehicle_id,
        recorded_at=recorded_at,
        latitude=latitude,
        longitude=longitude,
        bearing=bearing,
        speed=None,  # Not commonly provided in SIRI-VM
        delay=find_text(journey, ["Delay"]),
        progress_rate=find_text(journey, ["ProgressRate"]),
        line_ref=find_ref(journey, ["LineRef"]),
        journey_ref=journey_ref,
        operator_ref=find_ref(journey, ["OperatorRef"]),
        origin_name=find_text(journey, ["OriginName"]),
        destination_name=find_text(journey, ["DestinationName"]),
        destination_ref=find_ref(journey, ["DestinationRef"]),
        monitored=monitored,
        in_congestion=in_congestion,
        current_stop_ref=None,
        next_stop_ref=next_stop_ref,
        occupancy=find_text(journey, ["Occupancy", "OccupancyLevel"]),
    )


def to_jsonld(positions: List[VehiclePosition], uri_strategy: URIStrategy) -> dict:
    """Convert vehicle positions to JSON-LD document."""
    context = {
        "siri": "http://www.siri.org.uk/siri#",
        "netex": "http://data.europa.eu/949/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }

    graph = [pos.to_jsonld(uri_strategy) for pos in positions]

    return {"@context": context, "@graph": graph}
