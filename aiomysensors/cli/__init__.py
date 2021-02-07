"""Provide a CLI for aiomysensors."""
import logging

import click

from aiomysensors import __version__

from .gateway_mqtt import mqtt_gateway
from .gateway_serial import serial_gateway
from .gateway_tcp import tcp_gateway

SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(
    options_metavar="", subcommand_metavar="<command>", context_settings=SETTINGS
)
@click.option("--debug", is_flag=True, help="Start aiomysensors in debug mode.")
@click.version_option(__version__)
def cli(debug: bool) -> None:
    """Run aiomysensors as an app for testing purposes."""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


cli.add_command(mqtt_gateway)
cli.add_command(serial_gateway)
cli.add_command(tcp_gateway)
