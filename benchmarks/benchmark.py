#!/usr/bin/env python3
"""
Benchmark framework for netex2lc and siri2lc converters.

Uses test data from:
- Local testdata/ directory
- Entur profile-examples: https://github.com/entur/profile-examples

Evaluation Metrics:
1. Parsing Success Rate - % of files successfully parsed
2. Connection Yield - Number of connections generated per file
3. Data Completeness - % of optional fields populated
4. Processing Time - Seconds per file
5. Memory Usage - Peak memory consumption
6. Output Validity - RDF/JSON-LD syntactic validity
7. Semantic Accuracy - Correct URI generation, time formats, references
"""
from __future__ import annotations

import json
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlretrieve

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from netex2lc.netex_parser import parse_netex
from netex2lc.uri import URIStrategy
from netex2lc.validation import validate_xml_wellformed, detect_format, detect_siri_profile
from netex2lc.serializers import ConnectionSerializer
from siri2lc.siri_parser import parse_siri_et
from siri2lc.siri_vm_parser import parse_siri_vm
from siri2lc.siri_sx_parser import parse_siri_sx


# Entur profile-examples raw URLs
ENTUR_BASE = "https://raw.githubusercontent.com/entur/profile-examples/master"

# Verified paths from https://github.com/entur/profile-examples
ENTUR_NETEX_FILES = [
    # Full publication delivery example
    "netex/Full_PublicationDelivery_109_Oslo_morningbus_example.xml",
    # Network examples
    "netex/network/FlexibleLine-316-with-interchange.xml",
    "netex/network/Line61A.xml",
    "netex/network/Train-Network-with-RoutePointProjections.xml",
    # Schedule/calendar examples
    "netex/schedule/ServiceCalendar-example.xml",
    "netex/schedule/ServiceCalendar-DayTypeAssignments.xml",
    # Stop examples
    "netex/stops/BasicStopPlace_example.xml",
    "netex/stops/OsloS_station_example.xml",
    # Timetable examples
    "netex/timetable/AKT-2706-591T-Stokkeland-Lauvslandsmoen-with-extended-DestinationDisplay-incl-Via-and-Variants.xml",
]

ENTUR_SIRI_FILES = [
    # SIRI-ET (Estimated Timetable)
    "siri/siri-et-outline.xml",
    "siri/estimated-timetable/siri-et-nsb-example.xml",
    "siri/estimated-timetable/siri-et-extra-journey-1.xml",
    # SIRI-VM (Vehicle Monitoring)
    "siri/siri-vm-outline.xml",
    "siri/vehicle-monitoring/siri-vm.xml",
    "siri/vehicle-monitoring/siri-vm-at-stop.xml",
    # SIRI-SX (Situation Exchange)
    "siri/siri-sx-outline.xml",
    "siri/situation-exchange/siri-sx.xml",
    "siri/situation-exchange/siri-sx-for-line.xml",
]


@dataclass
class BenchmarkResult:
    """Result of benchmarking a single file."""

    file_path: str
    file_size_kb: float
    format_type: str  # 'netex' or 'siri'
    siri_profile: Optional[str] = None  # 'et', 'vm', 'sx' for SIRI

    # Parsing metrics
    parse_success: bool = False
    parse_error: Optional[str] = None
    parse_time_ms: float = 0.0
    memory_peak_mb: float = 0.0

    # Yield metrics
    connections_count: int = 0
    vehicles_count: int = 0  # For SIRI-VM
    alerts_count: int = 0    # For SIRI-SX

    # Data completeness (% of optional fields populated)
    completeness_score: float = 0.0
    completeness_details: Dict[str, float] = field(default_factory=dict)

    # Output validity
    jsonld_valid: bool = False
    turtle_valid: bool = False

    # Semantic accuracy
    uri_valid: bool = False
    datetime_valid: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "file": self.file_path,
            "file_size_kb": round(self.file_size_kb, 2),
            "format": self.format_type,
            "siri_profile": self.siri_profile,
            "parsing": {
                "success": self.parse_success,
                "error": self.parse_error,
                "time_ms": round(self.parse_time_ms, 2),
                "memory_peak_mb": round(self.memory_peak_mb, 2),
            },
            "yield": {
                "connections": self.connections_count,
                "vehicles": self.vehicles_count,
                "alerts": self.alerts_count,
            },
            "completeness": {
                "score": round(self.completeness_score, 2),
                "details": self.completeness_details,
            },
            "validity": {
                "jsonld": self.jsonld_valid,
                "turtle": self.turtle_valid,
                "uri_format": self.uri_valid,
                "datetime_format": self.datetime_valid,
            },
        }


