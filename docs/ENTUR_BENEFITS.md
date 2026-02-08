# Benefits for Entur Profile Developers

This document outlines the advantages of using `netex2lc` and `siri2lc` tools for developers working with the [Entur NeTEx and SIRI profiles](https://github.com/entur/profile-examples).

## Executive Summary

The `netex2lc` and `siri2lc` tools provide Entur profile developers with a pathway to publish transit data as **Linked Data**, enabling interoperability with the European semantic web ecosystem while maintaining compatibility with the Nordic NeTEx Profile.

---

## 1. Linked Data Publishing

### From Proprietary XML to Open Web Standards

| Current State | With netex2lc/siri2lc |
|---------------|----------------------|
| NeTEx XML files | JSON-LD, Turtle, N-Triples |
| Closed ecosystem | Web-scale interoperability |
| Point-to-point integration | Federated queries (SPARQL) |

Entur data becomes queryable alongside EU-wide transit data via the [EU Access Node](http://data.europa.eu/949/) and other National Access Points (NAPs).

### Example Transformation

```bash
# Convert NeTEx to Linked Connections
netex2lc oslo_bus_timetable.xml -o connections.jsonld

# Convert SIRI real-time to Linked Connections
siri2lc siri-et-response.xml -o realtime.jsonld
```

---

## 2. Alignment with EU Regulations

### MMTIS Delegated Regulation (EU) 2017/1926

The regulation requires Member States to provide multimodal travel information. Linked Connections format:

- Satisfies **machine-readable** requirements
- Enables **cross-border journey planning**
- Supports **real-time updates** (SIRI-ET to LC)

```
Entur NeTEx Profile --> netex2lc --> Linked Connections --> EU NAP
```

### Compliance Pathway

| Requirement | How Tools Help |
|-------------|----------------|
| Static timetables | NeTEx to LC conversion |
| Real-time updates | SIRI-ET to LC with delays |
| Service disruptions | SIRI-SX to alerts |
| Machine-readable | JSON-LD, Turtle output |

---

## 3. Interoperability with European Transit Data

### URI-based Identity

The scripts generate stable, dereferenceable URIs:

```
http://entur.org/stops/NSR:StopPlace:58366
http://entur.org/lines/RUT:Line:1
http://entur.org/journeys/ATB:ServiceJourney:123
```

### Cross-Dataset Linking

Entur stops, lines, and journeys can be linked to:

| External Dataset | Link Type |
|------------------|-----------|
| [EU-Spirit](https://eu-spirit.eu/) | Cross-border services |
| [Wikidata](https://www.wikidata.org/) | Geographic entities |
| [OpenStreetMap](https://www.openstreetmap.org/) | Infrastructure |
| [DBpedia](https://dbpedia.org/) | City/region information |

### Example: Linking to Wikidata

```json
{
  "@id": "http://entur.org/stops/NSR:StopPlace:58366",
  "owl:sameAs": "http://www.wikidata.org/entity/Q2879682"
}
```

---

## 4. Real-time Data Integration

### SIRI Profile Support

| SIRI Profile | Output | Use Case |
|--------------|--------|----------|
| **SIRI-ET** | `lc:Connection` with delays | Journey planning with real-time |
| **SIRI-VM** | Vehicle positions (JSON-LD) | Live tracking, accessibility |
| **SIRI-SX** | Service alerts (JSON-LD) | Disruption management |

### Real-time Journey Planning

Real-time Entur data can feed Linked Connections-compatible journey planners:

- [Planner.js](https://planner.js.org/) - Client-side route planning
- [OpenTripPlanner](https://www.opentripplanner.org/) - With LC extension
- Custom SPARQL-based planners

---

## 5. Benchmark-Driven Quality Assurance

### Validation for Profile Conformance

The benchmark validates that Entur profile data converts correctly:

| Metric | What It Catches |
|--------|-----------------|
| Parse success rate | Malformed XML, missing elements |
| Connection yield | Empty ServiceJourneys, missing PassingTimes |
| URI validity | Broken references, encoding issues |
| Completeness | Missing optional but valuable fields |
| JSON-LD validity | Structural correctness |
| DateTime format | ISO 8601 compliance |

### Running the Benchmark

```bash
# Benchmark Entur profile examples
python benchmarks/benchmark.py --entur-only -o results.json --csv results.csv

# Generate visualization charts
python benchmarks/visualize.py results.csv -o charts/
```

### Continuous Integration

```yaml
# Example GitHub Actions workflow
- name: Validate Entur Profiles
  run: |
    python benchmarks/benchmark.py --entur-only --csv results.csv
    # Fail if success rate < 95%
    python -c "import csv; r=list(csv.DictReader(open('results.csv'))); \
      success=sum(1 for x in r if x['parse_success']=='True')/len(r); \
      exit(0 if success >= 0.95 else 1)"
```

---

## 6. Developer Experience

### Quick Validation of Profile Changes

When updating Entur profile examples:

```bash
# Test a single file
netex2lc my_new_example.xml -o output.jsonld --validate

# Run full benchmark on local files
python benchmarks/benchmark.py --local-only

# Check specific SIRI profile
siri2lc siri-et-example.xml --format turtle -o output.ttl
```

### Visualization of Results

```bash
python benchmarks/visualize.py results.csv -o charts/
```

Generated charts show:
- Success rate by format (NeTEx/SIRI)
- Success rate by SIRI profile (ET/VM/SX)
- Parse time distribution
- Completeness scores
- Memory usage patterns

### Sample Dashboard Output

```
================================================================================
BENCHMARK SUMMARY
================================================================================

Files Processed:
  Total:     16
  NeTEx:     9
  SIRI:      7

Parsing Performance:
  Success Rate:     93.8%
  Avg Parse Time:   45.23 ms
  Avg Memory Peak:  8.45 MB

Output Yield:
  Connections:      124
  Vehicle Positions: 5
  Service Alerts:   3

Data Quality:
  Avg Completeness: 52.3%
  JSON-LD Valid:    100.0%
================================================================================
```

---

## 7. Research and Innovation

### Semantic Web Research

The Linked Connections output enables:

| Research Area | Application |
|---------------|-------------|
| **Federated querying** | Cross-operator journey planning |
| **Knowledge graphs** | Transit + geography + accessibility |
| **Machine learning** | Delay prediction, demand forecasting |
| **Accessibility analysis** | Wheelchair route coverage |

### SPARQL Query Examples

```sparql
# Find all connections departing from Oslo S
PREFIX lc: <http://semweb.mmlab.be/ns/linkedconnections#>
PREFIX netex: <http://data.europa.eu/949/>

SELECT ?connection ?departureTime ?arrivalStop
WHERE {
  ?connection a lc:Connection ;
              lc:departureStop <http://entur.org/stops/NSR:StopPlace:337> ;
              lc:departureTime ?departureTime ;
              lc:arrivalStop ?arrivalStop .
}
ORDER BY ?departureTime
LIMIT 10
```

```sparql
# Find wheelchair-accessible connections
SELECT ?connection ?departureStop ?arrivalStop
WHERE {
  ?connection a lc:Connection ;
              netex:wheelchairAccessible true ;
              lc:departureStop ?departureStop ;
              lc:arrivalStop ?arrivalStop .
}
```

### Compatibility with Standards

| Standard | Status |
|----------|--------|
| [Linked Connections](https://linkedconnections.org/) | Fully supported |
| [GTFS-LD](https://github.com/OpenTransport/linked-gtfs) | Compatible vocabulary |
| [Transmodel](https://www.transmodel-cen.eu/) | Aligned via NeTEx |
| [ERA vocabulary](http://data.europa.eu/949/) | Uses `netex:` namespace |

---

## 8. Concrete Use Cases for Entur

### Use Case 1: Nordic Journey Planning Federation

```
User in Oslo wants to travel to Stockholm:

1. Query Entur LC endpoint for Oslo --> Norwegian border
2. Query Swedish LC endpoint for border --> Stockholm
3. Combine results for complete journey
```

No bilateral API agreements required - just follow the links.

### Use Case 2: Accessibility Routing

Build specialized routing for users with mobility needs:

```sparql
SELECT ?journey ?stops
WHERE {
  ?journey netex:wheelchairAccessible true ;
           lc:departureStop ?from ;
           lc:arrivalStop ?to .
  ?from netex:Name "Oslo S" .
  ?to netex:Name "Bergen" .
}
```

### Use Case 3: Open Data Portal Integration

Linked Connections can be published on:

| Portal | Benefit |
|--------|---------|
| [data.norge.no](https://data.norge.no/) | Norwegian open data |
| [European Data Portal](https://data.europa.eu/) | EU-wide visibility |
| [Zenodo](https://zenodo.org/) | Research datasets |

### Use Case 4: Real-time Disruption Analysis

Combine SIRI-SX alerts with timetable data:

```sparql
# Find connections affected by current alerts
SELECT ?connection ?alert ?summary
WHERE {
  ?alert a siri:PtSituationElement ;
         siri:affectedLines ?line ;
         siri:summary ?summary .
  ?connection netex:line ?line .
}
```

---

## 9. Getting Started

### Installation

```bash
pip install -e ".[dev]"
```

### Quick Start

```bash
# Convert NeTEx to JSON-LD
netex2lc path/to/netex.xml -o connections.jsonld

# Convert SIRI-ET to Turtle
siri2lc path/to/siri-et.xml --format turtle -o connections.ttl

# Run benchmark
python benchmarks/benchmark.py --entur-only --csv results.csv
```

### Configuration

Create `config.yaml` for custom URI patterns:

```yaml
base_uri: "https://data.entur.org"
templates:
  stop_place: "{base_uri}/stops/{stop_id}"
  line: "{base_uri}/lines/{line_id}"
  service_journey: "{base_uri}/journeys/{service_journey_id}"
  connection: "{base_uri}/connections/{departure_date}/{service_journey_id}/{sequence}"
```

---

## 10. Summary

| Benefit | Impact |
|---------|--------|
| **EU compliance** | Meet MMTIS data sharing requirements |
| **Interoperability** | Connect with pan-European transit ecosystem |
| **Quality assurance** | Automated validation of profile examples |
| **Developer productivity** | Fast feedback on profile changes |
| **Innovation enablement** | Open data for research and startups |
| **Future-proofing** | Align with semantic web standards |

The scripts transform Entur's NeTEx/SIRI investment into a **web-scale data asset** without abandoning the existing profile infrastructure.

---

## References

- [Linked Connections Specification](https://linkedconnections.org/specification/1-0)
- [Entur Profile Examples](https://github.com/entur/profile-examples)
- [NeTEx Standard](https://netex-cen.eu/)
- [SIRI Standard](http://www.siri-cen.eu/)
- [EU NAP](https://transport.ec.europa.eu/transport-themes/intelligent-transport-systems/road/action-plan-and-directive/national-access-points_en)
- [ERA Vocabulary](http://data.europa.eu/949/)
