from __future__ import annotations

from datetime import date
import click

from netex2lc.jsonld import write_jsonld
from netex2lc.uri import URIStrategy
from .siri_parser import parse_siri_et


@click.command(help="Convert SIRI XML to Linked Connections JSON-LD (MVP).")
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="SIRI XML file.",
)
@click.option(
    "--type",
    "siri_type",
    type=click.Choice(["et", "vm", "sx"], case_sensitive=False),
    default="et",
    show_default=True,
    help="SIRI profile type (MVP supports ET only).",
)
@click.option(
    "--output",
    default="-",
    type=click.Path(dir_okay=False, writable=True, allow_dash=True),
    help="Output file path, or '-' for stdout.",
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
@click.option("--pretty/--compact", default=True, show_default=True)

def main(input_path, siri_type, output, uris_path, base_uri, service_date, pretty):
    if siri_type.lower() != "et":
        raise click.ClickException("Only SIRI-ET is supported in the MVP.")

    if uris_path:
        uri_strategy = URIStrategy.from_json(uris_path)
    else:
        uri_strategy = URIStrategy()

    if base_uri:
        uri_strategy.base_uri = base_uri

    parsed_date = None
    if service_date:
        parsed_date = date.fromisoformat(service_date)

    connections = parse_siri_et(input_path, uri_strategy, parsed_date)
    if not connections:
        click.echo("No connections generated. Check input file or service date.", err=True)

    write_jsonld(connections, output, pretty=pretty)


if __name__ == "__main__":
    main(standalone_mode=True)