@dataclass
class BenchmarkSummary:
    """Summary statistics across all benchmark runs."""

    total_files: int = 0
    netex_files: int = 0
    siri_files: int = 0

    parse_success_rate: float = 0.0
    avg_parse_time_ms: float = 0.0
    avg_memory_mb: float = 0.0

    total_connections: int = 0
    total_vehicles: int = 0
    total_alerts: int = 0

    avg_completeness: float = 0.0
    jsonld_valid_rate: float = 0.0

    results: List[BenchmarkResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "summary": {
                "total_files": self.total_files,
                "netex_files": self.netex_files,
                "siri_files": self.siri_files,
                "parse_success_rate": round(self.parse_success_rate * 100, 1),
                "avg_parse_time_ms": round(self.avg_parse_time_ms, 2),
                "avg_memory_mb": round(self.avg_memory_mb, 2),
                "total_connections": self.total_connections,
                "total_vehicles": self.total_vehicles,
                "total_alerts": self.total_alerts,
                "avg_completeness": round(self.avg_completeness * 100, 1),
                "jsonld_valid_rate": round(self.jsonld_valid_rate * 100, 1),
            },
            "results": [r.to_dict() for r in self.results],
        }


def download_entur_files(cache_dir: Path) -> List[Path]:
    """Download Entur profile examples to cache directory."""
    from urllib.error import HTTPError

    downloaded = []
    failed = []
    cache_dir.mkdir(parents=True, exist_ok=True)

    all_files = ENTUR_NETEX_FILES + ENTUR_SIRI_FILES

    print(f"Downloading {len(all_files)} files from Entur profile-examples...")

    for file_path in all_files:
        url = f"{ENTUR_BASE}/{file_path}"
        # Use full path structure to avoid name collisions
        local_path = cache_dir / file_path.replace("/", "_")

        if local_path.exists():
            downloaded.append(local_path)
            continue

        try:
            urlretrieve(url, local_path)
            downloaded.append(local_path)
            print(f"  [OK] {Path(file_path).name}")
        except HTTPError as e:
            if e.code == 404:
                print(f"  [404] {file_path} - not found")
            else:
                print(f"  [ERR] {file_path} - HTTP {e.code}")
            failed.append(file_path)
        except Exception as e:
            print(f"  [ERR] {file_path} - {e}")
            failed.append(file_path)

    if failed:
        print(f"\nWarning: {len(failed)} files could not be downloaded")

    print(f"Successfully cached {len(downloaded)} files\n")
    return downloaded


def calculate_completeness(connections: List) -> Dict[str, float]:
    """Calculate completeness score for optional fields."""
    if not connections:
        return {"score": 0.0}

    optional_fields = [
        "route", "trip", "operator", "headsign",
        "transport_mode", "wheelchair_accessible",
        "departure_lat", "departure_lon",
        "departure_stop_name", "line_name",
    ]

    field_scores = {}
    for field_name in optional_fields:
        count = sum(1 for c in connections if getattr(c, field_name, None) is not None)
        field_scores[field_name] = count / len(connections)

    avg_score = sum(field_scores.values()) / len(field_scores) if field_scores else 0
    field_scores["score"] = avg_score

    return field_scores


def validate_jsonld(data: dict) -> bool:
    """Validate JSON-LD structure."""
    try:
        if "@context" not in data:
            return False
        if "@graph" not in data and "@id" not in data:
            return False
        # Check that graph items have required fields
        if "@graph" in data:
            for item in data["@graph"]:
                if "@id" not in item:
                    return False
        return True
    except Exception:
        return False


def validate_uris(connections: List) -> bool:
    """Validate URI format in connections."""
    try:
        for c in connections:
            if not c.id.startswith("http"):
                return False
            if not c.departure_stop.startswith("http"):
                return False
            if not c.arrival_stop.startswith("http"):
                return False
        return True
    except Exception:
        return False


def validate_vm_uris(positions: List, uri_strategy: URIStrategy) -> bool:
    """Validate URI format in vehicle positions via JSON-LD output."""
    try:
        for pos in positions:
            jsonld = pos.to_jsonld(uri_strategy)
            # Check @id is a valid HTTP URI
            if not jsonld.get("@id", "").startswith("http"):
                return False
            # Check line ref if present
            if "netex:line" in jsonld:
                if not jsonld["netex:line"].get("@id", "").startswith("http"):
                    return False
            # Check journey ref if present
            if "netex:serviceJourney" in jsonld:
                if not jsonld["netex:serviceJourney"].get("@id", "").startswith("http"):
                    return False
            # Check stop refs if present
            for stop_key in ["siri:destinationRef", "siri:currentStopPoint", "siri:nextStopPoint"]:
                if stop_key in jsonld:
                    if not jsonld[stop_key].get("@id", "").startswith("http"):
                        return False
        return True
    except Exception:
        return False


