"""Command-line interface for SIRI to Linked Connections converter."""
from __future__ import annotations

import json
import sys
from datetime import date

import click

from netex2lc.config import load_config
from netex2lc.logging_config import setup_logging
from netex2lc.serializers import serialize_connections
from netex2lc.uri import URIStrategy
from netex2lc.validation import validate_input, detect_siri_profile

from .siri_parser import parse_siri_et
from .siri_vm_parser import parse_siri_vm, to_jsonld as vm_to_jsonld
from .siri_sx_parser import parse_siri_sx, to_jsonld as sx_to_jsonld


@click.command(help="Convert SIRI XML to Linked Connections (JSON-LD, Turtle, N-Triples).")
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="SIRI XML file.",
)
@click.option(
    "--type",
    "siri_type",
    type=click.Choice(["et", "vm", "sx", "auto"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="SIRI profile type. 'auto' will detect from file.",
)
@click.option(
    "--output",
    default="-",
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help="Output file path, or '-' for stdout.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["jsonld", "turtle", "ttl", "ntriples", "nt", "rdfxml"], case_sensitive=False),
    default="jsonld",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--uris",
    "uris_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    default=None,
    help="Path to a JSON file with URI templates.",
)
@click.option(
    "--base-uri",
    default=None,
    help="Override base URI for generated resources.",
)
@click.option(
    "--service-date",
    default=None,
    help="Service date (YYYY-MM-DD) for time-only fields.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    default=None,
    help="Path to YAML configuration file.",
)
@click.option("--pretty/--compact", default=True, show_default=True, help="Pretty print output.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all warnings.")
@click.option("--strict", is_flag=True, help="Fail on any parsing errors instead of skipping.")
@click.option("--validate/--no-validate", default=True, help="Validate input before parsing.")
def main(
    input_path,
    siri_type,
    output,
    output_format,
    uris_path,
    base_uri,
    service_date,
    config_path,
    pretty,
    verbose,
    quiet,
    strict,
    validate,
):
    """Convert SIRI XML to Linked Connections."""
    # Load config file if provided
    config = None
    if config_path:
        try:
            config = load_config(config_path)
        except Exception as e:
            raise click.ClickException(f"Error loading config: {e}")

    # Setup logging
    log_verbose = verbose or (config and config.verbose)
    log_quiet = quiet or (config and config.quiet)
    logger = setup_logging(verbose=log_verbose, quiet=log_quiet)

    # Determine input
    if not input_path:
        if config and config.siri_file:
            input_path = config.siri_file
        else:
            raise click.ClickException("No input file specified. Use --input or --config.")

    # Setup URI strategy
    if uris_path:
        uri_strategy = URIStrategy.from_json(uris_path)
    elif config:
        uri_strategy = config.get_uri_strategy()
    else:
        uri_strategy = URIStrategy()

    if base_uri:
        uri_strategy.base_uri = base_uri

    # Determine output format
    fmt = output_format.lower()
    if config and config.output_format:
        fmt = config.output_format.lower()

    # Determine output path
    out_path = output
    if config and config.output_path and output == "-":
        out_path = config.output_path

    is_strict = strict or (config and config.strict)

    # Validation
    should_validate = validate
    if config:
        should_validate = config.validate

    if should_validate:
        if not validate_input(input_path, strict=is_strict):
            if is_strict:
                raise click.ClickException(f"Validation failed for: {input_path}")

    # Auto-detect SIRI type if needed
    profile = siri_type.lower()
    if profile == "auto":
        detected = detect_siri_profile(input_path)
        if detected:
            profile = detected
            if log_verbose:
                click.echo(f"Detected SIRI profile: {profile.upper()}", err=True)
        else:
            raise click.ClickException(
                "Could not detect SIRI profile. Please specify --type explicitly."
            )

    # Parse service date
    parsed_date = None
    if service_date:
        try:
            parsed_date = date.fromisoformat(service_date)
        except ValueError:
            raise click.ClickException(f"Invalid service date format: {service_date}")
    elif config and config.service_date:
        try:
            parsed_date = date.fromisoformat(config.service_date)
        except ValueError:
            pass

    # Parse based on profile
    try:
        if profile == "et":
            connections = parse_siri_et(input_path, uri_strategy, parsed_date)
            if not connections:
                click.echo("No connections generated. Check input file or service date.", err=True)
                if is_strict:
                    sys.exit(1)
            serialize_connections(connections, out_path, format_name=fmt, pretty=pretty)
            if log_verbose:
                click.echo(f"Generated {len(connections)} connections.", err=True)

        elif profile == "vm":
            positions = parse_siri_vm(input_path, uri_strategy)
            if not positions:
                click.echo("No vehicle positions found.", err=True)
                if is_strict:
                    sys.exit(1)
            # VM output as JSON-LD (custom format)
            data = vm_to_jsonld(positions, uri_strategy)
            _write_output(data, out_path, pretty)
            if log_verbose:
                click.echo(f"Generated {len(positions)} vehicle positions.", err=True)

        elif profile == "sx":
            alerts = parse_siri_sx(input_path, uri_strategy)
            if not alerts:
                click.echo("No service alerts found.", err=True)
                if is_strict:
                    sys.exit(1)
            # SX output as JSON-LD (custom format)
            data = sx_to_jsonld(alerts, uri_strategy)
            _write_output(data, out_path, pretty)
            if log_verbose:
                click.echo(f"Generated {len(alerts)} service alerts.", err=True)

        else:
            raise click.ClickException(f"Unknown SIRI profile: {profile}")

    except Exception as e:
        if is_strict:
            raise click.ClickException(f"Parsing error: {e}")
        logger.error(f"Parsing error: {e}")
        sys.exit(1)


def _write_output(data: dict, output_path: str, pretty: bool):
    """Write JSON-LD data to file or stdout."""
    content = json.dumps(data, indent=2 if pretty else None, ensure_ascii=True)
    if output_path == "-":
        print(content)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


if __name__ == "__main__":
    main(standalone_mode=True)
