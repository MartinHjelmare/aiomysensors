"""Provide a CLI for aiomysensors."""

import logging
from typing import Annotated

import typer

from aiomysensors.gateway import Gateway
from aiomysensors.transport.mqtt import MQTTClient
from aiomysensors.transport.serial import SerialTransport
from aiomysensors.transport.tcp import TCPTransport

from .helper import run_gateway

cli = typer.Typer()
logging.basicConfig(level=logging.DEBUG)


@cli.command()
def mqtt_gateway(
    host: Annotated[str, typer.Option("--host", "-H", help="Host of the MQTT broker.")],
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port of the MQTT broker."),
    ] = 1883,
    in_prefix: Annotated[
        str,
        typer.Option(
            "--in-prefix",
            "-i",
            help="Topic in-prefix to subscribe to at the broker.",
        ),
    ] = "mygateway1-out",
    out_prefix: Annotated[
        str,
        typer.Option(
            "--out-prefix",
            "-o",
            help="Topic out-prefix to publish to at the broker.",
        ),
    ] = "mygateway1-in",
) -> None:
    """Start an MQTT gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = MQTTClient(host, port, in_prefix, out_prefix)
        return Gateway(transport)

    run_gateway(gateway_factory)


@cli.command()
def serial_gateway(
    port: Annotated[
        str,
        typer.Option("--port", "-p", help="Serial port of the gateway."),
    ],
    baud: Annotated[
        int,
        typer.Option("--baud", "-b", help="Baud rate of the serial connection."),
    ] = 115200,
) -> None:
    """Start a serial gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = SerialTransport(port, baud)
        return Gateway(transport)

    run_gateway(gateway_factory)


@cli.command()
def tcp_gateway(
    host: Annotated[
        str,
        typer.Option("--host", "-H", help="Host of the TCP connection."),
    ],
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port of the TCP connection."),
    ] = 5003,
) -> None:
    """Start a TCP gateway."""

    async def gateway_factory() -> Gateway:
        """Return a gateway."""
        transport = TCPTransport(host, port)
        return Gateway(transport)

    run_gateway(gateway_factory)
