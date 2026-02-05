from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, Mapping


DEFAULT_TEMPLATES = {
    "stop_place": "{base_uri}/stops/{stop_id}",
    "quay": "{base_uri}/stops/{stop_place_id}/quays/{quay_id}",
    "line": "{base_uri}/lines/{line_id}",
    "service_journey": "{base_uri}/journeys/{service_journey_id}",
    "connection": "{base_uri}/connections/{departure_date}/{service_journey_id}/{sequence}",
    "operator": "{base_uri}/operators/{operator_id}",
}

KEY_ALIASES = {
    "baseUri": "base_uri",
    "stopPlace": "stop_place",
    "serviceJourney": "service_journey",
}


@dataclass
class URIStrategy:
    base_uri: str = "http://transport.example.org"
    templates: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TEMPLATES))

    @classmethod
    def from_json(cls, path: str) -> "URIStrategy":
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        base_uri = raw.get("baseUri") or raw.get("base_uri") or cls().base_uri
        templates = dict(DEFAULT_TEMPLATES)
        raw_templates = raw.get("templates") or raw
        if isinstance(raw_templates, Mapping):
            for key, value in raw_templates.items():
                normalized = KEY_ALIASES.get(key, key)
                templates[normalized] = value
        return cls(base_uri=base_uri, templates=templates)

    def _format(self, template_key: str, **values: str) -> str:
        template = self.templates.get(template_key, DEFAULT_TEMPLATES.get(template_key, ""))
        if not template:
            raise ValueError(f"Missing URI template for {template_key}")
        template = re.sub(r"\{departureTime\\([^}]+\\)\\}", "{departureTime}", template)
        merged = {"base_uri": self.base_uri, "baseUri": self.base_uri, **values}
        return template.format_map(merged)

    def stop(self, stop_id: str) -> str:
        return self._format(
            "stop_place",
            stop_id=stop_id,
            stopPlaceId=stop_id,
            stop_place_id=stop_id,
        )

    def line(self, line_id: str) -> str:
        return self._format("line", line_id=line_id, lineId=line_id)

    def service_journey(self, service_journey_id: str) -> str:
        return self._format(
            "service_journey",
            service_journey_id=service_journey_id,
            serviceJourneyId=service_journey_id,
        )

    def operator(self, operator_id: str) -> str:
        return self._format("operator", operator_id=operator_id, operatorId=operator_id)

    def connection(self, departure_date: str, service_journey_id: str, sequence: int) -> str:
        return self._format(
            "connection",
            departure_date=departure_date,
            departureTime=departure_date,
            service_journey_id=service_journey_id,
            serviceJourneyId=service_journey_id,
            sequence=sequence,
        )
