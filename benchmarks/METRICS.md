# Benchmark Evaluation Metrics

This document defines the evaluation metrics used to assess the quality and performance of the `netex2lc` and `siri2lc` converters.

## Overview

The benchmark evaluates converters across four dimensions:

| Dimension | Description |
|-----------|-------------|
| **Performance** | Speed and resource usage |
| **Yield** | Quantity of output produced |
| **Completeness** | Data richness of output |
| **Validity** | Correctness of output format |

---

## 1. Performance Metrics

### 1.1 Parse Time (ms)

**Definition**: Wall-clock time to parse input and generate output objects.

**Measurement**: `time.perf_counter()` before/after parsing

**Target**: < 100ms for typical files, < 1000ms for large files (>1MB)

### 1.2 Memory Peak (MB)

**Definition**: Maximum memory allocated during parsing.

**Measurement**: `tracemalloc.get_traced_memory()`

**Target**: < 50MB for typical files, < 500MB for large files

### 1.3 Throughput (connections/second)

**Definition**: Rate of connection generation.

**Calculation**: `connections_count / parse_time_seconds`

**Target**: > 1000 connections/second

---

## 2. Yield Metrics

### 2.1 Connection Count

**Definition**: Number of `lc:Connection` objects generated.

**Expected**: For NeTEx with N passing times per journey: `N-1` connections per journey

**Formula**:
```
Expected = Σ (passing_times_per_journey - 1) for all ServiceJourneys
```

### 2.2 Vehicle Position Count (SIRI-VM)

**Definition**: Number of `VehicleActivity` records parsed.

**Expected**: One per `<VehicleActivity>` element in input

### 2.3 Alert Count (SIRI-SX)

**Definition**: Number of `PtSituationElement` or `RoadSituationElement` records parsed.

**Expected**: One per situation element in input

### 2.4 Parse Success Rate

**Definition**: Percentage of files that parse without errors.

**Calculation**: `successful_files / total_files * 100`

**Target**: > 95%

---

## 3. Completeness Metrics

### 3.1 Field Population Rate

**Definition**: Percentage of optional fields populated in output.

**Fields Evaluated for Connections**:

| Field | Priority | Source |
|-------|----------|--------|
| `route` (line reference) | High | `LineRef` |
| `trip` (journey reference) | High | `ServiceJourneyRef` |
| `operator` | Medium | `OperatorRef` |
| `headsign` | Medium | `DestinationDisplay` |
| `transport_mode` | Medium | `TransportMode` |
| `wheelchair_accessible` | Low | `AccessibilityAssessment` |
| `departure_lat/lon` | Low | `StopPlace/Quay` coordinates |
| `departure_stop_name` | Low | `Name` element |

**Calculation**:
```
Field Rate = populated_count / total_connections * 100
Overall = average(all field rates)
```

**Target**: > 50% for high-priority fields, > 30% overall

### 3.2 Real-time Data Richness (SIRI-ET)

**Fields Evaluated**:
- `departure_delay` - Delay in seconds
- `arrival_delay` - Delay in seconds
- `departure_status` - Status enum (onTime, delayed, cancelled)
- `arrival_status` - Status enum

**Target**: > 80% for delay fields when expected times differ from aimed times

---

## 4. Validity Metrics

### 4.1 JSON-LD Validity

**Definition**: Output conforms to JSON-LD structure.

**Checks**:
1. `@context` present with required namespaces
2. `@graph` array or `@id` at root
3. Each connection has `@id` and `@type`
4. Time values have `@type: xsd:dateTime`

**Target**: 100%

### 4.2 Turtle Validity

**Definition**: Output is valid Turtle RDF syntax.

**Check**: Can be loaded by RDFLib without errors

**Target**: 100%

### 4.3 URI Format Validity

**Definition**: Generated URIs follow expected patterns.

**Checks**:
1. All URIs start with configured base URI
2. URIs are properly encoded (no spaces, special chars)
3. URI templates are correctly expanded

**Target**: 100%

### 4.4 DateTime Format Validity

**Definition**: Time values conform to ISO 8601.

**Format**: `YYYY-MM-DDTHH:MM:SS+HH:MM` or `YYYY-MM-DDTHH:MM:SSZ`

**Checks**:
1. Contains `T` separator
2. Parseable by `datetime.fromisoformat()`
3. Timezone info present

**Target**: 100%

---

## 5. Semantic Accuracy Metrics

### 5.1 Stop Reference Accuracy

**Definition**: Departure/arrival stops correctly reference input stop IDs.

**Check**: Generated stop URIs contain original stop reference IDs

### 5.2 Time Ordering

**Definition**: Arrival time >= Departure time for each connection.

**Check**: `arrival_time > departure_time` or equal (for instantaneous stops)

### 5.3 Sequence Integrity

**Definition**: Connections form valid chains within a journey.

**Check**: For connections in same trip, `conn[n].arrival_stop == conn[n+1].departure_stop`

---

## Benchmark Test Data

### Local Test Data (`testdata/`)

| Category | Files | Purpose |
|----------|-------|---------|
| NeTEx | 3 | Bus timetable examples |
| SIRI-ET | 2 | Estimated timetable |
| SIRI-VM | 2 | Vehicle monitoring |
| SIRI-SX | 2 | Situation exchange |

### Entur Profile Examples

| Category | Files | Purpose |
|----------|-------|---------|
| NeTEx Full | 1 | Complete publication delivery (Oslo bus) |
| NeTEx Submodels | 4 | Individual frame types |
| NeTEx Flex | 1 | Flexible lines with booking |
| SIRI | 3 | One per profile (ET, VM, SX) |

---

## Running the Benchmark

```bash
# Full benchmark (local + Entur)
python benchmarks/benchmark.py

# Local only
python benchmarks/benchmark.py --local-only

# Entur only
python benchmarks/benchmark.py --entur-only

# Save results
python benchmarks/benchmark.py -o results.json
```

---

## Interpreting Results

### Success Criteria

| Metric | Minimum | Good | Excellent |
|--------|---------|------|-----------|
| Parse Success Rate | 80% | 95% | 100% |
| Avg Parse Time | < 500ms | < 100ms | < 50ms |
| Avg Memory | < 200MB | < 50MB | < 20MB |
| Completeness | 30% | 50% | 70% |
| JSON-LD Valid | 90% | 99% | 100% |

### Common Issues

1. **Low connection count**: Check if file contains `ServiceJourney` with `PassingTimes`
2. **High memory**: Consider streaming parser for large files
3. **Low completeness**: Check if optional elements exist in source data
4. **Invalid output**: Check namespace handling and URI encoding
