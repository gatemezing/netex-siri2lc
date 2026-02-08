#!/usr/bin/env python3
"""
Visualization script for benchmark results.

Generates charts from benchmark CSV output to visualize:
- Parse success rate by format
- Parse time distribution
- Memory usage
- Completeness scores
- File size vs parse time correlation

Usage:
    python benchmarks/visualize.py results.csv -o charts/
    python benchmarks/visualize.py results.csv --show
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    print("Error: matplotlib is required for visualization.")
    print("Install with: pip install matplotlib")
    exit(1)


def load_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load benchmark results from CSV file."""
    results = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types
            row["file_size_kb"] = float(row["file_size_kb"])
            row["parse_success"] = row["parse_success"] == "True"
            row["parse_time_ms"] = float(row["parse_time_ms"])
            row["memory_peak_mb"] = float(row["memory_peak_mb"])
            row["connections"] = int(row["connections"])
            row["vehicles"] = int(row["vehicles"])
            row["alerts"] = int(row["alerts"])
            row["completeness_score"] = float(row["completeness_score"])
            row["jsonld_valid"] = row["jsonld_valid"] == "True"
            row["uri_valid"] = row["uri_valid"] == "True"
            row["datetime_valid"] = row["datetime_valid"] == "True"
            results.append(row)
    return results


def load_summary_csv(csv_path: str) -> Dict[str, float]:
    """Load benchmark summary from CSV file."""
    summary = {}
    summary_path = csv_path.replace(".csv", "_summary.csv")
    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    summary[row[0]] = float(row[1])
    except FileNotFoundError:
        pass
    return summary


