from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time
from typing import List, Optional

from netex2lc.models import Connection
from netex2lc.uri import URIStrategy
from netex2lc.xml_utils import ET, find_ref, find_text, iter_elements, local_name


@dataclass
class EstimatedCall:
    stop_ref: Optional[str]
    aimed_arrival: Optional[str]
    expected_arrival: Optional[str]
    aimed_departure: Optional[str]
    expected_departure: Optional[str]
    arrival_status: Optional[str]
    departure_status: Optional[str]


def parse_siri_et(path: str, uri_strategy: URIStrategy, service_date: Optional[date]) -> List[Connection]:
    tree = ET.parse(path)
    root = tree.getroot()

    connections: List[Connection] = []

    for journey in iter_elements(root, "EstimatedVehicleJourney"):
        journey_id = find_text(journey, ["DatedVehicleJourneyRef", "VehicleJourneyRef"])
        if not journey_id:
            continue
        line_ref = find_ref(journey, ["LineRef"])

        calls = _extract_estimated_calls(journey)
        if not calls:
            continue

        for idx in range(len(calls) - 1):
            departure = calls[idx]
            arrival = calls[idx + 1]

            dep_time = _choose_time(departure.expected_departure, departure.aimed_departure)
            arr_time = _choose_time(arrival.expected_arrival, arrival.aimed_arrival)

            dep_dt = _normalize_time(dep_time, service_date)
            arr_dt = _normalize_time(arr_time, service_date)

            if dep_dt is None or arr_dt is None:
                continue

            if not departure.stop_ref or not arrival.stop_ref:
                continue

            departure_date = dep_dt.strftime("%Y%m%d")
            connection_id = uri_strategy.connection(departure_date, journey_id, idx + 1)

            departure_delay = _delay_seconds(departure.aimed_departure, departure.expected_departure, service_date)
            arrival_delay = _delay_seconds(arrival.aimed_arrival, arrival.expected_arrival, service_date)

            connections.append(
                Connection(
                    id=connection_id,
                    departure_stop=uri_strategy.stop(departure.stop_ref),
                    arrival_stop=uri_strategy.stop(arrival.stop_ref),
                    departure_time=dep_dt.isoformat(),
                    arrival_time=arr_dt.isoformat(),
                    route=uri_strategy.line(line_ref) if line_ref else None,
                    trip=uri_strategy.service_journey(journey_id),
                    departure_delay=departure_delay,
                    arrival_delay=arrival_delay,
                    departure_status=departure.departure_status,
                    arrival_status=arrival.arrival_status,
                )
            )

    return connections


def _extract_estimated_calls(journey) -> List[EstimatedCall]:
    calls: List[EstimatedCall] = []

    for call in journey.iter():
        if local_name(call.tag) != "EstimatedCall":
            continue

        calls.append(
            EstimatedCall(
                stop_ref=find_ref(call, ["StopPointRef", "ScheduledStopPointRef"]),
                aimed_arrival=find_text(call, ["AimedArrivalTime"]),
                expected_arrival=find_text(call, ["ExpectedArrivalTime"]),
                aimed_departure=find_text(call, ["AimedDepartureTime"]),
                expected_departure=find_text(call, ["ExpectedDepartureTime"]),
                arrival_status=find_text(call, ["ArrivalStatus"]),
                departure_status=find_text(call, ["DepartureStatus"]),
            )
        )

    return calls


def _choose_time(expected: Optional[str], aimed: Optional[str]) -> Optional[str]:
    return expected or aimed


def _normalize_time(value: Optional[str], service_date: Optional[date]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    if service_date is None:
        return None

    try:
        parsed = time.fromisoformat(value)
        return datetime.combine(service_date, parsed)
    except ValueError:
        return None


def _delay_seconds(aimed: Optional[str], expected: Optional[str], service_date: Optional[date]) -> Optional[int]:
    aimed_dt = _normalize_time(aimed, service_date)
    expected_dt = _normalize_time(expected, service_date)
    if aimed_dt is None or expected_dt is None:
        return None
    return int((expected_dt - aimed_dt).total_seconds())