def validate_sx_uris(alerts: List, uri_strategy: URIStrategy) -> bool:
    """Validate URI format in service alerts via JSON-LD output."""
    try:
        for alert in alerts:
            jsonld = alert.to_jsonld(uri_strategy)
            # Check @id is a valid HTTP URI
            if not jsonld.get("@id", "").startswith("http"):
                return False
            # Check affected stops
            if "siri:affectedStopPoints" in jsonld:
                for stop in jsonld["siri:affectedStopPoints"]:
                    if not stop.get("@id", "").startswith("http"):
                        return False
            # Check affected lines
            if "siri:affectedLines" in jsonld:
                for line in jsonld["siri:affectedLines"]:
                    if not line.get("@id", "").startswith("http"):
                        return False
        return True
    except Exception:
        return False


def validate_vm_jsonld(positions: List, uri_strategy: URIStrategy) -> bool:
    """Validate JSON-LD structure for vehicle positions."""
    try:
        from siri2lc.siri_vm_parser import to_jsonld
        data = to_jsonld(positions, uri_strategy)
        return validate_jsonld(data)
    except Exception:
        return False


def validate_sx_jsonld(alerts: List, uri_strategy: URIStrategy) -> bool:
    """Validate JSON-LD structure for service alerts."""
    try:
        from siri2lc.siri_sx_parser import to_jsonld
        data = to_jsonld(alerts, uri_strategy)
        return validate_jsonld(data)
    except Exception:
        return False


def validate_datetimes(connections: List) -> bool:
    """Validate datetime format in connections."""
    try:
        for c in connections:
            # Check ISO 8601 format
            if "T" not in c.departure_time:
                return False
            if "T" not in c.arrival_time:
                return False
        return True
    except Exception:
        return False


def benchmark_netex_file(file_path: Path, uri_strategy: URIStrategy) -> BenchmarkResult:
    """Benchmark a single NeTEx file."""
    result = BenchmarkResult(
        file_path=str(file_path.name),
        file_size_kb=file_path.stat().st_size / 1024,
        format_type="netex",
    )

    # Check well-formed XML
    is_valid, error = validate_xml_wellformed(str(file_path))
    if not is_valid:
        result.parse_error = error
        return result

    # Parse with timing and memory tracking
    tracemalloc.start()
    start_time = time.perf_counter()

    try:
        connections = parse_netex([str(file_path)], uri_strategy)
        result.parse_success = True
        result.connections_count = len(connections)

        # Calculate completeness
        completeness = calculate_completeness(connections)
        result.completeness_score = completeness.get("score", 0)
        result.completeness_details = {k: v for k, v in completeness.items() if k != "score"}

        # Validate URIs and datetimes
        if connections:
            result.uri_valid = validate_uris(connections)
            result.datetime_valid = validate_datetimes(connections)

        # Validate output formats
        if connections:
            serializer = ConnectionSerializer(connections)
            jsonld_data = serializer.to_jsonld_dict()
            result.jsonld_valid = validate_jsonld(jsonld_data)

            try:
                turtle_output = serializer.to_turtle()
                result.turtle_valid = len(turtle_output) > 0
            except Exception:
                result.turtle_valid = False

    except Exception as e:
        result.parse_error = str(e)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    result.parse_time_ms = (end_time - start_time) * 1000
    result.memory_peak_mb = peak / 1024 / 1024

    return result


