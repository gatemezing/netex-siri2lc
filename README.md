# netex-siri2lc

Convert NeTEx and SIRI XML into Linked Connections RDF (JSON-LD, Turtle, N-Triples).

## Features

- **netex2lc**: Parse NeTEx `ServiceJourney` passing times into `lc:Connection` resources
- **siri2lc**: Parse SIRI feeds into Linked Connections:
  - **SIRI-ET**: Estimated Timetable (real-time connection updates)
  - **SIRI-VM**: Vehicle Monitoring (real-time vehicle positions)
  - **SIRI-SX**: Situation Exchange (service alerts/disruptions)
- Multiple output formats: JSON-LD, Turtle, N-Triples, RDF/XML
- YAML configuration file support
- Input validation and auto-detection of SIRI profiles

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install from source
pip install -e .

# Or install with dev dependencies for testing
pip install -e ".[dev]"
```

## Usage

### NeTEx to Linked Connections

```bash
# Basic usage (JSON-LD output)
python -m netex2lc \
  --input path/to/netex.xml \
  --output connections.jsonld

# Turtle format
python -m netex2lc \
  --input path/to/netex.xml \
  --format turtle \
  --output connections.ttl

# Multiple input files with custom base URI
python -m netex2lc \
  --input stops.xml \
  --input lines.xml \
  --input timetables.xml \
  --base-uri http://myoperator.example.org \
  --output connections.jsonld

# Using configuration file
python -m netex2lc --config config.yaml

# Verbose mode with validation
python -m netex2lc \
  --input netex.xml \
  --verbose \
  --strict \
  --output connections.jsonld
```

### SIRI to Linked Connections

```bash
# SIRI-ET (Estimated Timetable) - auto-detected
python -m siri2lc \
  --input path/to/siri-et.xml \
  --service-date 2026-02-05 \
  --output realtime.jsonld

# Explicit profile type
python -m siri2lc \
  --input path/to/siri.xml \
  --type et \
  --output realtime.jsonld

# SIRI-VM (Vehicle Monitoring)
python -m siri2lc \
  --input path/to/siri-vm.xml \
  --type vm \
  --output vehicles.jsonld

# SIRI-SX (Situation Exchange / Alerts)
python -m siri2lc \
  --input path/to/siri-sx.xml \
  --type sx \
  --output alerts.jsonld

# With configuration file
python -m siri2lc --config config.yaml --input siri.xml
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--input` | Input XML file(s) |
| `--output` | Output file path (`-` for stdout) |
| `--format` | Output format: `jsonld`, `turtle`, `ntriples`, `rdfxml` |
| `--uris` | JSON file with URI templates |
| `--base-uri` | Base URI for generated resources |
| `--config` | YAML configuration file |
| `--verbose`, `-v` | Enable verbose logging |
| `--quiet`, `-q` | Suppress warnings |
| `--strict` | Fail on parsing errors (instead of skipping) |
| `--validate/--no-validate` | Enable/disable input validation |
| `--pretty/--compact` | Pretty-print or compact output |

### Configuration File (YAML)

```yaml
input:
  netex:
    files:
      - /data/netex/stops.xml
      - /data/netex/timetables.xml
    validate: true

  siri:
    endpoints:
      estimated_timetable: https://api.example.org/siri/et
      vehicle_monitoring: https://api.example.org/siri/vm
    poll_interval: 30

output:
  format: jsonld
  destination: /data/output/connections.jsonld
  pretty: true

uris:
  base_uri: http://transport.example.org
  templates:
    stop_place: "{base_uri}/stops/{stop_id}"
    line: "{base_uri}/lines/{line_id}"
    connection: "{base_uri}/connections/{departure_date}/{service_journey_id}/{sequence}"

strict: false
verbose: false
```

### Python API

```python
from netex2lc import parse_netex, URIStrategy, serialize_connections
from siri2lc import parse_siri_et, parse_siri_vm, parse_siri_sx
from datetime import date

# Configure URI templates
uri_strategy = URIStrategy(base_uri="http://myoperator.example.org")

# Parse NeTEx
connections = parse_netex(["stops.xml", "timetables.xml"], uri_strategy)

# Serialize to different formats
serialize_connections(connections, "output.jsonld", format_name="jsonld")
serialize_connections(connections, "output.ttl", format_name="turtle")

# Parse SIRI-ET (real-time updates)
rt_connections = parse_siri_et("siri-et.xml", uri_strategy, date(2026, 2, 5))

# Parse SIRI-VM (vehicle positions)
positions = parse_siri_vm("siri-vm.xml", uri_strategy)
for pos in positions:
    print(f"Vehicle {pos.vehicle_id} at ({pos.latitude}, {pos.longitude})")

# Parse SIRI-SX (service alerts)
alerts = parse_siri_sx("siri-sx.xml", uri_strategy)
for alert in alerts:
    print(f"Alert: {alert.summary}")
```

## Output Formats

### JSON-LD

```json
{
  "@context": {
    "lc": "http://semweb.mmlab.be/ns/linkedconnections#",
    "netex": "http://data.europa.eu/949/",
    "siri": "http://www.siri.org.uk/siri#"
  },
  "@graph": [
    {
      "@id": "http://transport.example.org/connections/20260205/SJ001/1",
      "@type": "lc:Connection",
      "lc:departureStop": {"@id": "http://transport.example.org/stops/SP001"},
      "lc:departureTime": {"@value": "2026-02-05T08:30:00+01:00", "@type": "xsd:dateTime"},
      "lc:arrivalStop": {"@id": "http://transport.example.org/stops/SP002"},
      "lc:arrivalTime": {"@value": "2026-02-05T08:45:00+01:00", "@type": "xsd:dateTime"}
    }
  ]
}
```

### Turtle

```turtle
@prefix lc: <http://semweb.mmlab.be/ns/linkedconnections#> .
@prefix netex: <http://data.europa.eu/949/> .

<http://transport.example.org/connections/20260205/SJ001/1> a lc:Connection ;
    lc:departureStop <http://transport.example.org/stops/SP001> ;
    lc:arrivalStop <http://transport.example.org/stops/SP002> ;
    lc:departureTime "2026-02-05T08:30:00+01:00"^^xsd:dateTime ;
    lc:arrivalTime "2026-02-05T08:45:00+01:00"^^xsd:dateTime .
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=netex2lc --cov=siri2lc

# Verbose
pytest -v
```

## Benchmarking

Run benchmarks against local test data and Entur profile examples:

```bash
# Full benchmark
python benchmarks/benchmark.py -o results.json --csv results.csv

# Local test data only
python benchmarks/benchmark.py --local-only

# Entur examples only
python benchmarks/benchmark.py --entur-only

# Generate visualization charts
python benchmarks/visualize.py results.csv -o charts/
```

See [benchmarks/METRICS.md](benchmarks/METRICS.md) for evaluation criteria.

## Documentation

- [Benefits for Entur Profile Developers](docs/ENTUR_BENEFITS.md) - Why use these tools with Entur profiles
- [Benchmark Metrics](benchmarks/METRICS.md) - Evaluation criteria and methodology
- [Results Template](benchmarks/RESULTS_TEMPLATE.md) - Expected benchmark outputs

## References

- [Linked Connections Specification](https://linkedconnections.org/specification/1-0)
- [ERA NeTEx RDF Ontology](http://data.europa.eu/949/)
- [GTFS2LC](https://github.com/linkedconnections/gtfs2lc)
- [NeTEx Standard](https://netex-cen.eu/)
- [SIRI Standard](http://www.siri-cen.eu/)

## License

MIT

## Profile examples
- https://github.com/entur/profile-examples