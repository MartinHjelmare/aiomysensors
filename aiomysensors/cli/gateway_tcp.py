"""Provide a TCP gateway."""
import click

from aiomysensors.gateway import Gateway
from aiomysensors.transport.tcp import TCPTransport

from .helper import handle_gateway, run_gateway


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
    transport = TCPTransport(host, port)
    gateway = Gateway(transport)
    run_gateway(handle_gateway, gateway)
