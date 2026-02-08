# Benchmark Results

## Test Data Inventory

### Local Test Data (`testdata/`)

| File | Format | Profile | Size |
|------|--------|---------|------|
| Netex_01.1_Bus_SimpleTimetable_JourneysOnly.xml | NeTEx | - | 19.6 KB |
| Netex_01.2_Bus_SimpleTimetable_WithTimings.xml | NeTEx | - | 55.7 KB |
| Netex_09.2_Bus_SimpleTimetable_Slovenia.xml | NeTEx | - | 37.5 KB |
| ext_estimatedTimetable_response.xml | SIRI | ET | 5.3 KB |
| exv_vehicleMonitoring_response.xml | SIRI | VM | 5.7 KB |
| exx_situationExchange_response.xml | SIRI | SX | 10.1 KB |
| exs_stopMonitoring_response.xml | SIRI | SM | 10.4 KB |

### Entur Profile Examples (to be downloaded)

| File | Format | Profile | Description |
|------|--------|---------|-------------|
| Full_PublicationDelivery_109_Oslo_morningbus_example.xml | NeTEx | - | Complete Oslo bus timetable |
| submodel_Timetable.xml | NeTEx | - | Timetable frame only |
| submodel_ServiceCalendar.xml | NeTEx | - | Calendar definitions |
| submodel_Network.xml | NeTEx | - | Network topology |
| submodel_StopPlaces.xml | NeTEx | - | Stop definitions |
| FlexibleLine-with-BookingArrangements-example.xml | NeTEx | - | Demand-responsive transport |
| siri-et.xml | SIRI | ET | Estimated timetable |
| siri-vm.xml | SIRI | VM | Vehicle monitoring |
| siri-sx.xml | SIRI | SX | Situation exchange |

---

## Expected Results

### netex2lc Performance

| Metric | Target | Expected |
|--------|--------|----------|
| Parse Success Rate | > 95% | ~100% (3/3 local files) |
| Avg Parse Time | < 100ms | ~20-50ms |
| Memory Peak | < 50MB | ~5-10MB |
| Connections per File | varies | 2-10 per journey |

### siri2lc Performance

| Profile | Target Success | Expected Output |
|---------|----------------|-----------------|
| SIRI-ET | > 95% | 2-5 connections per journey |
| SIRI-VM | > 95% | 1-5 vehicle positions |
| SIRI-SX | > 95% | 1-3 alerts per file |

---

## Evaluation Criteria

### Parsing Quality

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Success Rate | 30% | Files parsed without errors |
| Error Handling | 20% | Graceful handling of malformed input |
| Profile Detection | 10% | Correct auto-detection of SIRI profile |

### Output Quality

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Connection Yield | 15% | Expected number of connections generated |
| Data Completeness | 15% | Optional fields populated |
| Format Validity | 10% | Valid JSON-LD/Turtle output |

---

## Running the Benchmark

```bash
# Install dependencies
pip install -e ".[dev]"

# Run full benchmark with JSON output
python benchmarks/benchmark.py -o results.json

# Run with CSV output for spreadsheet/visualization
python benchmarks/benchmark.py --csv results.csv

# Run local only (no network required)
python benchmarks/benchmark.py --local-only

# Run with both JSON and CSV output
python benchmarks/benchmark.py -o results.json --csv results.csv

# View JSON results
cat results.json | python -m json.tool
```

## Generating Visualizations

After running the benchmark with `--csv`, generate charts:

```bash
# Generate all charts to charts/ directory
python benchmarks/visualize.py results.csv -o charts/

# Generate charts and display interactively
python benchmarks/visualize.py results.csv --show
```

### Generated Charts

| Chart | Description |
|-------|-------------|
| `dashboard.png` | Summary dashboard with all key metrics |
| `success_by_format.png` | Parse success rate by format (NeTEx/SIRI) |
| `success_by_siri_profile.png` | Success rate by SIRI profile (ET/VM/SX) |
| `parse_time_distribution.png` | Histogram of parse times |
| `size_vs_time.png` | Scatter plot of file size vs parse time |
| `completeness_scores.png` | Data completeness by file |
| `output_yield.png` | Connections/vehicles/alerts generated |
| `memory_usage.png` | Memory usage by file |
| `validity_summary.png` | JSON-LD/URI/DateTime validity |

---

## Sample Output

```
================================================================================
BENCHMARK SUMMARY
================================================================================

Files Processed:
  Total:     13
  NeTEx:     6
  SIRI:      7

Parsing Performance:
  Success Rate:     92.3%
  Avg Parse Time:   45.23 ms
  Avg Memory Peak:  8.45 MB

Output Yield:
  Connections:      24
  Vehicle Positions: 2
  Service Alerts:   3

Data Quality:
  Avg Completeness: 45.2%
  JSON-LD Valid:    100.0%

================================================================================
```

---

## Comparison with GTFS2LC

| Metric | netex2lc | gtfs2lc | Notes |
|--------|----------|---------|-------|
| Input Format | NeTEx XML | GTFS CSV | NeTEx more verbose |
| Parse Speed | ~50ms | ~20ms | XML parsing overhead |
| Memory Usage | ~10MB | ~5MB | DOM vs streaming |
| Output Richness | Higher | Standard | NeTEx has more metadata |
| Profile Support | Full | N/A | Multi-profile (ET, VM, SX) |
