"""Provide an MQTT gateway."""
import asyncio
import logging
import uuid
from typing import Optional, cast

import click
import paho.mqtt.client as mqtt
from asyncio_mqtt import Client as AsyncioClient
from asyncio_mqtt import MqttError

from aiomysensors.exceptions import TransportError, TransportFailedError
from aiomysensors.gateway import Gateway
from aiomysensors.transport.mqtt import MQTTTransport

from .helper import run_gateway

PAHO_MQTT_LOGGER = logging.getLogger("paho.mqtt.client")


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


class MQTTClient(MQTTTransport):
    """Represent an MQTT client."""

    def __init__(self, host: str, port: int, in_prefix: str, out_prefix: str) -> None:
        """Set up client."""
        super().__init__(in_prefix=in_prefix, out_prefix=out_prefix)
        self._client = AsyncioClient(
            host,
            port,
            client_id=mqtt.base62(uuid.uuid4().int, padding=22),
            logger=PAHO_MQTT_LOGGER,
            clean_session=True,
        )
        self._incoming_task: Optional[asyncio.Task] = None

    async def _connect(self) -> None:
        """Connect to the broker."""
        try:
            await self._client.connect(timeout=10)
        except MqttError as err:
            raise TransportError from err

        self._incoming_task = asyncio.create_task(self._handle_incoming())

    async def _disconnect(self) -> None:
        """Disconnect from the broker."""
        assert self._incoming_task
        self._incoming_task.cancel()
        await self._incoming_task
        try:
            await self._client.disconnect(timeout=10)
        except MqttError as err:
            raise TransportError from err

    async def _publish(self, topic: str, payload: str, qos: int) -> None:
        """Publish to topic."""
        params: dict = {"qos": qos, "retain": False, "timeout": 10.0}
        if payload:
            params["payload"] = payload

        try:
            await self._client.publish(topic, **params)
        except MqttError as err:
            raise TransportFailedError from err

    async def _subscribe(self, topic: str, qos: int) -> None:
        """Subscribe to topic."""
        try:
            await self._client.subscribe(topic, qos=qos, timeout=10)
        except MqttError as err:
            raise TransportError from err

    async def _handle_incoming(self) -> None:
        """Handle incoming messages."""
        try:
            async with self._client.unfiltered_messages() as messages:
                async for message in messages:
                    message = cast(mqtt.MQTTMessage, message)
                    self._receive(message.topic, message.payload.decode(), message.qos)
        except MqttError as err:
            raise TransportFailedError from err