def benchmark_siri_file(file_path: Path, uri_strategy: URIStrategy) -> BenchmarkResult:
    """Benchmark a single SIRI file."""
    result = BenchmarkResult(
        file_path=str(file_path.name),
        file_size_kb=file_path.stat().st_size / 1024,
        format_type="siri",
    )

    # Check well-formed XML
    is_valid, error = validate_xml_wellformed(str(file_path))
    if not is_valid:
        result.parse_error = error
        return result

    # Detect SIRI profile
    profile = detect_siri_profile(str(file_path))
    result.siri_profile = profile

    if not profile:
        result.parse_error = "Could not detect SIRI profile"
        return result

    # Parse with timing and memory tracking
    tracemalloc.start()
    start_time = time.perf_counter()

    try:
        if profile == "et":
            connections = parse_siri_et(str(file_path), uri_strategy, date.today())
            result.connections_count = len(connections)
            result.parse_success = True

            if connections:
                completeness = calculate_completeness(connections)
                result.completeness_score = completeness.get("score", 0)
                result.uri_valid = validate_uris(connections)
                result.datetime_valid = validate_datetimes(connections)

                serializer = ConnectionSerializer(connections)
                result.jsonld_valid = validate_jsonld(serializer.to_jsonld_dict())

        elif profile == "vm":
            positions = parse_siri_vm(str(file_path), uri_strategy)
            result.vehicles_count = len(positions)
            result.parse_success = True

            if positions:
                # Check VM completeness
                vm_fields = ["latitude", "longitude", "line_ref", "journey_ref"]
                field_counts = {f: sum(1 for p in positions if getattr(p, f, None)) for f in vm_fields}
                result.completeness_score = sum(field_counts.values()) / (len(vm_fields) * len(positions))
                # Validate JSON-LD and URIs using uri_strategy
                result.jsonld_valid = validate_vm_jsonld(positions, uri_strategy)
                result.uri_valid = validate_vm_uris(positions, uri_strategy)
                result.datetime_valid = all(
                    "T" in p.recorded_at for p in positions if p.recorded_at
                )

        elif profile == "sx":
            alerts = parse_siri_sx(str(file_path), uri_strategy)
            result.alerts_count = len(alerts)
            result.parse_success = True

            if alerts:
                # Check SX completeness
                sx_fields = ["summary", "description", "severity"]
                field_counts = {f: sum(1 for a in alerts if getattr(a, f, None)) for f in sx_fields}
                result.completeness_score = sum(field_counts.values()) / (len(sx_fields) * len(alerts))
                # Validate JSON-LD and URIs using uri_strategy
                result.jsonld_valid = validate_sx_jsonld(alerts, uri_strategy)
                result.uri_valid = validate_sx_uris(alerts, uri_strategy)
                result.datetime_valid = all(
                    "T" in a.creation_time for a in alerts if a.creation_time
                )

    except Exception as e:
        result.parse_error = str(e)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    result.parse_time_ms = (end_time - start_time) * 1000
    result.memory_peak_mb = peak / 1024 / 1024

    return result


def run_benchmark(
    include_local: bool = True,
    include_entur: bool = True,
    cache_dir: Optional[Path] = None,
) -> BenchmarkSummary:
    """Run full benchmark suite."""

    uri_strategy = URIStrategy(base_uri="http://benchmark.example.org")
    results: List[BenchmarkResult] = []

    # Collect test files
    test_files: List[Path] = []

    if include_local:
        local_dir = Path(__file__).parent.parent / "testdata"
        if local_dir.exists():
            test_files.extend(local_dir.glob("**/*.xml"))

    if include_entur:
        cache = cache_dir or Path(__file__).parent / ".cache"
        entur_files = download_entur_files(cache)
        test_files.extend(entur_files)

    print(f"\nBenchmarking {len(test_files)} files...\n")
    print("-" * 80)

    for file_path in test_files:
        print(f"Processing: {file_path.name[:50]:<50}", end=" ")

        # Detect format
        fmt = detect_format(str(file_path))

        if fmt == "netex":
            result = benchmark_netex_file(file_path, uri_strategy)
        elif fmt == "siri":
            result = benchmark_siri_file(file_path, uri_strategy)
        else:
            result = BenchmarkResult(
                file_path=str(file_path.name),
                file_size_kb=file_path.stat().st_size / 1024,
                format_type="unknown",
                parse_error="Unknown format",
            )

        results.append(result)

        # Print status
        if result.parse_success:
            yield_info = f"C:{result.connections_count} V:{result.vehicles_count} A:{result.alerts_count}"
            print(f"[OK] {yield_info:<20} {result.parse_time_ms:.0f}ms")
        else:
            print(f"[FAIL] {result.parse_error[:30] if result.parse_error else 'Unknown'}")

    print("-" * 80)

    # Calculate summary
    summary = BenchmarkSummary(results=results)
    summary.total_files = len(results)
    summary.netex_files = sum(1 for r in results if r.format_type == "netex")
    summary.siri_files = sum(1 for r in results if r.format_type == "siri")

    successful = [r for r in results if r.parse_success]
    if successful:
        summary.parse_success_rate = len(successful) / len(results)
        summary.avg_parse_time_ms = sum(r.parse_time_ms for r in successful) / len(successful)
        summary.avg_memory_mb = sum(r.memory_peak_mb for r in successful) / len(successful)
        summary.avg_completeness = sum(r.completeness_score for r in successful) / len(successful)
        summary.jsonld_valid_rate = sum(1 for r in successful if r.jsonld_valid) / len(successful)

    summary.total_connections = sum(r.connections_count for r in results)
    summary.total_vehicles = sum(r.vehicles_count for r in results)
    summary.total_alerts = sum(r.alerts_count for r in results)

    return summary


