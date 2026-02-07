"""Serializers for Linked Connections output in various RDF formats."""
from __future__ import annotations

import json
from typing import Iterable, List, Optional

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

from .models import Connection

# Namespace definitions
LC = Namespace("http://semweb.mmlab.be/ns/linkedconnections#")
NETEX = Namespace("http://data.europa.eu/949/")
GTFS = Namespace("http://vocab.gtfs.org/terms#")
SIRI = Namespace("http://www.siri.org.uk/siri#")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

# JSON-LD context
JSONLD_CONTEXT = {
    "lc": str(LC),
    "netex": str(NETEX),
    "gtfs": str(GTFS),
    "siri": str(SIRI),
    "xsd": str(XSD),
    "geo": str(GEO),
}


class ConnectionSerializer:
    """Serializer for Connection objects to various RDF formats."""

    def __init__(self, connections: Iterable[Connection]):
        self.connections = list(connections)

    def to_graph(self) -> Graph:
        """Convert connections to an RDFLib Graph."""
        g = Graph()

        # Bind namespaces for prettier output
        g.bind("lc", LC)
        g.bind("netex", NETEX)
        g.bind("gtfs", GTFS)
        g.bind("siri", SIRI)
        g.bind("geo", GEO)

        for conn in self.connections:
            self._add_connection_to_graph(g, conn)

        return g

    def _add_connection_to_graph(self, g: Graph, conn: Connection):
        """Add a single connection to the graph."""
        uri = URIRef(conn.id)

        # Type
        g.add((uri, RDF.type, LC.Connection))

        # Required properties
        g.add((uri, LC.departureStop, URIRef(conn.departure_stop)))
        g.add((uri, LC.arrivalStop, URIRef(conn.arrival_stop)))
        g.add((uri, LC.departureTime, Literal(conn.departure_time, datatype=XSD.dateTime)))
        g.add((uri, LC.arrivalTime, Literal(conn.arrival_time, datatype=XSD.dateTime)))

        # Optional properties
        if conn.route:
            g.add((uri, NETEX.line, URIRef(conn.route)))

        if conn.trip:
            g.add((uri, NETEX.serviceJourney, URIRef(conn.trip)))

        if conn.operator:
            g.add((uri, NETEX.operator, URIRef(conn.operator)))

        if conn.headsign:
            g.add((uri, GTFS.headsign, Literal(conn.headsign)))

        if conn.departure_delay is not None:
            g.add((uri, LC.departureDelay, Literal(conn.departure_delay, datatype=XSD.integer)))

        if conn.arrival_delay is not None:
            g.add((uri, LC.arrivalDelay, Literal(conn.arrival_delay, datatype=XSD.integer)))

        if conn.departure_status:
            g.add((uri, SIRI.departureStatus, Literal(conn.departure_status)))

        if conn.arrival_status:
            g.add((uri, SIRI.arrivalStatus, Literal(conn.arrival_status)))

        # Extended metadata
        if conn.transport_mode:
            g.add((uri, NETEX.transportMode, Literal(conn.transport_mode)))

        if conn.wheelchair_accessible is not None:
            g.add(
                (uri, NETEX.wheelchairAccessible, Literal(conn.wheelchair_accessible, datatype=XSD.boolean))
            )

        if conn.bikes_allowed is not None:
            g.add((uri, GTFS.bikesAllowed, Literal(conn.bikes_allowed, datatype=XSD.boolean)))

        # Stop coordinates
        if conn.departure_lat is not None and conn.departure_lon is not None:
            stop_uri = URIRef(conn.departure_stop)
            g.add((stop_uri, GEO.lat, Literal(conn.departure_lat, datatype=XSD.float)))
            g.add((stop_uri, GEO.long, Literal(conn.departure_lon, datatype=XSD.float)))

        if conn.arrival_lat is not None and conn.arrival_lon is not None:
            stop_uri = URIRef(conn.arrival_stop)
            g.add((stop_uri, GEO.lat, Literal(conn.arrival_lat, datatype=XSD.float)))
            g.add((stop_uri, GEO.long, Literal(conn.arrival_lon, datatype=XSD.float)))

    def to_jsonld(self, pretty: bool = True) -> str:
        """Serialize to JSON-LD format."""
        graph = [conn.to_jsonld() for conn in self.connections]
        data = {"@context": JSONLD_CONTEXT, "@graph": graph}
        return json.dumps(data, indent=2 if pretty else None, ensure_ascii=True)

    def to_jsonld_dict(self) -> dict:
        """Return JSON-LD as a dictionary."""
        graph = [conn.to_jsonld() for conn in self.connections]
        return {"@context": JSONLD_CONTEXT, "@graph": graph}

    def to_turtle(self) -> str:
        """Serialize to Turtle format."""
        g = self.to_graph()
        return g.serialize(format="turtle")

    def to_ntriples(self) -> str:
        """Serialize to N-Triples format."""
        g = self.to_graph()
        return g.serialize(format="nt")

    def to_rdfxml(self) -> str:
        """Serialize to RDF/XML format."""
        g = self.to_graph()
        return g.serialize(format="xml")

    def to_format(self, format_name: str, pretty: bool = True) -> str:
        """Serialize to the specified format.

        Args:
            format_name: One of 'jsonld', 'turtle', 'ttl', 'ntriples', 'nt', 'rdfxml', 'xml'
            pretty: Whether to pretty-print (applies to JSON-LD)

        Returns:
            Serialized string
        """
        format_lower = format_name.lower()

        if format_lower == "jsonld":
            return self.to_jsonld(pretty=pretty)
        elif format_lower in ("turtle", "ttl"):
            return self.to_turtle()
        elif format_lower in ("ntriples", "nt"):
            return self.to_ntriples()
        elif format_lower in ("rdfxml", "xml"):
            return self.to_rdfxml()
        else:
            raise ValueError(f"Unsupported format: {format_name}")


def serialize_connections(
    connections: Iterable[Connection],
    output_path: str,
    format_name: str = "jsonld",
    pretty: bool = True,
) -> None:
    """Serialize connections to a file.

    Args:
        connections: Iterable of Connection objects
        output_path: Path to output file, or '-' for stdout
        format_name: Output format ('jsonld', 'turtle', 'ntriples', 'rdfxml')
        pretty: Whether to pretty-print (applies to JSON-LD)
    """
    serializer = ConnectionSerializer(connections)
    content = serializer.to_format(format_name, pretty=pretty)

    if output_path == "-":
        print(content)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


# Backward compatibility with old jsonld module
def to_jsonld(connections: Iterable[Connection]) -> dict:
    """Convert connections to JSON-LD dictionary (backward compatible)."""
    return ConnectionSerializer(connections).to_jsonld_dict()


def write_jsonld(connections: Iterable[Connection], output_path: str, pretty: bool = True) -> None:
    """Write connections as JSON-LD (backward compatible)."""
    serialize_connections(connections, output_path, format_name="jsonld", pretty=pretty)
