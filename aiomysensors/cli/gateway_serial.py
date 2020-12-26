"""Provide a serial gateway."""
from typing import Any

import click

from aiomysensors.gateway import Gateway
from aiomysensors.transport.serial import SerialTransport

from .helper import handle_gateway, run_gateway


@click.command(options_metavar="<options>")
@click.option(
    "-b",
    "--baud",
    default=115200,
    show_default=True,
    type=int,
    help="Baud rate of the serial connection.",
)
@click.option("-p", "--port", required=True, help="Serial port of the gateway.")
def serial_gateway(**kwargs: Any) -> None:
    """Start a serial gateway."""
    transport = SerialTransport(**kwargs)
    gateway = Gateway(transport)
    run_gateway(handle_gateway, gateway)
