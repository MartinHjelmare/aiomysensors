"""Provide an MQTT transport."""
import asyncio
import logging
import uuid
from abc import abstractmethod
from typing import Optional, Tuple, cast

import paho.mqtt.client as mqtt
from asyncio_mqtt import Client as AsyncioClient
from asyncio_mqtt import MqttError

from ..exceptions import TransportError, TransportFailedError
from . import Transport

PAHO_MQTT_LOGGER = logging.getLogger("paho.mqtt.client")


class MQTTTransport(Transport):
    """Represent an MQTT transport."""

    def __init__(
        self, *, in_prefix: str = "mygateway1-out", out_prefix: str = "mygateway1-in"
    ) -> None:
        """Set up MQTT transport."""
        self.in_prefix = in_prefix  # prefix for topics gw -> controller
        self.out_prefix = out_prefix  # prefix for topics controller -> gw
        # topic structure:
        # The prefix can also have topic dividers.
        # prefix/node/child/type/ack/subtype : payload
        self._incoming_messages: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> None:
        """Connect the transport."""
        await self._connect()

        topics = [
            "/+/+/0/+/+",
            "/+/+/1/+/+",
            "/+/+/2/+/+",
            "/+/+/3/+/+",
            "/+/+/4/+/+",
        ]
        tasks = []

        for partial_topic in topics:
            topic = f"{self.in_prefix}{partial_topic}"
            topic_levels = topic.split("/")
            try:
                qos = int(topic_levels[-2])
            except ValueError:
                qos = 0
            tasks.append(self._subscribe(topic, qos))

        await asyncio.gather(*tasks)

    async def disconnect(self) -> None:
        """Disconnect the transport."""
        await self._disconnect()

    async def read(self) -> str:
        """Return a decoded message."""
        decoded_message: str = await self._incoming_messages.get()
        self._incoming_messages.task_done()
        return decoded_message

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""
        topic, payload, qos = self._parse_message_to_mqtt(decoded_message)

        await self._publish(topic, payload, qos)

    @abstractmethod
    async def _connect(self) -> None:
        """Connect the transport."""

    @abstractmethod
    async def _disconnect(self) -> None:
        """Disconnect the transport."""

    @abstractmethod
    async def _publish(self, topic: str, payload: str, qos: int) -> None:
        """Publish to topic."""

    @abstractmethod
    async def _subscribe(self, topic: str, qos: int) -> None:
        """Subscribe to topic."""

    def _receive(self, topic: str, payload: str, qos: int) -> None:
        """Receive an MQTT message.

        Call this method when a message is received from the MQTT broker.
        """
        decoded_message = self._parse_mqtt_to_message(topic, payload, qos)
        if decoded_message is None:
            return

        self._incoming_messages.put_nowait(decoded_message)

    def _parse_mqtt_to_message(
        self, topic: str, payload: str, qos: int
    ) -> Optional[str]:
        """Parse an MQTT topic and payload.

        Return a decoded message.
        """
        # prefix/node_id/child_id/command/ack/message_type : payload
        # The prefix can have topic dividers too.
        topic_levels = topic.split("/")
        without_prefix = topic_levels[-5:]
        prefix_end_idx = topic.index("/".join(without_prefix)) - 1
        prefix = topic[:prefix_end_idx]
        if prefix != self.in_prefix:
            return None

        if qos:
            ack = "1"
        else:
            ack = "0"
        without_prefix[3] = ack
        without_prefix.append(payload)

        return ";".join(without_prefix)

    def _parse_message_to_mqtt(self, decoded_message: str) -> Tuple[str, str, int]:
        """Parse a decoded message.

        Return an MQTT topic, payload and qos-level as a tuple.
        """
        # "node_id;child_id;command;ack;message_type;payload\n"
        partial_message, _, payload = decoded_message.rstrip().rpartition(";")
        _, _, _, ack, _ = partial_message.split(";")
        partial_topic = partial_message.replace(";", "/")

        # prefix/node_id/child_id/command/ack/message_type : payload
        return f"{self.out_prefix}/{partial_topic}", payload, int(ack)


class MQTTClient(MQTTTransport):
    """Represent an MQTT client."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        in_prefix: str = "mygateway1-out",
        out_prefix: str = "mygateway1-in",
    ) -> None:
        """Set up client."""
        super().__init__(in_prefix=in_prefix, out_prefix=out_prefix)
        self._host = host
        self._port = port
        self._client: Optional[AsyncioClient] = None
        self._incoming_task: Optional[asyncio.Task] = None

    async def _connect(self) -> None:
        """Connect to the broker."""
        self._client = AsyncioClient(
            self._host,
            self._port,
            client_id=mqtt.base62(uuid.uuid4().int, padding=22),
            logger=PAHO_MQTT_LOGGER,
            clean_session=True,
        )
        try:
            await self._client.connect(timeout=10)
        except MqttError as err:
            raise TransportError from err

        self._incoming_task = asyncio.create_task(self._handle_incoming())

    async def _disconnect(self) -> None:
        """Disconnect from the broker."""
        assert self._client
        assert self._incoming_task
        self._incoming_task.cancel()
        await self._incoming_task
        try:
            await self._client.disconnect(timeout=10)
        except MqttError:
            pass

    async def _publish(self, topic: str, payload: str, qos: int) -> None:
        """Publish to topic."""
        assert self._client
        params: dict = {"qos": qos, "retain": False, "timeout": 10.0}
        if payload:
            params["payload"] = payload

        try:
            await self._client.publish(topic, **params)
        except MqttError as err:
            raise TransportFailedError from err

    async def _subscribe(self, topic: str, qos: int) -> None:
        """Subscribe to topic."""
        assert self._client
        try:
            await self._client.subscribe(topic, qos=qos, timeout=10)
        except MqttError as err:
            raise TransportError from err

    async def _handle_incoming(self) -> None:
        """Handle incoming messages."""
        assert self._client
        try:
            async with self._client.unfiltered_messages() as messages:
                async for message in messages:
                    message = cast(mqtt.MQTTMessage, message)
                    self._receive(message.topic, message.payload.decode(), message.qos)
        except MqttError as err:
            raise TransportFailedError from err