def chart_success_by_format(results: List[Dict], output_dir: Path, show: bool = False):
    """Create bar chart of parse success rate by format."""
    # Group by format
    formats = {}
    for r in results:
        fmt = r["format"]
        if fmt not in formats:
            formats[fmt] = {"success": 0, "total": 0}
        formats[fmt]["total"] += 1
        if r["parse_success"]:
            formats[fmt]["success"] += 1

    # Calculate rates
    labels = list(formats.keys())
    success_rates = [formats[f]["success"] / formats[f]["total"] * 100 for f in labels]
    totals = [formats[f]["total"] for f in labels]

    # Create chart
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#2ecc71" if rate >= 90 else "#f39c12" if rate >= 70 else "#e74c3c" for rate in success_rates]
    bars = ax.bar(labels, success_rates, color=colors, edgecolor="black", linewidth=1.2)

    # Add value labels on bars
    for bar, rate, total in zip(bars, success_rates, totals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{rate:.1f}%\n(n={total})",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_xlabel("Format", fontsize=12)
    ax.set_ylabel("Success Rate (%)", fontsize=12)
    ax.set_title("Parse Success Rate by Format", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 110)
    ax.axhline(y=95, color="green", linestyle="--", alpha=0.5, label="Target (95%)")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "success_by_format.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_success_by_siri_profile(results: List[Dict], output_dir: Path, show: bool = False):
    """Create bar chart of parse success rate by SIRI profile."""
    # Filter SIRI results
    siri_results = [r for r in results if r["format"] == "siri" and r["siri_profile"]]
    if not siri_results:
        return

    # Group by profile
    profiles = {}
    for r in siri_results:
        profile = r["siri_profile"].upper()
        if profile not in profiles:
            profiles[profile] = {"success": 0, "total": 0}
        profiles[profile]["total"] += 1
        if r["parse_success"]:
            profiles[profile]["success"] += 1

    # Calculate rates
    labels = list(profiles.keys())
    success_rates = [profiles[p]["success"] / profiles[p]["total"] * 100 for p in labels]

    # Create chart
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#3498db", "#9b59b6", "#e67e22"][:len(labels)]
    bars = ax.bar(labels, success_rates, color=colors, edgecolor="black", linewidth=1.2)

    for bar, rate in zip(bars, success_rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
        )

    ax.set_xlabel("SIRI Profile", fontsize=12)
    ax.set_ylabel("Success Rate (%)", fontsize=12)
    ax.set_title("Parse Success Rate by SIRI Profile", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 110)

    plt.tight_layout()
    plt.savefig(output_dir / "success_by_siri_profile.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_parse_time_distribution(results: List[Dict], output_dir: Path, show: bool = False):
    """Create histogram of parse times."""
    successful = [r for r in results if r["parse_success"]]
    if not successful:
        return

    times = [r["parse_time_ms"] for r in successful]

    fig, ax = plt.subplots(figsize=(10, 5))
    n, bins, patches = ax.hist(times, bins=20, color="#3498db", edgecolor="black", alpha=0.7)

    # Color bars by performance
    for patch, left_edge in zip(patches, bins[:-1]):
        if left_edge < 50:
            patch.set_facecolor("#2ecc71")  # Excellent
        elif left_edge < 100:
            patch.set_facecolor("#f39c12")  # Good
        else:
            patch.set_facecolor("#e74c3c")  # Slow

    ax.axvline(x=100, color="red", linestyle="--", linewidth=2, label="Target (100ms)")
    ax.axvline(x=sum(times) / len(times), color="blue", linestyle="-", linewidth=2, label=f"Mean ({sum(times)/len(times):.1f}ms)")

    ax.set_xlabel("Parse Time (ms)", fontsize=12)
    ax.set_ylabel("Number of Files", fontsize=12)
    ax.set_title("Parse Time Distribution", fontsize=14, fontweight="bold")
    ax.legend()

    # Add legend for colors
    excellent = mpatches.Patch(color="#2ecc71", label="< 50ms (Excellent)")
    good = mpatches.Patch(color="#f39c12", label="50-100ms (Good)")
    slow = mpatches.Patch(color="#e74c3c", label="> 100ms (Slow)")
    ax.legend(handles=[excellent, good, slow], loc="upper right")

    plt.tight_layout()
    plt.savefig(output_dir / "parse_time_distribution.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_file_size_vs_time(results: List[Dict], output_dir: Path, show: bool = False):
    """Create scatter plot of file size vs parse time."""
    successful = [r for r in results if r["parse_success"]]
    if not successful:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Separate by format
    netex = [r for r in successful if r["format"] == "netex"]
    siri = [r for r in successful if r["format"] == "siri"]

    if netex:
        ax.scatter(
            [r["file_size_kb"] for r in netex],
            [r["parse_time_ms"] for r in netex],
            c="#3498db",
            label="NeTEx",
            alpha=0.7,
            s=80,
            edgecolors="black",
        )

    if siri:
        ax.scatter(
            [r["file_size_kb"] for r in siri],
            [r["parse_time_ms"] for r in siri],
            c="#e74c3c",
            label="SIRI",
            alpha=0.7,
            s=80,
            edgecolors="black",
        )

    ax.set_xlabel("File Size (KB)", fontsize=12)
    ax.set_ylabel("Parse Time (ms)", fontsize=12)
    ax.set_title("File Size vs Parse Time", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / "size_vs_time.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_completeness_scores(results: List[Dict], output_dir: Path, show: bool = False):
    """Create bar chart of completeness scores."""
    successful = [r for r in results if r["parse_success"] and r["completeness_score"] > 0]
    if not successful:
        return

    # Sort by completeness score
    sorted_results = sorted(successful, key=lambda x: x["completeness_score"], reverse=True)[:15]

    labels = [r["file"][:25] + "..." if len(r["file"]) > 25 else r["file"] for r in sorted_results]
    scores = [r["completeness_score"] * 100 for r in sorted_results]
    formats = [r["format"] for r in sorted_results]

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#3498db" if f == "netex" else "#e74c3c" for f in formats]
    bars = ax.barh(labels, scores, color=colors, edgecolor="black")

    ax.set_xlabel("Completeness Score (%)", fontsize=12)
    ax.set_title("Data Completeness by File (Top 15)", fontsize=14, fontweight="bold")
    ax.axvline(x=50, color="green", linestyle="--", alpha=0.5, label="Target (50%)")

    # Add legend
    netex_patch = mpatches.Patch(color="#3498db", label="NeTEx")
    siri_patch = mpatches.Patch(color="#e74c3c", label="SIRI")
    ax.legend(handles=[netex_patch, siri_patch])

    plt.tight_layout()
    plt.savefig(output_dir / "completeness_scores.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_output_yield(results: List[Dict], output_dir: Path, show: bool = False):
    """Create stacked bar chart of output yield."""
    successful = [r for r in results if r["parse_success"]]
    if not successful:
        return

    # Calculate totals by format
    netex_connections = sum(r["connections"] for r in successful if r["format"] == "netex")
    siri_connections = sum(r["connections"] for r in successful if r["format"] == "siri")
    siri_vehicles = sum(r["vehicles"] for r in successful if r["format"] == "siri")
    siri_alerts = sum(r["alerts"] for r in successful if r["format"] == "siri")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Connections by format
    ax1 = axes[0]
    ax1.bar(["NeTEx", "SIRI"], [netex_connections, siri_connections], color=["#3498db", "#e74c3c"], edgecolor="black")
    ax1.set_ylabel("Count", fontsize=12)
    ax1.set_title("Connections Generated", fontsize=14, fontweight="bold")
    for i, v in enumerate([netex_connections, siri_connections]):
        ax1.text(i, v + 1, str(v), ha="center", fontsize=11)

    # SIRI output types
    ax2 = axes[1]
    siri_labels = ["Connections", "Vehicles", "Alerts"]
    siri_values = [siri_connections, siri_vehicles, siri_alerts]
    colors = ["#e74c3c", "#9b59b6", "#f39c12"]
    ax2.bar(siri_labels, siri_values, color=colors, edgecolor="black")
    ax2.set_ylabel("Count", fontsize=12)
    ax2.set_title("SIRI Output by Type", fontsize=14, fontweight="bold")
    for i, v in enumerate(siri_values):
        ax2.text(i, v + 0.5, str(v), ha="center", fontsize=11)

    plt.tight_layout()
    plt.savefig(output_dir / "output_yield.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_memory_usage(results: List[Dict], output_dir: Path, show: bool = False):
    """Create bar chart of memory usage."""
    successful = [r for r in results if r["parse_success"] and r["memory_peak_mb"] > 0]
    if not successful:
        return

    # Sort by memory usage
    sorted_results = sorted(successful, key=lambda x: x["memory_peak_mb"], reverse=True)[:10]

    labels = [r["file"][:20] + "..." if len(r["file"]) > 20 else r["file"] for r in sorted_results]
    memory = [r["memory_peak_mb"] for r in sorted_results]

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#e74c3c" if m > 50 else "#f39c12" if m > 20 else "#2ecc71" for m in memory]
    bars = ax.barh(labels, memory, color=colors, edgecolor="black")

    ax.set_xlabel("Memory Peak (MB)", fontsize=12)
    ax.set_title("Memory Usage by File (Top 10)", fontsize=14, fontweight="bold")
    ax.axvline(x=50, color="red", linestyle="--", alpha=0.5, label="Limit (50MB)")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "memory_usage.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def chart_validity_summary(results: List[Dict], output_dir: Path, show: bool = False):
    """Create pie chart of validity metrics."""
    successful = [r for r in results if r["parse_success"]]
    if not successful:
        return

    total = len(successful)
    jsonld_valid = sum(1 for r in successful if r["jsonld_valid"])
    uri_valid = sum(1 for r in successful if r["uri_valid"])
    datetime_valid = sum(1 for r in successful if r["datetime_valid"])

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    metrics = [
        ("JSON-LD Valid", jsonld_valid, total),
        ("URI Format Valid", uri_valid, total),
        ("DateTime Valid", datetime_valid, total),
    ]

    for ax, (name, valid, tot) in zip(axes, metrics):
        invalid = tot - valid
        sizes = [valid, invalid]
        colors = ["#2ecc71", "#e74c3c"]
        labels = [f"Valid\n({valid})", f"Invalid\n({invalid})"]

        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax.set_title(name, fontsize=12, fontweight="bold")

    plt.suptitle("Output Validity Metrics", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "validity_summary.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def generate_summary_dashboard(results: List[Dict], summary: Dict, output_dir: Path, show: bool = False):
    """Generate a summary dashboard with key metrics."""
    fig = plt.figure(figsize=(14, 10))

    # Title
    fig.suptitle("Benchmark Results Dashboard", fontsize=18, fontweight="bold", y=0.98)

    # Key metrics boxes
    ax_metrics = fig.add_subplot(3, 3, 1)
    ax_metrics.axis("off")
    metrics_text = (
        f"Total Files: {summary.get('total_files', len(results))}\n"
        f"NeTEx: {summary.get('netex_files', sum(1 for r in results if r['format'] == 'netex'))}\n"
        f"SIRI: {summary.get('siri_files', sum(1 for r in results if r['format'] == 'siri'))}"
    )
    ax_metrics.text(0.5, 0.5, metrics_text, transform=ax_metrics.transAxes,
                    fontsize=14, ha="center", va="center",
                    bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#2c3e50"))
    ax_metrics.set_title("Files", fontsize=12, fontweight="bold")

    ax_perf = fig.add_subplot(3, 3, 2)
    ax_perf.axis("off")
    perf_text = (
        f"Success Rate: {summary.get('parse_success_rate', 0):.1f}%\n"
        f"Avg Time: {summary.get('avg_parse_time_ms', 0):.1f} ms\n"
        f"Avg Memory: {summary.get('avg_memory_mb', 0):.2f} MB"
    )
    ax_perf.text(0.5, 0.5, perf_text, transform=ax_perf.transAxes,
                 fontsize=14, ha="center", va="center",
                 bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#2c3e50"))
    ax_perf.set_title("Performance", fontsize=12, fontweight="bold")

    ax_yield = fig.add_subplot(3, 3, 3)
    ax_yield.axis("off")
    yield_text = (
        f"Connections: {summary.get('total_connections', sum(r['connections'] for r in results))}\n"
        f"Vehicles: {summary.get('total_vehicles', sum(r['vehicles'] for r in results))}\n"
        f"Alerts: {summary.get('total_alerts', sum(r['alerts'] for r in results))}"
    )
    ax_yield.text(0.5, 0.5, yield_text, transform=ax_yield.transAxes,
                  fontsize=14, ha="center", va="center",
                  bbox=dict(boxstyle="round", facecolor="#ecf0f1", edgecolor="#2c3e50"))
    ax_yield.set_title("Output Yield", fontsize=12, fontweight="bold")

    # Success rate by format (bar chart)
    ax_success = fig.add_subplot(3, 3, 4)
    formats = {}
    for r in results:
        fmt = r["format"]
        if fmt not in formats:
            formats[fmt] = {"success": 0, "total": 0}
        formats[fmt]["total"] += 1
        if r["parse_success"]:
            formats[fmt]["success"] += 1
    labels = list(formats.keys())
    rates = [formats[f]["success"] / formats[f]["total"] * 100 for f in labels]
    colors = ["#3498db", "#e74c3c"][:len(labels)]
    ax_success.bar(labels, rates, color=colors, edgecolor="black")
    ax_success.set_ylabel("Success %")
    ax_success.set_title("Success by Format", fontsize=12, fontweight="bold")
    ax_success.set_ylim(0, 110)

    # Parse time histogram
    ax_time = fig.add_subplot(3, 3, 5)
    successful = [r for r in results if r["parse_success"]]
    if successful:
        times = [r["parse_time_ms"] for r in successful]
        ax_time.hist(times, bins=15, color="#3498db", edgecolor="black", alpha=0.7)
        ax_time.axvline(x=100, color="red", linestyle="--", label="Target")
    ax_time.set_xlabel("Time (ms)")
    ax_time.set_title("Parse Time Distribution", fontsize=12, fontweight="bold")

    # Completeness distribution
    ax_complete = fig.add_subplot(3, 3, 6)
    if successful:
        scores = [r["completeness_score"] * 100 for r in successful if r["completeness_score"] > 0]
        if scores:
            ax_complete.hist(scores, bins=10, color="#2ecc71", edgecolor="black", alpha=0.7)
            ax_complete.axvline(x=50, color="red", linestyle="--", label="Target")
    ax_complete.set_xlabel("Completeness %")
    ax_complete.set_title("Completeness Distribution", fontsize=12, fontweight="bold")

    # Output yield by type
    ax_output = fig.add_subplot(3, 3, 7)
    output_types = ["Connections", "Vehicles", "Alerts"]
    output_values = [
        sum(r["connections"] for r in results),
        sum(r["vehicles"] for r in results),
        sum(r["alerts"] for r in results),
    ]
    ax_output.bar(output_types, output_values, color=["#3498db", "#9b59b6", "#f39c12"], edgecolor="black")
    ax_output.set_title("Output by Type", fontsize=12, fontweight="bold")

    # Validity pie chart
    ax_valid = fig.add_subplot(3, 3, 8)
    if successful:
        valid = sum(1 for r in successful if r["jsonld_valid"])
        invalid = len(successful) - valid
        ax_valid.pie([valid, invalid], labels=[f"Valid ({valid})", f"Invalid ({invalid})"],
                     colors=["#2ecc71", "#e74c3c"], autopct="%1.0f%%")
    ax_valid.set_title("JSON-LD Validity", fontsize=12, fontweight="bold")

    # File size vs time scatter
    ax_scatter = fig.add_subplot(3, 3, 9)
    if successful:
        netex = [r for r in successful if r["format"] == "netex"]
        siri = [r for r in successful if r["format"] == "siri"]
        if netex:
            ax_scatter.scatter([r["file_size_kb"] for r in netex], [r["parse_time_ms"] for r in netex],
                               c="#3498db", label="NeTEx", alpha=0.6)
        if siri:
            ax_scatter.scatter([r["file_size_kb"] for r in siri], [r["parse_time_ms"] for r in siri],
                               c="#e74c3c", label="SIRI", alpha=0.6)
        ax_scatter.legend(fontsize=8)
    ax_scatter.set_xlabel("Size (KB)")
    ax_scatter.set_ylabel("Time (ms)")
    ax_scatter.set_title("Size vs Time", fontsize=12, fontweight="bold")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / "dashboard.png", dpi=150)
    if show:
        plt.show()
    plt.close()


def main():
    """Generate visualizations from benchmark CSV results."""
    parser = argparse.ArgumentParser(description="Generate benchmark visualization charts")
    parser.add_argument("csv_file", help="Input CSV file from benchmark")
    parser.add_argument("-o", "--output", default="charts", help="Output directory for charts")
    parser.add_argument("--show", action="store_true", help="Display charts interactively")

    args = parser.parse_args()

    # Load data
    results = load_csv(args.csv_file)
    summary = load_summary_csv(args.csv_file)

    print(f"Loaded {len(results)} benchmark results")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate charts
    print("Generating charts...")

    chart_success_by_format(results, output_dir, args.show)
    print("  - success_by_format.png")

    chart_success_by_siri_profile(results, output_dir, args.show)
    print("  - success_by_siri_profile.png")

    chart_parse_time_distribution(results, output_dir, args.show)
    print("  - parse_time_distribution.png")

    chart_file_size_vs_time(results, output_dir, args.show)
    print("  - size_vs_time.png")

    chart_completeness_scores(results, output_dir, args.show)
    print("  - completeness_scores.png")

    chart_output_yield(results, output_dir, args.show)
    print("  - output_yield.png")

    chart_memory_usage(results, output_dir, args.show)
    print("  - memory_usage.png")

    chart_validity_summary(results, output_dir, args.show)
    print("  - validity_summary.png")

    generate_summary_dashboard(results, summary, output_dir, args.show)
    print("  - dashboard.png")

    print(f"\nCharts saved to: {output_dir}/")


if __name__ == "__main__":
    main()
