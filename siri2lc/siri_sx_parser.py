"""SIRI-SX (Situation Exchange) parser for service alerts and disruptions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from netex2lc.uri import URIStrategy
from netex2lc.xml_utils import ET, find_ref, find_text, iter_elements, local_name


@dataclass
class AffectedStop:
    """An affected stop point or place."""

    stop_ref: str
    stop_name: Optional[str] = None
    stop_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class AffectedLine:
    """An affected line/route."""

    line_ref: str
    line_name: Optional[str] = None
    direction_ref: Optional[str] = None


@dataclass
class Consequence:
    """Consequence/impact of a situation."""

    condition: Optional[str] = None
    severity: Optional[str] = None
    blocking_journey_planner: bool = False
    blocking_realtime: bool = False
    arrival_boarding: Optional[str] = None
    departure_boarding: Optional[str] = None


@dataclass
class ServiceAlert:
    """A SIRI-SX service alert/situation."""

    situation_number: str
    creation_time: str
    participant_ref: Optional[str]
    version: Optional[str]
    progress: Optional[str]
    severity: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    reason: Optional[str]
    validity_start: Optional[str]
    validity_end: Optional[str]
    affected_stops: List[AffectedStop] = field(default_factory=list)
    affected_lines: List[AffectedLine] = field(default_factory=list)
    consequences: List[Consequence] = field(default_factory=list)
    audience: Optional[str] = None
    report_type: Optional[str] = None

    def to_jsonld(self, uri_strategy: URIStrategy) -> dict:
        """Convert to JSON-LD representation."""
        alert_uri = f"{uri_strategy.base_uri}/alerts/{self.situation_number}"

        data = {
            "@id": alert_uri,
            "@type": "siri:PtSituationElement",
            "siri:situationNumber": self.situation_number,
            "siri:creationTime": {
                "@value": self.creation_time,
                "@type": "xsd:dateTime",
            },
        }

        if self.participant_ref:
            data["siri:participantRef"] = self.participant_ref

        if self.version:
            data["siri:version"] = self.version

        if self.progress:
            data["siri:progress"] = self.progress

        if self.severity:
            data["siri:severity"] = self.severity

        if self.summary:
            data["siri:summary"] = self.summary

        if self.description:
            data["siri:description"] = self.description

        if self.reason:
            data["siri:reason"] = self.reason

        if self.validity_start:
            data["siri:validityStart"] = {
                "@value": self.validity_start,
                "@type": "xsd:dateTime",
            }

        if self.validity_end:
            data["siri:validityEnd"] = {
                "@value": self.validity_end,
                "@type": "xsd:dateTime",
            }

        if self.audience:
            data["siri:audience"] = self.audience

        if self.affected_stops:
            data["siri:affectedStopPoints"] = [
                {
                    "@id": uri_strategy.stop(stop.stop_ref),
                    "siri:stopPointName": stop.stop_name,
                }
                if stop.stop_name
                else {"@id": uri_strategy.stop(stop.stop_ref)}
                for stop in self.affected_stops
            ]

        if self.affected_lines:
            data["siri:affectedLines"] = [
                {"@id": uri_strategy.line(line.line_ref)} for line in self.affected_lines
            ]

        if self.consequences:
            data["siri:consequences"] = [
                self._consequence_to_jsonld(c) for c in self.consequences
            ]

        return data

    def _consequence_to_jsonld(self, consequence: Consequence) -> dict:
        """Convert a consequence to JSON-LD."""
        result = {}
        if consequence.condition:
            result["siri:condition"] = consequence.condition
        if consequence.severity:
            result["siri:severity"] = consequence.severity
        if consequence.blocking_journey_planner:
            result["siri:blockingJourneyPlanner"] = True
        if consequence.blocking_realtime:
            result["siri:blockingRealTime"] = True
        if consequence.arrival_boarding:
            result["siri:arrivalBoardingActivity"] = consequence.arrival_boarding
        if consequence.departure_boarding:
            result["siri:departureBoardingActivity"] = consequence.departure_boarding
        return result


def parse_siri_sx(path: str, uri_strategy: URIStrategy) -> List[ServiceAlert]:
    """Parse SIRI-SX (Situation Exchange) XML file.

    Args:
        path: Path to SIRI-SX XML file
        uri_strategy: URI generation strategy

    Returns:
        List of ServiceAlert objects
    """
    tree = ET.parse(path)
    root = tree.getroot()

    alerts: List[ServiceAlert] = []

    # Look for PtSituationElement (public transport situations)
    for situation in iter_elements(root, "PtSituationElement"):
        alert = _parse_situation(situation)
        if alert:
            alerts.append(alert)

    # Also check for RoadSituationElement which can affect PT
    for situation in iter_elements(root, "RoadSituationElement"):
        alert = _parse_situation(situation)
        if alert:
            alerts.append(alert)

    return alerts


def _parse_situation(situation) -> Optional[ServiceAlert]:
    """Parse a single PtSituationElement or RoadSituationElement."""
    situation_number = find_text(situation, ["SituationNumber"])
    creation_time = find_text(situation, ["CreationTime"])

    if not situation_number or not creation_time:
        return None

    # Parse validity period
    validity_start = None
    validity_end = None
    for period in situation.iter():
        if local_name(period.tag) == "ValidityPeriod":
            validity_start = find_text(period, ["StartTime"])
            validity_end = find_text(period, ["EndTime"])
            break

    # Parse affected stops
    affected_stops = _parse_affected_stops(situation)

    # Parse affected lines
    affected_lines = _parse_affected_lines(situation)

    # Parse consequences
    consequences = _parse_consequences(situation)

    # Get reason (various possible elements)
    reason = (
        find_text(situation, ["MiscellaneousReason"])
        or find_text(situation, ["PersonnelReason"])
        or find_text(situation, ["EquipmentReason"])
        or find_text(situation, ["EnvironmentReason"])
    )

    return ServiceAlert(
        situation_number=situation_number,
        creation_time=creation_time,
        participant_ref=find_text(situation, ["ParticipantRef"]),
        version=find_text(situation, ["Version"]),
        progress=find_text(situation, ["Progress"]),
        severity=find_text(situation, ["Severity"]),
        summary=find_text(situation, ["Summary"]),
        description=find_text(situation, ["Description"]),
        reason=reason,
        validity_start=validity_start,
        validity_end=validity_end,
        affected_stops=affected_stops,
        affected_lines=affected_lines,
        consequences=consequences,
        audience=find_text(situation, ["Audience"]),
        report_type=find_text(situation, ["ReportType"]),
    )


def _parse_affected_stops(situation) -> List[AffectedStop]:
    """Parse affected stop points from a situation."""
    stops = []

    for elem in situation.iter():
        tag = local_name(elem.tag)
        if tag == "AffectedStopPoint":
            stop_ref = find_ref(elem, ["StopPointRef"])
            if stop_ref:
                latitude = None
                longitude = None
                for loc in elem.iter():
                    if local_name(loc.tag) == "Location":
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

                stops.append(
                    AffectedStop(
                        stop_ref=stop_ref,
                        stop_name=find_text(elem, ["StopPointName"]),
                        stop_type=find_text(elem, ["StopPointType"]),
                        latitude=latitude,
                        longitude=longitude,
                    )
                )

        elif tag == "AffectedStopPlace":
            stop_ref = find_ref(elem, ["StopPlaceRef"])
            if stop_ref:
                stops.append(
                    AffectedStop(
                        stop_ref=stop_ref,
                        stop_name=find_text(elem, ["StopPlaceName"]),
                    )
                )

    return stops


def _parse_affected_lines(situation) -> List[AffectedLine]:
    """Parse affected lines from a situation."""
    lines = []

    for elem in situation.iter():
        if local_name(elem.tag) == "AffectedLine":
            line_ref = find_ref(elem, ["LineRef"])
            if line_ref:
                lines.append(
                    AffectedLine(
                        line_ref=line_ref,
                        line_name=find_text(elem, ["PublishedLineName", "LineName"]),
                        direction_ref=find_ref(elem, ["DirectionRef"]),
                    )
                )

    # Also check for LineRef directly under Affects
    for elem in situation.iter():
        if local_name(elem.tag) == "Affects":
            for child in elem.iter():
                if local_name(child.tag) == "LineRef":
                    ref = child.get("ref") or child.text
                    if ref and ref.strip():
                        ref = ref.strip()
                        # Avoid duplicates
                        if not any(l.line_ref == ref for l in lines):
                            lines.append(AffectedLine(line_ref=ref))

    return lines


def _parse_consequences(situation) -> List[Consequence]:
    """Parse consequences from a situation."""
    consequences = []

    for elem in situation.iter():
        if local_name(elem.tag) == "Consequence":
            # Parse blocking info
            blocking_jp = False
            blocking_rt = False
            for blocking in elem.iter():
                if local_name(blocking.tag) == "Blocking":
                    jp_text = find_text(blocking, ["JourneyPlanner"])
                    rt_text = find_text(blocking, ["RealTime"])
                    blocking_jp = jp_text and jp_text.lower() == "true"
                    blocking_rt = rt_text and rt_text.lower() == "true"
                    break

            # Parse boarding info
            arrival_boarding = None
            departure_boarding = None
            for boarding in elem.iter():
                if local_name(boarding.tag) == "Boarding":
                    arrival_boarding = find_text(boarding, ["ArrivalBoardingActivity"])
                    departure_boarding = find_text(boarding, ["DepartureBoardingActivity"])
                    break

            consequences.append(
                Consequence(
                    condition=find_text(elem, ["Condition"]),
                    severity=find_text(elem, ["Severity"]),
                    blocking_journey_planner=blocking_jp,
                    blocking_realtime=blocking_rt,
                    arrival_boarding=arrival_boarding,
                    departure_boarding=departure_boarding,
                )
            )

    return consequences


def to_jsonld(alerts: List[ServiceAlert], uri_strategy: URIStrategy) -> dict:
    """Convert service alerts to JSON-LD document."""
    context = {
        "siri": "http://www.siri.org.uk/siri#",
        "netex": "http://data.europa.eu/949/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
    }

    graph = [alert.to_jsonld(uri_strategy) for alert in alerts]

    return {"@context": context, "@graph": graph}
