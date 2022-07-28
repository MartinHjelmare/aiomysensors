"""Provide an MQTT gateway."""
import click

from aiomysensors.gateway import Gateway
from aiomysensors.transport.mqtt import MQTTClient

from .helper import run_gateway


@click.command(options_metavar="<options>")
@click.option(
    "-p",
    "--port",
    default=1883,
    show_default=True,
    type=int,
    help="Port of the MQTT broker.",
)
@click.option("-H", "--host", required=True, help="Host of the MQTT broker.")
@click.option(
    "-i",
    "--in-prefix",
    default="mygateway1-out",
    show_default=True,
    type=str,
    help="Topic in-prefix to subscribe to at the broker.",
)
@click.option(
    "-o",
    "--out-prefix",
    default="mygateway1-in",
    show_default=True,
    type=str,
    help="Topic out-prefix to publish to at the broker.",
)
def mqtt_gateway(host: str, port: int, in_prefix: str, out_prefix: str) -> None:
    """Start an MQTT gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = MQTTClient(host, port, in_prefix, out_prefix)
        gateway = Gateway(transport)
        return gateway

    run_gateway(gateway_factory)
