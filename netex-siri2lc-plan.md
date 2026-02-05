# NeTEx2LC & SIRI2LC: Proposal for European Transit Data to Linked Connections Converters

## Executive Summary

This document proposes the development of **netex2lc** and **siri2lc**, a pair of converters equivalent to the gtfs2lc tool suite, designed to transform European standard transit data formats (NeTEx and SIRI) into Linked Connections using RDF and Linked Data principles.

**Key Innovation**: Leverage existing NeTEx RDF ontology (http://data.europa.eu/949/) to create a seamless conversion pipeline from European transit standards to Linked Connections.

---

## Table of Contents

1. [Background and Motivation](#1-background-and-motivation)
2. [Architecture Overview](#2-architecture-overview)
3. [NeTEx2LC: Static Data Converter](#3-netex2lc-static-data-converter)
4. [SIRI2LC: Real-time Data Converter](#4-siri2lc-real-time-data-converter)
5. [Technical Specifications](#5-technical-specifications)
6. [Implementation Plan](#6-implementation-plan)
7. [Usage Examples](#7-usage-examples)
8. [Comparison with GTFS-LC](#8-comparison-with-gtfs-lc)
9. [Integration with Existing Tools](#9-integration-with-existing-tools)
10. [Roadmap and Milestones](#10-roadmap-and-milestones)

---

## 1. Background and Motivation

### 1.1 The European Transit Data Challenge

**Problem**: EU Regulation 2017/1926 mandates NeTEx and SIRI as official standards for National Access Points (NAPs), but:
- Limited tooling for consuming these formats
- Verbose XML structure hinders web applications
- No standard approach for client-side route planning
- Difficult integration with Linked Data ecosystems

**Solution**: Create converters that:
- Transform NeTEx/SIRI into RDF-based Linked Connections
- Enable client-side route planning like gtfs2lc/gtfsrt2lc
- Support federated queries across European NAPs
- Provide RESTful, cacheable transit data

### 1.2 Why Linked Connections?

The Linked Connections framework offers:
- **Hypermedia-driven**: Self-describing, follow-your-nose discovery
- **Client-side routing**: Reduces server computational load
- **HTTP-cacheable**: CDN-friendly, scalable architecture
- **Linked Data**: URIs for everything, SPARQL-queryable
- **Incremental updates**: Efficient real-time data integration

### 1.3 Existing Assets

This proposal builds on:
- **NeTEx RDF Ontology**: http://data.europa.eu/949/ (already available)
- **Transmodel Ontology**: https://w3id.org/transmodel/terms#
- **Linked Connections Spec**: https://linkedconnections.org/specification/1-0
- **GTFS-LC Experience**: Proven architecture from gtfs2lc/gtfsrt2lc
- **European NAPs**: Growing dataset of NeTEx/SIRI feeds

---

## 2. Architecture Overview

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    European Transit Data                     │
├─────────────────────────────────────────────────────────────┤
│  NeTEx XML Files          │         SIRI XML Feeds          │
│  (Static Schedules)       │       (Real-time Updates)       │
└────────────┬──────────────┴──────────────┬──────────────────┘
             │                              │
             ▼                              ▼
    ┌────────────────┐            ┌────────────────┐
    │   netex2lc     │            │    siri2lc     │
    │   Converter    │            │   Converter    │
    └────────┬───────┘            └────────┬───────┘
             │                              │
             │  Uses NeTEx RDF Ontology     │
             │  (data.europa.eu/949/)       │
             │                              │
             ▼                              ▼
    ┌────────────────────────────────────────────────┐
    │         Linked Connections (RDF)               │
    │   JSON-LD / Turtle / N-Triples / JSON          │
    └────────────────┬───────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────┐
    │          Publishing & Consumption              │
    ├────────────────────────────────────────────────┤
    │ • HTTP Server (Routable Tiles)                 │
    │ • Triple Store (SPARQL Endpoint)               │
    │ • Linked Data Fragments Server                 │
    │ • Client-side Route Planners                   │
    └────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: Parse NeTEx XML                                      │
│   Input: NeTEx PublicationDelivery XML files                 │
│   Process: XML parsing, validation against XSD              │
│   Output: In-memory object model                            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 2: Map to NeTEx RDF Ontology                            │
│   Input: Parsed NeTEx objects                                │
│   Process: Apply RML/R2RML mappings OR direct OWL mapping   │
│   Output: RDF triples (NeTEx namespace)                     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: Transform to Linked Connections                      │
│   Input: NeTEx RDF triples                                   │
│   Process: SPARQL CONSTRUCT or custom transformation        │
│   Output: Linked Connections RDF (lc: namespace)            │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ STEP 4: Serialize & Publish                                  │
│   Input: Linked Connections RDF                              │
│   Process: Serialize to JSON-LD, Turtle, N-Triples, or JSON │
│   Output: Published fragments (time-based pages)            │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Technology Stack

**Programming Language**: Python or Node.js (following gtfs2lc precedent)
- Python: Better XML/RDF ecosystem (rdflib, lxml)
- Node.js: Consistency with gtfs2lc, streaming architecture

**Recommended**: **Python** for initial implementation

**Core Dependencies**:
- `lxml` - NeTEx/SIRI XML parsing
- `rdflib` - RDF graph manipulation
- `pyshacl` - SHACL validation (using shacl_netex.ttl)
- `SPARQLWrapper` - SPARQL queries
- `click` - CLI interface
- `jsonld` - JSON-LD serialization

---

## 3. NeTEx2LC: Static Data Converter

### 3.1 Purpose

Convert NeTEx XML publications (static timetable data) into Linked Connections representing scheduled connections between stops.

### 3.2 Input Format: NeTEx

**Structure**:
```xml
<PublicationDelivery version="1.1"
    xmlns="http://www.netex.org.uk/netex">
  <PublicationTimestamp>2026-02-05T00:00:00Z</PublicationTimestamp>
  <ParticipantRef>OperatorXYZ</ParticipantRef>

  <dataObjects>
    <CompositeFrame>
      <frames>
        <!-- SiteFrame: StopPlaces, Quays -->
        <!-- ServiceFrame: Lines, Routes, JourneyPatterns -->
        <!-- TimetableFrame: ServiceJourneys, PassingTimes -->
        <!-- FareFrame: Fare products, pricing -->
      </frames>
    </CompositeFrame>
  </dataObjects>
</PublicationDelivery>
```

**Key NeTEx Classes** (mapped to RDF ontology):
- `StopPlace` → http://data.europa.eu/949/StopPlace_VersionStructure
- `Quay` → http://data.europa.eu/949/Quay_VersionStructure
- `Line` → http://data.europa.eu/949/Line_VersionStructure
- `Route` → http://data.europa.eu/949/Route_VersionStructure
- `ServiceJourney` → http://data.europa.eu/949/ServiceJourney_VersionStructure
- `TimetabledPassingTime` → http://data.europa.eu/949/TimetabledPassingTime_VersionedChildStructure

### 3.3 Transformation Logic

#### 3.3.1 Connection Generation

A **Connection** is created for each consecutive pair of TimetabledPassingTimes in a ServiceJourney:

```python
for service_journey in timetable_frame.service_journeys:
    passing_times = service_journey.passing_times  # sorted by sequence

    for i in range(len(passing_times) - 1):
        departure_pt = passing_times[i]
        arrival_pt = passing_times[i + 1]

        connection = LinkedConnection(
            id=generate_uri(service_journey, departure_pt, arrival_pt),
            departure_stop=departure_pt.stop_point_ref,
            departure_time=departure_pt.departure_time,
            arrival_stop=arrival_pt.stop_point_ref,
            arrival_time=arrival_pt.arrival_time,
            route=service_journey.line_ref,
            trip=service_journey.id,
            operator=service_journey.operator_ref
        )

        yield connection
```

#### 3.3.2 URI Strategy (RFC 6570)

**URI Templates** (configurable):

```json
{
  "baseUri": "http://transport.example.org",
  "stopPlace": "{baseUri}/stops/{stopPlaceId}",
  "quay": "{baseUri}/stops/{stopPlaceId}/quays/{quayId}",
  "line": "{baseUri}/lines/{lineId}",
  "serviceJourney": "{baseUri}/journeys/{serviceJourneyId}",
  "connection": "{baseUri}/connections/{departureTime(yyyyMMdd)}/{serviceJourneyId}/{sequence}"
}
```

**Example URIs**:
- Stop: `http://transport.example.org/stops/NSR:StopPlace:123`
- Journey: `http://transport.example.org/journeys/RUT:ServiceJourney:456`
- Connection: `http://transport.example.org/connections/20260205/RUT:ServiceJourney:456/3`

#### 3.3.3 RDF Output (JSON-LD)

```json
{
  "@context": {
    "lc": "http://semweb.mmlab.be/ns/linkedconnections#",
    "netex": "http://data.europa.eu/949/",
    "gtfs": "http://vocab.gtfs.org/terms#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#"
  },
  "@graph": [
    {
      "@id": "http://transport.example.org/connections/20260205/RUT:ServiceJourney:456/3",
      "@type": "lc:Connection",
      "lc:departureStop": {
        "@id": "http://transport.example.org/stops/NSR:StopPlace:123",
        "@type": "netex:StopPlace_VersionStructure",
        "netex:Name": "Oslo Central Station",
        "geo:lat": 59.9127,
        "geo:long": 10.7501
      },
      "lc:departureTime": {
        "@value": "2026-02-05T08:30:00+01:00",
        "@type": "xsd:dateTime"
      },
      "lc:arrivalStop": {
        "@id": "http://transport.example.org/stops/NSR:StopPlace:456",
        "@type": "netex:StopPlace_VersionStructure",
        "netex:Name": "Nationaltheatret",
        "geo:lat": 59.9143,
        "geo:long": 10.7347
      },
      "lc:arrivalTime": {
        "@value": "2026-02-05T08:33:00+01:00",
        "@type": "xsd:dateTime"
      },
      "netex:serviceJourney": {
        "@id": "http://transport.example.org/journeys/RUT:ServiceJourney:456",
        "@type": "netex:ServiceJourney_VersionStructure",
        "netex:PrivateCode": "Line1-Morning-01"
      },
      "netex:line": {
        "@id": "http://transport.example.org/lines/RUT:Line:1",
        "@type": "netex:Line_VersionStructure",
        "netex:PublicCode": "1",
        "netex:Name": "Frognerseteren - Bergkrystallen"
      },
      "netex:operator": {
        "@id": "http://transport.example.org/operators/RUT:Operator:210",
        "netex:Name": "Ruter AS"
      },
      "gtfs:headsign": "Bergkrystallen"
    }
  ]
}
```

### 3.4 Advanced Features

#### 3.4.1 Multi-modal Support
NeTEx supports multiple transport modes natively:
- Bus, Tram, Metro, Rail, Ferry, Air, etc.
- Map to `netex:TransportMode` in RDF
- Enable multi-modal routing queries

#### 3.4.2 Fare Integration
NeTEx includes comprehensive fare data:
- Extract fare zones from `FareFrame`
- Link connections to applicable fares
- Enable cost-based route planning

#### 3.4.3 Accessibility Information
NeTEx provides rich accessibility data:
- Wheelchair accessibility per journey/stop
- Step-free access information
- Audio/visual aids availability
- Map to schema.org accessibility properties

---

## 4. SIRI2LC: Real-time Data Converter

### 4.1 Purpose

Convert SIRI XML real-time feeds into Linked Connections that update or augment static schedule data from NeTEx.

### 4.2 Input Format: SIRI Profiles

SIRI supports 8 service profiles. Focus on three for Linked Connections:

#### 4.2.1 SIRI-VM (Vehicle Monitoring)
Provides real-time vehicle positions:

```xml
<Siri version="2.0">
  <ServiceDelivery>
    <VehicleMonitoringDelivery>
      <VehicleActivity>
        <RecordedAtTime>2026-02-05T14:30:00Z</RecordedAtTime>
        <MonitoredVehicleJourney>
          <LineRef>RUT:Line:1</LineRef>
          <VehicleRef>Vehicle_1001</VehicleRef>
          <VehicleLocation>
            <Longitude>10.7501</Longitude>
            <Latitude>59.9127</Latitude>
          </VehicleLocation>
          <MonitoredCall>
            <StopPointRef>NSR:Quay:789</StopPointRef>
            <AimedArrivalTime>2026-02-05T08:45:00Z</AimedArrivalTime>
            <ExpectedArrivalTime>2026-02-05T08:47:00Z</ExpectedArrivalTime>
            <ArrivalStatus>delayed</ArrivalStatus>
          </MonitoredCall>
        </MonitoredVehicleJourney>
      </VehicleActivity>
    </VehicleMonitoringDelivery>
  </ServiceDelivery>
</Siri>
```

#### 4.2.2 SIRI-ET (Estimated Timetable)
Provides journey-wide predictions:

```xml
<EstimatedTimetableDelivery>
  <EstimatedJourneyVersionFrame>
    <EstimatedVehicleJourney>
      <LineRef>RUT:Line:1</LineRef>
      <DatedVehicleJourneyRef>RUT:ServiceJourney:456</DatedVehicleJourneyRef>
      <EstimatedCalls>
        <EstimatedCall>
          <StopPointRef>NSR:Quay:123</StopPointRef>
          <AimedArrivalTime>08:30:00</AimedArrivalTime>
          <ExpectedArrivalTime>08:32:00</ExpectedArrivalTime>
          <ArrivalStatus>delayed</ArrivalStatus>
        </EstimatedCall>
        <!-- More calls... -->
      </EstimatedCalls>
    </EstimatedVehicleJourney>
  </EstimatedJourneyVersionFrame>
</EstimatedTimetableDelivery>
```

#### 4.2.3 SIRI-SX (Situation Exchange)
Service alerts and disruptions:

```xml
<SituationExchangeDelivery>
  <Situations>
    <PtSituationElement>
      <SituationNumber>ALERT-2026-001</SituationNumber>
      <Summary>Line 1 Delays Due to Signal Failure</Summary>
      <Description>Expect 10-15 minute delays on Line 1</Description>
      <Affects>
        <Networks>
          <AffectedNetwork>
            <AffectedLine>
              <LineRef>RUT:Line:1</LineRef>
            </AffectedLine>
          </AffectedNetwork>
        </Networks>
      </Affects>
    </PtSituationElement>
  </Situations>
</SituationExchangeDelivery>
```

### 4.3 Transformation Logic

#### 4.3.1 Real-time Connection Updates (SIRI-ET)

```python
def siri_et_to_linked_connections(estimated_timetable, static_netex):
    """
    Convert SIRI-ET to updated Linked Connections
    """
    for estimated_journey in estimated_timetable.estimated_journeys:
        # Find corresponding static ServiceJourney from NeTEx
        static_journey = static_netex.find_service_journey(
            estimated_journey.dated_vehicle_journey_ref
        )

        estimated_calls = estimated_journey.estimated_calls

        for i in range(len(estimated_calls) - 1):
            departure_call = estimated_calls[i]
            arrival_call = estimated_calls[i + 1]

            # Calculate delays
            departure_delay = calculate_delay(
                departure_call.aimed_departure_time,
                departure_call.expected_departure_time
            )
            arrival_delay = calculate_delay(
                arrival_call.aimed_arrival_time,
                arrival_call.expected_arrival_time
            )

            # Generate updated connection
            connection = LinkedConnection(
                id=generate_connection_uri(static_journey, i),
                departure_stop=departure_call.stop_point_ref,
                departure_time=departure_call.expected_departure_time,
                arrival_stop=arrival_call.stop_point_ref,
                arrival_time=arrival_call.expected_arrival_time,
                departure_delay=departure_delay,
                arrival_delay=arrival_delay,
                route=estimated_journey.line_ref,
                trip=estimated_journey.dated_vehicle_journey_ref,
                status=departure_call.departure_status  # onTime, delayed, cancelled
            )

            yield connection
```

#### 4.3.2 Vehicle Position Enrichment (SIRI-VM)

```python
def enrich_with_vehicle_positions(connections, vehicle_monitoring):
    """
    Add real-time vehicle position to connections
    """
    for connection in connections:
        # Find matching vehicle
        vehicle_activity = vehicle_monitoring.find_by_journey(
            connection.trip
        )

        if vehicle_activity:
            connection.vehicle = {
                "id": vehicle_activity.vehicle_ref,
                "location": {
                    "latitude": vehicle_activity.latitude,
                    "longitude": vehicle_activity.longitude
                },
                "bearing": vehicle_activity.bearing,
                "occupancy": vehicle_activity.occupancy_status
            }

        yield connection
```

### 4.4 RDF Output (JSON-LD with Real-time Data)

```json
{
  "@context": {
    "lc": "http://semweb.mmlab.be/ns/linkedconnections#",
    "netex": "http://data.europa.eu/949/",
    "siri": "http://www.siri.org.uk/siri#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@id": "http://transport.example.org/connections/20260205/RUT:ServiceJourney:456/3",
  "@type": "lc:Connection",
  "lc:departureStop": {
    "@id": "http://transport.example.org/stops/NSR:StopPlace:123"
  },
  "lc:departureTime": {
    "@value": "2026-02-05T08:32:00+01:00",
    "@type": "xsd:dateTime"
  },
  "lc:departureDelay": {
    "@value": "120",
    "@type": "xsd:integer",
    "@comment": "Delay in seconds"
  },
  "siri:departureStatus": "delayed",
  "lc:arrivalStop": {
    "@id": "http://transport.example.org/stops/NSR:StopPlace:456"
  },
  "lc:arrivalTime": {
    "@value": "2026-02-05T08:35:00+01:00",
    "@type": "xsd:dateTime"
  },
  "lc:arrivalDelay": {
    "@value": "120",
    "@type": "xsd:integer"
  },
  "siri:arrivalStatus": "delayed",
  "netex:serviceJourney": {
    "@id": "http://transport.example.org/journeys/RUT:ServiceJourney:456"
  },
  "siri:vehicle": {
    "@id": "http://transport.example.org/vehicles/1001",
    "siri:currentLocation": {
      "geo:lat": 59.9135,
      "geo:long": 10.7424
    },
    "siri:bearing": 45.0,
    "siri:occupancy": "seatsAvailable",
    "siri:recordedAtTime": "2026-02-05T08:31:30+01:00"
  }
}
```

---

## 5. Technical Specifications

### 5.1 Package Structure

```
netex2lc/
├── README.md
├── setup.py
├── requirements.txt
├── netex2lc/
│   ├── __init__.py
│   ├── cli.py                    # Command-line interface
│   ├── parsers/
│   │   ├── netex_parser.py      # NeTEx XML parser
│   │   ├── siri_parser.py       # SIRI XML parser
│   │   └── validators.py        # SHACL/XSD validation
│   ├── transformers/
│   │   ├── netex_to_rdf.py      # NeTEx → RDF (data.europa.eu/949)
│   │   ├── rdf_to_lc.py         # RDF → Linked Connections
│   │   └── siri_to_lc.py        # SIRI → Linked Connections
│   ├── models/
│   │   ├── linked_connection.py  # LinkedConnection data model
│   │   ├── uri_strategy.py       # RFC 6570 URI templates
│   │   └── ontology_mapper.py    # NeTEx ontology mapping
│   ├── serializers/
│   │   ├── jsonld.py             # JSON-LD output
│   │   ├── turtle.py             # Turtle output
│   │   ├── ntriples.py           # N-Triples output
│   │   └── json.py               # Plain JSON output
│   └── utils/
│       ├── time_utils.py
│       ├── geo_utils.py
│       └── cache.py
├── siri2lc/
│   ├── __init__.py
│   ├── cli.py
│   ├── siri_vm_converter.py     # Vehicle Monitoring
│   ├── siri_et_converter.py     # Estimated Timetable
│   ├── siri_sx_converter.py     # Situation Exchange
│   └── realtime_updater.py      # Continuous update daemon
├── tests/
│   ├── test_netex_parser.py
│   ├── test_siri_parser.py
│   ├── test_transformers.py
│   └── fixtures/
│       ├── sample_netex.xml
│       └── sample_siri.xml
├── examples/
│   ├── uri_templates.json
│   ├── config.yaml
│   └── docker-compose.yml
└── ontologies/
    ├── netex_ontology.ttl       # Reference to data.europa.eu/949
    ├── siri_ontology.ttl        # SIRI RDF ontology (to be created)
    └── linked_connections.ttl   # LC ontology
```

### 5.2 Configuration File (config.yaml)

```yaml
# netex2lc configuration

input:
  netex:
    files:
      - /data/netex/stops.xml
      - /data/netex/lines.xml
      - /data/netex/timetables.xml
    validate: true
    xsd_path: /schemas/netex_publication.xsd

  siri:
    endpoints:
      vehicle_monitoring: https://api.example.org/siri/vm
      estimated_timetable: https://api.example.org/siri/et
      situation_exchange: https://api.example.org/siri/sx
    poll_interval: 30  # seconds
    api_key: ${SIRI_API_KEY}

output:
  format: jsonld  # jsonld | turtle | ntriples | json
  destination: /data/output/connections/
  page_size: 100  # connections per page
  fragment_by: time  # time | route | operator

uris:
  base_uri: http://transport.example.org
  templates:
    stop_place: "{base_uri}/stops/{stopPlaceId}"
    quay: "{base_uri}/stops/{stopPlaceId}/quays/{quayId}"
    line: "{base_uri}/lines/{lineId}"
    service_journey: "{base_uri}/journeys/{serviceJourneyId}"
    connection: "{base_uri}/connections/{departureTime(yyyyMMdd)}/{serviceJourneyId}/{sequence}"
    operator: "{base_uri}/operators/{operatorId}"

ontology:
  netex_namespace: http://data.europa.eu/949/
  netex_owl: /path/to/rdf-netex/owl_netex.ttl
  netex_shacl: /path/to/rdf-netex/shacl_netex.ttl
  use_transmodel: true
  transmodel_namespace: https://w3id.org/transmodel/terms#

publishing:
  server:
    enabled: true
    host: 0.0.0.0
    port: 8080
  routable_tiles:
    enabled: true
    tile_duration: PT1H  # 1 hour per tile
  cache:
    enabled: true
    ttl: 3600  # seconds

logging:
  level: INFO
  file: /var/log/netex2lc.log
```

### 5.3 Command-Line Interface

#### NeTEx2LC

```bash
# Basic usage
netex2lc --input netex_files/ --output connections.jsonld

# With configuration
netex2lc --config config.yaml

# Specify output format
netex2lc --input netex.xml --format turtle --output connections.ttl

# With URI templates
netex2lc --input netex.xml --uris uri_templates.json --format jsonld

# Validate against SHACL
netex2lc --input netex.xml --validate --shacl rdf-netex/shacl_netex.ttl

# Start server mode
netex2lc --config config.yaml --serve --port 8080

# Generate fragmented output (routable tiles)
netex2lc --input netex.xml --fragment-by time --fragment-size PT1H
```

#### SIRI2LC

```bash
# Convert SIRI-ET feed
siri2lc --type et \
        --siri-feed https://api.example.org/siri/et \
        --netex-reference static_netex.xml \
        --output realtime.jsonld

# Convert SIRI-VM feed
siri2lc --type vm \
        --siri-feed https://api.example.org/siri/vm \
        --format jsonld

# Continuous update mode (daemon)
siri2lc --config config.yaml --daemon --interval 30

# With API key authentication
siri2lc --siri-feed https://api.example.org/siri/et \
        --header "Authorization: Bearer ${API_KEY}" \
        --output realtime.jsonld

# Combine multiple SIRI profiles
siri2lc --siri-et https://api.example.org/siri/et \
        --siri-vm https://api.example.org/siri/vm \
        --siri-sx https://api.example.org/siri/sx \
        --merge --output combined.jsonld
```

### 5.4 Programmatic API (Python)

```python
from netex2lc import NeTExConverter
from siri2lc import SIRIConverter
from netex2lc.models import URIStrategy

# Configure URI templates
uri_strategy = URIStrategy.from_file('uri_templates.json')

# Convert NeTEx to Linked Connections
netex_converter = NeTExConverter(
    netex_files=['stops.xml', 'lines.xml', 'timetables.xml'],
    ontology_path='rdf-netex/owl_netex.ttl',
    uri_strategy=uri_strategy,
    output_format='jsonld'
)

# Generate connections (streaming)
for connection in netex_converter.convert():
    print(connection.to_jsonld())

# Or serialize all at once
netex_converter.convert_to_file('connections.jsonld')

# Real-time updates with SIRI
siri_converter = SIRIConverter(
    siri_et_endpoint='https://api.example.org/siri/et',
    netex_reference=netex_converter,  # Use static data as reference
    uri_strategy=uri_strategy
)

# Continuous updates
for updated_connection in siri_converter.stream_updates(interval=30):
    print(updated_connection.to_jsonld())
```

---

## 6. Implementation Plan

### 6.1 Phase 1: Core NeTEx2LC (Months 1-3)

**Objectives**:
- ✅ Parse NeTEx XML files (SiteFrame, ServiceFrame, TimetableFrame)
- ✅ Map to data.europa.eu/949 RDF ontology
- ✅ Generate Linked Connections from ServiceJourneys
- ✅ Implement URI strategy (RFC 6570)
- ✅ Support JSON-LD and Turtle output

**Deliverables**:
- `netex2lc` Python package (v0.1.0)
- CLI tool for batch conversion
- Documentation and examples
- Test suite with sample NeTEx data

**Milestones**:
- Week 4: NeTEx parser complete
- Week 8: RDF transformation working
- Week 12: First release with documentation

### 6.2 Phase 2: SIRI2LC Integration (Months 4-6)

**Objectives**:
- ✅ Parse SIRI XML (VM, ET, SX profiles)
- ✅ Real-time connection updates
- ✅ Vehicle position integration
- ✅ Service alert handling
- ✅ Streaming/daemon mode

**Deliverables**:
- `siri2lc` Python package (v0.1.0)
- Real-time update daemon
- Integration with netex2lc
- API documentation

**Milestones**:
- Week 16: SIRI-ET converter complete
- Week 20: SIRI-VM integration
- Week 24: Daemon mode and production testing

### 6.3 Phase 3: Publishing & Optimization (Months 7-9)

**Objectives**:
- ✅ HTTP server for Linked Connections
- ✅ Routable tiles implementation
- ✅ Linked Data Fragments server
- ✅ SPARQL endpoint setup
- ✅ Performance optimization
- ✅ CDN integration

**Deliverables**:
- HTTP server component
- Docker containerization
- Kubernetes deployment configs
- Performance benchmarks
- Production deployment guide

**Milestones**:
- Week 28: HTTP server operational
- Week 32: Routable tiles working
- Week 36: Production-ready release (v1.0.0)

### 6.4 Phase 4: Advanced Features (Months 10-12)

**Objectives**:
- ✅ Multi-modal journey planning
- ✅ Fare integration
- ✅ Accessibility routing
- ✅ European NAP federation
- ✅ SPARQL federated queries

**Deliverables**:
- Client-side route planner (JavaScript)
- Federated query examples
- Multi-modal routing demos
- Research paper publication

**Milestones**:
- Week 40: Fare integration
- Week 44: Accessibility features
- Week 48: NAP federation proof-of-concept

---

## 7. Usage Examples

### 7.1 Complete Workflow Example

#### Step 1: Convert NeTEx to Linked Connections

```bash
# Download NeTEx files from Norwegian NAP
wget https://data.norge.no/netex/stops.xml
wget https://data.norge.no/netex/lines.xml
wget https://data.norge.no/netex/timetables.xml

# Convert to Linked Connections
netex2lc \
  --input stops.xml lines.xml timetables.xml \
  --ontology rdf-netex/owl_netex.ttl \
  --uris uri_templates.json \
  --format jsonld \
  --output /data/lc/static/ \
  --fragment-by time \
  --fragment-size PT1H
```

**Output**: Time-based fragments
```
/data/lc/static/
├── connections-20260205-00.jsonld  # 00:00-01:00
├── connections-20260205-01.jsonld  # 01:00-02:00
├── connections-20260205-02.jsonld
...
├── connections-20260205-23.jsonld
└── index.jsonld  # Hydra collection index
```

#### Step 2: Start Real-time Updates with SIRI

```bash
# Start SIRI2LC daemon
siri2lc \
  --config config.yaml \
  --siri-et https://api.ruter.no/siri/et \
  --siri-vm https://api.ruter.no/siri/vm \
  --netex-reference /data/lc/static/ \
  --output /data/lc/realtime/ \
  --daemon \
  --interval 30
```

#### Step 3: Serve Linked Connections

```bash
# Start HTTP server
netex2lc serve \
  --static /data/lc/static/ \
  --realtime /data/lc/realtime/ \
  --port 8080 \
  --enable-cors
```

#### Step 4: Query with Client-side Router

```javascript
// JavaScript client
import { ConnectionsFetcher, CSA } from 'netex-lc-client';

const fetcher = new ConnectionsFetcher({
  baseUrl: 'http://localhost:8080/connections/'
});

const router = new CSA(fetcher);

const journey = await router.plan({
  from: 'http://transport.example.org/stops/NSR:StopPlace:123',
  to: 'http://transport.example.org/stops/NSR:StopPlace:789',
  departureTime: new Date('2026-02-05T08:00:00Z')
});

console.log(journey.connections);
```

### 7.2 SPARQL Query Examples

#### Query 1: Find all delayed connections

```sparql
PREFIX lc: <http://semweb.mmlab.be/ns/linkedconnections#>
PREFIX siri: <http://www.siri.org.uk/siri#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?connection ?departureStop ?arrivalStop ?delay ?status
WHERE {
  ?connection a lc:Connection ;
              lc:departureStop ?departureStop ;
              lc:arrivalStop ?arrivalStop ;
              lc:departureDelay ?delay ;
              siri:departureStatus ?status .

  FILTER(?delay > 120)  # More than 2 minutes delay
  FILTER(?status = "delayed")
}
ORDER BY DESC(?delay)
```

#### Query 2: Multi-modal journey with transfers

```sparql
PREFIX lc: <http://semweb.mmlab.be/ns/linkedconnections#>
PREFIX netex: <http://data.europa.eu/949/>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT ?c1 ?c2 ?transferStop ?transferTime
WHERE {
  # First connection (metro)
  ?c1 a lc:Connection ;
      lc:arrivalStop ?transferStop ;
      lc:arrivalTime ?arrival1 ;
      netex:transportMode "metro" .

  # Second connection (bus)
  ?c2 a lc:Connection ;
      lc:departureStop ?transferStop ;
      lc:departureTime ?departure2 ;
      netex:transportMode "bus" .

  # Transfer time between 5-15 minutes
  BIND(?departure2 - ?arrival1 AS ?transferTime)
  FILTER(?transferTime >= "PT5M"^^xsd:duration)
  FILTER(?transferTime <= "PT15M"^^xsd:duration)
}
```

#### Query 3: Accessible connections

```sparql
PREFIX lc: <http://semweb.mmlab.be/ns/linkedconnections#>
PREFIX netex: <http://data.europa.eu/949/>
PREFIX schema: <http://schema.org/>

SELECT ?connection ?journey ?accessibility
WHERE {
  ?connection a lc:Connection ;
              netex:serviceJourney ?journey .

  ?journey netex:accessibilityAssessment ?accessibility ;
           netex:wheelchairAccessible true ;
           netex:stepFreeAccess true .
}
```

---

## 8. Comparison with GTFS-LC

### 8.1 Feature Comparison

| Feature | GTFS2LC | NeTEx2LC | Advantage |
|---------|---------|----------|-----------|
| **Data Source** | GTFS CSV | NeTEx XML | NeTEx more comprehensive |
| **Ontology** | Linked GTFS | data.europa.eu/949 | Official EU ontology |
| **Complexity** | Simple | Complex | GTFS simpler, NeTEx richer |
| **Fare Data** | Limited | Comprehensive | NeTEx advantage |
| **Accessibility** | Basic | Detailed | NeTEx advantage |
| **Multi-modal** | Yes | Yes (native) | NeTEx better integrated |
| **Real-time** | GTFS-RT (protobuf) | SIRI (XML) | GTFS-RT more compact |
| **Adoption** | Global | Europe-focused | GTFS wider adoption |
| **EU Compliance** | No | Yes (mandated) | NeTEx required for NAPs |
| **Tool Maturity** | Mature (gtfs2lc) | New (proposed) | GTFS-LC battle-tested |

### 8.2 Data Model Mapping

| GTFS Concept | NeTEx Concept | Linked Connection Property |
|--------------|---------------|---------------------------|
| stop | StopPlace/Quay | lc:departureStop, lc:arrivalStop |
| route | Line | netex:line |
| trip | ServiceJourney | netex:serviceJourney |
| stop_time | TimetabledPassingTime | lc:departureTime, lc:arrivalTime |
| agency | Operator | netex:operator |
| calendar | DayType, OperatingPeriod | netex:validityCondition |
| fare_attributes | FareProduct | netex:fareProduct |
| transfer | Interchange | netex:interchange |

### 8.3 Performance Comparison (Estimated)

**Test Dataset**: Medium-sized transit network (1000 stops, 50 routes)

| Metric | GTFS2LC | NeTEx2LC (Estimated) |
|--------|---------|----------------------|
| Parse time | 2.5 sec | 8-12 sec (XML parsing) |
| Transform time | 1.2 sec | 3-5 sec (RDF mapping) |
| Output size (JSON-LD) | 12 MB | 18-25 MB (richer data) |
| Memory usage | 150 MB | 300-400 MB |
| Connections generated | 50,000 | 50,000 |

**Optimization Strategy**:
- Streaming XML parsing (lxml iterparse)
- Lazy RDF graph construction
- Incremental serialization
- Optional compression (gzip)

---

## 9. Integration with Existing Tools

### 9.1 Triple Store Integration

**Apache Jena Fuseki**:
```bash
# Load NeTEx-LC data
curl -X POST \
  -H "Content-Type: application/ld+json" \
  --data-binary @connections.jsonld \
  http://localhost:3030/transit/data

# Query via SPARQL
curl -X POST \
  -H "Content-Type: application/sparql-query" \
  --data "SELECT * WHERE { ?s ?p ?o } LIMIT 10" \
  http://localhost:3030/transit/sparql
```

**Virtuoso**:
```sql
-- Load into Virtuoso
DB.DBA.RDF_LOAD_RDFXML_MT(
  file_to_string_output('/data/connections.ttl'),
  '',
  'http://transport.example.org/graph/connections'
);

-- Query
SPARQL
SELECT *
FROM <http://transport.example.org/graph/connections>
WHERE { ?s ?p ?o }
LIMIT 10;
```

### 9.2 Linked Data Fragments Server

```bash
# Install LDF Server
npm install -g @ldfserver/server

# Configure data source
cat > config.json <<EOF
{
  "@context": "https://linkedsoftwaredependencies.org/bundles/npm/@ldfserver/server/^3.0.0/components/context.jsonld",
  "@id": "urn:ldf-server:my",
  "import": "preset-qpf:config-defaults.json",
  "datasources": [{
    "@id": "urn:ldf-server:myDatasource",
    "@type": "SparqlDatasource",
    "datasourceTitle": "NeTEx Linked Connections",
    "url": "http://localhost:3030/transit/sparql"
  }]
}
EOF

# Start server
ldf-server config.json 5000
```

### 9.3 OpenTripPlanner Integration

**Future Work**: Extend OTP to consume Linked Connections
- Create OTP graph builder for LC format
- Enable federated routing across LC endpoints
- Combine with existing GTFS support

---

## 10. Roadmap and Milestones

### 10.1 Short-term (Q1-Q2 2026)

- ✅ **M1**: NeTEx parser and validator (Jan-Feb)
- ✅ **M2**: RDF transformation engine (Feb-Mar)
- ✅ **M3**: Linked Connections generator (Mar-Apr)
- ✅ **M4**: First alpha release (Apr)
- ✅ **M5**: SIRI-ET real-time converter (May-Jun)
- ✅ **M6**: Beta release with documentation (Jun)

### 10.2 Medium-term (Q3-Q4 2026)

- 🔄 **M7**: Production deployment (Jul)
- 🔄 **M8**: HTTP server and routable tiles (Aug)
- 🔄 **M9**: SIRI-VM vehicle tracking (Sep)
- 🔄 **M10**: Performance optimization (Oct)
- 🔄 **M11**: European NAP pilot (Nov)
- 🔄 **M12**: v1.0.0 stable release (Dec)

### 10.3 Long-term (2027+)

- 🎯 Multi-modal routing client library
- 🎯 Federated SPARQL across EU NAPs
- 🎯 Real-time delay prediction (ML)
- 🎯 Accessibility-aware routing
- 🎯 Integration with MaaS platforms
- 🎯 W3C standardization proposal

---

## 11. Open Source Strategy

### 11.1 Licensing

**Recommended**: MIT License or Apache 2.0
- Maximum adoption and contribution
- Compatible with commercial use
- Aligns with GTFS-LC ecosystem

### 11.2 Repository Structure

```
GitHub Organization: netex-linked-connections

Repositories:
├── netex2lc           # Main converter library
├── siri2lc            # Real-time SIRI converter
├── netex-lc-server    # HTTP server for LC
├── netex-lc-client    # JavaScript client library
├── netex-lc-spec      # Specification documents
└── netex-lc-examples  # Example datasets and configs
```

### 11.3 Community Engagement

- **Documentation**: Comprehensive guides on GitBook/ReadTheDocs
- **Examples**: Real-world datasets from European operators
- **Workshops**: Present at FOSS4G, SemanticWeb conferences
- **Collaboration**: Partner with Ruter, SNCF, Transport for London
- **Standards**: Contribute to NeTEx/SIRI working groups

---

## 12. Conclusion

### 12.1 Summary

This proposal outlines a comprehensive solution for converting European transit data standards (NeTEx and SIRI) into Linked Connections, enabling:

1. **Semantic Interoperability**: RDF-based data using official EU ontologies
2. **Client-side Routing**: Scalable, distributed journey planning
3. **Real-time Updates**: SIRI integration for live data
4. **EU Compliance**: Alignment with Regulation 2017/1926
5. **Open Standards**: W3C Linked Data principles

### 12.2 Key Innovations

- **Leverage Existing NeTEx RDF Ontology**: Use data.europa.eu/949 directly
- **Unified European Transit Graph**: Enable federated queries across NAPs
- **Multi-modal by Default**: NeTEx native support for all transport modes
- **Rich Metadata**: Accessibility, fares, real-time, all in RDF

### 12.3 Next Steps

1. **Secure Funding**: Research grants (EU Horizon), transit agency sponsorship
2. **Form Consortium**: Collaborate with universities, operators, tech companies
3. **Pilot Project**: Implement for one NAP (e.g., Norway, France)
4. **Community Building**: Open-source release, documentation, workshops
5. **Standardization**: Submit to W3C, CEN, EU working groups

### 12.4 Call to Action

**We invite collaboration from**:
- Transit operators and authorities
- European NAP maintainers
- Semantic web researchers
- Open-source developers
- Journey planning service providers

**Contact**: [Your Organization/Email]
**Repository**: https://github.com/netex-linked-connections/netex2lc (to be created)

---

## Appendices

### Appendix A: NeTEx to Linked Connections Mapping Table

| NeTEx Element | XPath | NeTEx RDF Class | Linked Connection Property |
|--------------|-------|-----------------|---------------------------|
| StopPlace | //StopPlace | netex:StopPlace_VersionStructure | lc:departureStop, lc:arrivalStop |
| Quay | //Quay | netex:Quay_VersionStructure | lc:departureStop, lc:arrivalStop |
| Line | //Line | netex:Line_VersionStructure | netex:line |
| ServiceJourney | //ServiceJourney | netex:ServiceJourney_VersionStructure | netex:serviceJourney |
| TimetabledPassingTime | //TimetabledPassingTime | netex:TimetabledPassingTime_VersionedChildStructure | lc:departureTime, lc:arrivalTime |
| DepartureTime | //DepartureTime | xsd:dateTime | lc:departureTime |
| ArrivalTime | //ArrivalTime | xsd:dateTime | lc:arrivalTime |
| Operator | //Operator | netex:Operator_VersionStructure | netex:operator |

### Appendix B: SIRI to Linked Connections Mapping Table

| SIRI Element | SIRI Profile | SIRI RDF Property (proposed) | Linked Connection Property |
|--------------|--------------|------------------------------|---------------------------|
| VehicleActivity | SIRI-VM | siri:vehicleActivity | siri:vehicle |
| VehicleLocation | SIRI-VM | siri:vehicleLocation | siri:currentLocation |
| MonitoredCall | SIRI-VM | siri:monitoredCall | lc:departureStop, lc:arrivalStop |
| EstimatedCall | SIRI-ET | siri:estimatedCall | lc:departureTime, lc:arrivalTime |
| ExpectedArrivalTime | SIRI-ET | siri:expectedArrivalTime | lc:arrivalTime |
| ExpectedDepartureTime | SIRI-ET | siri:expectedDepartureTime | lc:departureTime |
| ArrivalStatus | SIRI-ET | siri:arrivalStatus | siri:arrivalStatus |
| DepartureDelay | SIRI-ET | siri:departureDelay | lc:departureDelay |
| PtSituationElement | SIRI-SX | siri:ptSituationElement | siri:alert |

### Appendix C: Sample URI Templates (RFC 6570)

```json
{
  "baseUri": "http://transport.example.org",
  "stopPlace": "{baseUri}/stops/{stopPlaceId}",
  "quay": "{baseUri}/stops/{stopPlaceId}/quays/{quayId}",
  "line": "{baseUri}/lines/{lineId}",
  "route": "{baseUri}/routes/{routeId}",
  "serviceJourney": "{baseUri}/journeys/{operatorId}:{serviceJourneyId}",
  "datedServiceJourney": "{baseUri}/journeys/{operatorId}:{serviceJourneyId}/{operatingDay}",
  "connection": "{baseUri}/connections/{departureTime(yyyyMMddHHmm)}/{serviceJourneyId}/{sequence}",
  "operator": "{baseUri}/operators/{operatorId}",
  "authority": "{baseUri}/authorities/{authorityId}",
  "vehicle": "{baseUri}/vehicles/{vehicleId}",
  "alert": "{baseUri}/alerts/{alertId}"
}
```

### Appendix D: References

1. **NeTEx Standard**: CEN TS 16614 series
2. **SIRI Standard**: CEN TS 15531 series
3. **EU Regulation 2017/1926**: Delegated Regulation on provision of EU-wide multimodal travel information services
4. **Linked Connections Specification**: https://linkedconnections.org/specification/1-0
5. **NeTEx RDF Ontology**: http://data.europa.eu/949/
6. **Transmodel Ontology**: https://w3id.org/transmodel/terms#
7. **GTFS2LC**: https://github.com/linkedconnections/gtfs2lc
8. **RFC 6570**: URI Template specification

---

**Document Version**: 1.0
**Date**: February 5, 2026
**Authors**: Transit Data Working Group
**License**: CC BY 4.0

---

**End of Proposal**
