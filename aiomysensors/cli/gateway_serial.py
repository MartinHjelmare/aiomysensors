"""Provide a serial gateway."""
import click

from aiomysensors.gateway import Gateway
from aiomysensors.transport.serial import SerialTransport

from .helper import run_gateway


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
def serial_gateway(port: str, baud: int) -> None:
    """Start a serial gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = SerialTransport(port, baud)
        gateway = Gateway(transport)
        return gateway

    run_gateway(gateway_factory)