def print_summary(summary: BenchmarkSummary):
    """Print benchmark summary to console."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)

    print(f"\nFiles Processed:")
    print(f"  Total:     {summary.total_files}")
    print(f"  NeTEx:     {summary.netex_files}")
    print(f"  SIRI:      {summary.siri_files}")

    print(f"\nParsing Performance:")
    print(f"  Success Rate:     {summary.parse_success_rate * 100:.1f}%")
    print(f"  Avg Parse Time:   {summary.avg_parse_time_ms:.2f} ms")
    print(f"  Avg Memory Peak:  {summary.avg_memory_mb:.2f} MB")

    print(f"\nOutput Yield:")
    print(f"  Connections:      {summary.total_connections}")
    print(f"  Vehicle Positions:{summary.total_vehicles}")
    print(f"  Service Alerts:   {summary.total_alerts}")

    print(f"\nData Quality:")
    print(f"  Avg Completeness: {summary.avg_completeness * 100:.1f}%")
    print(f"  JSON-LD Valid:    {summary.jsonld_valid_rate * 100:.1f}%")

    print("\n" + "=" * 80)


def export_csv(summary: BenchmarkSummary, output_path: str):
    """Export benchmark results to CSV file."""
    import csv

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row
        writer.writerow([
            "file",
            "format",
            "siri_profile",
            "file_size_kb",
            "parse_success",
            "parse_time_ms",
            "memory_peak_mb",
            "connections",
            "vehicles",
            "alerts",
            "completeness_score",
            "jsonld_valid",
            "uri_valid",
            "datetime_valid",
            "parse_error",
        ])

        # Data rows
        for r in summary.results:
            writer.writerow([
                r.file_path,
                r.format_type,
                r.siri_profile or "",
                round(r.file_size_kb, 2),
                r.parse_success,
                round(r.parse_time_ms, 2),
                round(r.memory_peak_mb, 4),
                r.connections_count,
                r.vehicles_count,
                r.alerts_count,
                round(r.completeness_score, 4),
                r.jsonld_valid,
                r.uri_valid,
                r.datetime_valid,
                r.parse_error or "",
            ])

    # Also write summary CSV
    summary_path = output_path.replace(".csv", "_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["total_files", summary.total_files])
        writer.writerow(["netex_files", summary.netex_files])
        writer.writerow(["siri_files", summary.siri_files])
        writer.writerow(["parse_success_rate", round(summary.parse_success_rate * 100, 2)])
        writer.writerow(["avg_parse_time_ms", round(summary.avg_parse_time_ms, 2)])
        writer.writerow(["avg_memory_mb", round(summary.avg_memory_mb, 4)])
        writer.writerow(["total_connections", summary.total_connections])
        writer.writerow(["total_vehicles", summary.total_vehicles])
        writer.writerow(["total_alerts", summary.total_alerts])
        writer.writerow(["avg_completeness", round(summary.avg_completeness * 100, 2)])
        writer.writerow(["jsonld_valid_rate", round(summary.jsonld_valid_rate * 100, 2)])

    print(f"CSV exported to: {output_path}")
    print(f"Summary exported to: {summary_path}")


def main():
    """Run benchmark and output results."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark netex2lc and siri2lc converters")
    parser.add_argument("--local-only", action="store_true", help="Only use local testdata")
    parser.add_argument("--entur-only", action="store_true", help="Only use Entur examples")
    parser.add_argument("--output", "-o", help="Output JSON file for results")
    parser.add_argument("--csv", help="Output CSV file for results")
    parser.add_argument("--cache-dir", help="Cache directory for downloaded files")

    args = parser.parse_args()

    include_local = not args.entur_only
    include_entur = not args.local_only
    cache_dir = Path(args.cache_dir) if args.cache_dir else None

    summary = run_benchmark(
        include_local=include_local,
        include_entur=include_entur,
        cache_dir=cache_dir,
    )

    print_summary(summary)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)
        print(f"\nResults saved to: {args.output}")

    if args.csv:
        export_csv(summary, args.csv)


if __name__ == "__main__":
    main()
