from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .models import Connection
from .uri import URIStrategy
from .xml_utils import ET, find_ref, find_text, iter_elements, local_name


@dataclass
class PassingTime:
    sequence: Optional[int]
    stop_ref: Optional[str]
    departure_time: Optional[str]
    arrival_time: Optional[str]


PASSING_TIME_TAGS = {"TimetabledPassingTime", "PassingTime"}
STOP_REF_TAGS = [
    "StopPointRef",
    "ScheduledStopPointRef",
    "StopPointInJourneyPatternRef",
    "QuayRef",
    "StopPlaceRef",
]
DEPARTURE_TIME_TAGS = ["DepartureTime", "AimedDepartureTime", "ExpectedDepartureTime"]
ARRIVAL_TIME_TAGS = ["ArrivalTime", "AimedArrivalTime", "ExpectedArrivalTime"]


def parse_netex(paths: List[str], uri_strategy: URIStrategy) -> List[Connection]:
    connections: List[Connection] = []

    for path in paths:
        tree = ET.parse(path)
        root = tree.getroot()

        for service_journey in iter_elements(root, "ServiceJourney"):
            service_journey_id = service_journey.get("id") or find_text(
                service_journey, ["ServiceJourneyRef", "ServiceJourneyId", "Id"]
            )
            if not service_journey_id:
                continue

            line_ref = find_ref(service_journey, ["LineRef"])
            operator_ref = find_ref(service_journey, ["OperatorRef", "OperatorRefStructure"])

            passing_times = _extract_passing_times(service_journey)
            if not passing_times:
                continue

            sorted_times = _sort_passing_times(passing_times)

            for idx in range(len(sorted_times) - 1):
                departure = sorted_times[idx]
                arrival = sorted_times[idx + 1]

                departure_time = departure.departure_time or departure.arrival_time
                arrival_time = arrival.arrival_time or arrival.departure_time

                if not departure_time or not arrival_time:
                    continue
                if not departure.stop_ref or not arrival.stop_ref:
                    continue

                departure_date = _date_for_uri(departure_time) or "00000000"
                connection_id = uri_strategy.connection(
                    departure_date, service_journey_id, idx + 1
                )

                connection = Connection(
                    id=connection_id,
                    departure_stop=uri_strategy.stop(departure.stop_ref),
                    arrival_stop=uri_strategy.stop(arrival.stop_ref),
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    route=uri_strategy.line(line_ref) if line_ref else None,
                    trip=uri_strategy.service_journey(service_journey_id),
                    operator=uri_strategy.operator(operator_ref) if operator_ref else None,
                )
                connections.append(connection)

    return connections


def _extract_passing_times(service_journey) -> List[PassingTime]:
    times: List[PassingTime] = []

    for child in service_journey.iter():
        if local_name(child.tag) not in PASSING_TIME_TAGS:
            continue
        sequence_text = find_text(child, ["SequenceNumber", "Order"])
        sequence = int(sequence_text) if sequence_text and sequence_text.isdigit() else None
        stop_ref = find_ref(child, STOP_REF_TAGS)
        if not stop_ref:
            continue
        departure_time = find_text(child, DEPARTURE_TIME_TAGS)
        arrival_time = find_text(child, ARRIVAL_TIME_TAGS)
        times.append(
            PassingTime(
                sequence=sequence,
                stop_ref=stop_ref,
                departure_time=departure_time,
                arrival_time=arrival_time,
            )
        )

    if times:
        return times
    return _extract_call_times(service_journey)


def _extract_call_times(service_journey) -> List[PassingTime]:
    times: List[PassingTime] = []

    for call in service_journey.iter():
        if local_name(call.tag) != "Call":
            continue
        order_text = call.get("order") or find_text(call, ["Order", "SequenceNumber"])
        sequence = int(order_text) if order_text and order_text.isdigit() else None
        stop_ref = find_ref(call, STOP_REF_TAGS)
        if not stop_ref:
            continue

        arrival_time = _find_call_time(call, "Arrival")
        departure_time = _find_call_time(call, "Departure")

        times.append(
            PassingTime(
                sequence=sequence,
                stop_ref=stop_ref,
                departure_time=departure_time,
                arrival_time=arrival_time,
            )
        )

    return times


def _find_call_time(call, name: str) -> Optional[str]:
    for child in call.iter():
        if local_name(child.tag) != name:
            continue
        value = find_text(
            child,
            [
                "Time",
                "ArrivalTime",
                "DepartureTime",
                "AimedArrivalTime",
                "AimedDepartureTime",
            ],
        )
        if value:
            return value
    return None


def _sort_passing_times(passing_times: List[PassingTime]) -> List[PassingTime]:
    if all(pt.sequence is not None for pt in passing_times):
        return sorted(passing_times, key=lambda pt: pt.sequence or 0)
    return passing_times


def _date_for_uri(time_str: str) -> Optional[str]:
    if not time_str:
        return None
    try:
        normalized = time_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt.strftime("%Y%m%d")
    except ValueError:
        if len(time_str) >= 10 and time_str[4] == "-":
            return time_str[:10].replace("-", "")
    return None
