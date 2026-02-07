"""Command-line interface for NeTEx to Linked Connections converter."""
from __future__ import annotations

import sys

import click

from .config import load_config
from .logging_config import setup_logging
from .netex_parser import parse_netex
from .serializers import serialize_connections
from .uri import URIStrategy
from .validation import validate_input


@click.command(help="Convert NeTEx XML to Linked Connections (JSON-LD, Turtle, N-Triples).")
@click.option(
    "--input",
    "inputs",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="One or more NeTEx XML files.",
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
    inputs,
    output,
    output_format,
    uris_path,
    base_uri,
    config_path,
    pretty,
    verbose,
    quiet,
    strict,
    validate,
):
    """Convert NeTEx XML to Linked Connections."""
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

    # Determine inputs
    input_files = list(inputs)
    if config and config.netex_files:
        input_files.extend(config.netex_files)

    if not input_files:
        raise click.ClickException("No input files specified. Use --input or --config.")

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

    # Validation
    should_validate = validate
    if config:
        should_validate = config.validate

    is_strict = strict or (config and config.strict)

    if should_validate:
        for path in input_files:
            if not validate_input(path, strict=is_strict):
                if is_strict:
                    raise click.ClickException(f"Validation failed for: {path}")

    # Parse
    try:
        connections = parse_netex(input_files, uri_strategy)
    except Exception as e:
        if is_strict:
            raise click.ClickException(f"Parsing error: {e}")
        logger.error(f"Parsing error: {e}")
        connections = []

    if not connections:
        click.echo("No connections generated. Check input files.", err=True)
        if is_strict:
            sys.exit(1)

    # Serialize
    try:
        serialize_connections(connections, out_path, format_name=fmt, pretty=pretty)
    except Exception as e:
        raise click.ClickException(f"Serialization error: {e}")

    if log_verbose:
        click.echo(f"Generated {len(connections)} connections.", err=True)


if __name__ == "__main__":
    main(standalone_mode=True)
