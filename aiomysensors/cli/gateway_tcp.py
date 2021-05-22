"""Provide a TCP gateway."""
import click

from aiomysensors.gateway import Gateway
from aiomysensors.transport.tcp import TCPTransport

from .helper import run_gateway


@click.command(options_metavar="<options>")
@click.option(
    "-p",
    "--port",
    default=5003,
    show_default=True,
    type=int,
    help="Port of the TCP connection.",
)
@click.option("-H", "--host", required=True, help="Host of the TCP connection.")
def tcp_gateway(host: str, port: int) -> None:
    """Start a TCP gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = TCPTransport(host, port)
        gateway = Gateway(transport)
        return gateway

    run_gateway(gateway_factory)
