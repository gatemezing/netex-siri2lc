from __future__ import annotations

import sys
import click

from .jsonld import write_jsonld
from .netex_parser import parse_netex
from .uri import URIStrategy


@click.command(help="Convert NeTEx XML to Linked Connections JSON-LD (MVP).")
@click.option(
    "--input",
    "inputs",
    multiple=True,
    required=True,
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
    type=click.Choice(["jsonld"], case_sensitive=False),
    default="jsonld",
    show_default=True,
    help="Output format (MVP only supports jsonld).",
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
@click.option("--pretty/--compact", default=True, show_default=True)

def main(inputs, output, output_format, uris_path, base_uri, pretty):
    if output_format.lower() != "jsonld":
        raise click.ClickException("Only jsonld output is supported in the MVP.")

    if uris_path:
        uri_strategy = URIStrategy.from_json(uris_path)
    else:
        uri_strategy = URIStrategy()

    if base_uri:
        uri_strategy.base_uri = base_uri

    connections = parse_netex(list(inputs), uri_strategy)
    if not connections:
        click.echo("No connections generated. Check input files.", err=True)

    write_jsonld(connections, output, pretty=pretty)


if __name__ == "__main__":
    main(standalone_mode=True)
