from __future__ import annotations

import json
from typing import Iterable, List

from .models import Connection


CONTEXT = {
    "lc": "http://semweb.mmlab.be/ns/linkedconnections#",
    "netex": "http://data.europa.eu/949/",
    "gtfs": "http://vocab.gtfs.org/terms#",
    "siri": "http://www.siri.org.uk/siri#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
}


def to_jsonld(connections: Iterable[Connection]) -> dict:
    graph: List[dict] = [connection.to_jsonld() for connection in connections]
    return {"@context": CONTEXT, "@graph": graph}


def write_jsonld(connections: Iterable[Connection], output_path: str, pretty: bool = True) -> None:
    data = to_jsonld(connections)
    if output_path == "-":
        print(
            json.dumps(
                data,
                indent=2 if pretty else None,
                ensure_ascii=True,
                sort_keys=False,
            )
        )
        return

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(
            data,
            handle,
            indent=2 if pretty else None,
            ensure_ascii=True,
            sort_keys=False,
        )
