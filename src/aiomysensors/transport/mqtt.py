"""Provide an MQTT transport."""

from abc import abstractmethod
import asyncio
import contextlib
from dataclasses import dataclass
from enum import Enum
import logging
from typing import cast
import uuid

from aiomqtt import Client as AsyncioClient
from aiomqtt import MqttError

from aiomysensors.exceptions import TransportError, TransportFailedError

from . import Transport

PAHO_MQTT_LOGGER = logging.getLogger("paho.mqtt.client")


class MQTTMessageType(Enum):
    """Represent the MQTT message type."""

    ERROR = "error"
    MESSAGE = "message"


@dataclass
class ReceivedMessage:
    """Represent a received message from the broker."""

    message_type: MQTTMessageType
    message: str | None = None
    error: Exception | None = None


class MQTTTransport(Transport):
    """Represent an MQTT transport."""

    def __init__(
        self,
        *,
        in_prefix: str = "mygateway1-out",
        out_prefix: str = "mygateway1-in",
    ) -> None:
        """Set up MQTT transport."""
        self.in_prefix = in_prefix  # prefix for topics gw -> controller
        self.out_prefix = out_prefix  # prefix for topics controller -> gw
        # topic structure:
        # The prefix can also have topic dividers.
        # prefix/node/child/type/ack/subtype : payload
        self._incoming_messages: asyncio.Queue[ReceivedMessage] = asyncio.Queue()

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
        received_message = await self._incoming_messages.get()
        self._incoming_messages.task_done()
        if received_message.message_type is MQTTMessageType.ERROR:
            error = received_message.error
            if error is None:
                raise RuntimeError("Received an error message without an error.")
            raise error

        decoded_message = received_message.message
        if decoded_message is None:
            raise RuntimeError("Received a message without a message.")
        return decoded_message

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""
        topic, payload, qos = self._parse_message_to_mqtt(decoded_message)

        await self._publish(topic, payload, qos)

    @abstractmethod
    async def _connect(self) -> None:
        """Connect the transport.

        Raise TransportError if the connection failed.
        """

    @abstractmethod
    async def _disconnect(self) -> None:
        """Disconnect the transport."""

    @abstractmethod
    async def _publish(self, topic: str, payload: str, qos: int) -> None:
        """Publish to topic.

        Raise TransportError if the publish failed.
        """

    @abstractmethod
    async def _subscribe(self, topic: str, qos: int) -> None:
        """Subscribe to topic.

        Raise TransportError if the subscribe failed.
        """

    def _receive(self, topic: str, payload: str) -> None:
        """Receive an MQTT message.

        Call this method when a message is received from the MQTT broker.
        """
        decoded_message = self._parse_mqtt_to_message(topic, payload)
        message = ReceivedMessage(
            message_type=MQTTMessageType.MESSAGE,
            message=decoded_message,
        )
        self._incoming_messages.put_nowait(message)

    def _receive_error(self, error: Exception) -> None:
        """Propagate an Exception raised when receiving an MQTT message.

        Call this method when receiving a message failed.
        """
        message = ReceivedMessage(message_type=MQTTMessageType.ERROR, error=error)
        self._incoming_messages.put_nowait(message)

    @staticmethod
    def _parse_mqtt_to_message(topic: str, payload: str) -> str:
        """Parse an MQTT topic and payload.

        Return a decoded message.
        """
        # prefix/node_id/child_id/command/ack/message_type : payload
        # The prefix can have topic dividers too.
        topic_levels = topic.split("/")
        without_prefix = topic_levels[-5:]
        without_prefix.append(payload)

        return ";".join(without_prefix)

    def _parse_message_to_mqtt(self, decoded_message: str) -> tuple[str, str, int]:
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
        self._client: AsyncioClient | None = None
        self._incoming_task: asyncio.Task | None = None

    async def _connect(self) -> None:
        """Connect to the broker.

        Raise TransportError if the connection failed.
        """
        if self._client is not None or self._incoming_task is not None:
            raise RuntimeError("Client needs to disconnect before connecting again.")

        self._client = AsyncioClient(
            self._host,
            self._port,
            identifier=f"aiomysensors-{uuid.uuid4().int}",
            logger=PAHO_MQTT_LOGGER,
            clean_session=True,
        )
        try:
            await self._client.__aenter__()
        except MqttError as err:
            raise TransportError from err

        self._incoming_task = asyncio.create_task(self._handle_incoming())

    async def _disconnect(self) -> None:
        """Disconnect from the broker."""
        if not self._client or not self._incoming_task:
            raise RuntimeError("Client needs to connect before disconnecting.")

        self._incoming_task.cancel()
        await self._incoming_task
        self._incoming_task = None
        with contextlib.suppress(MqttError):
            await self._client.__aexit__(None, None, None)

        self._client = None

    async def _publish(self, topic: str, payload: str, qos: int) -> None:
        """Publish to topic.

        Raise TransportError if the publish failed.
        """
        if not self._client:
            raise RuntimeError("Client needs to connect before publishing.")

        params: dict = {"qos": qos, "retain": False, "timeout": 10}
        if payload:
            params["payload"] = payload

        try:
            await self._client.publish(topic, **params)
        except MqttError as err:
            raise TransportFailedError from err

    async def _subscribe(self, topic: str, qos: int) -> None:
        """Subscribe to topic.

        Raise TransportError if the subscribe failed.
        """
        if not self._client:
            raise RuntimeError("Client needs to connect before subscribing.")

        try:
            await self._client.subscribe(topic, qos=qos, timeout=10)
        except MqttError as err:
            raise TransportError from err

    async def _handle_incoming(self) -> None:
        """Handle incoming messages."""
        if not self._client:
            raise RuntimeError("Client not connected.")
        try:
            async for message in self._client.messages:
                payload = cast("bytes", message.payload)
                self._receive(message.topic.value, payload.decode())
        except MqttError as err:
            self._receive_error(
                TransportFailedError(f"Failed to receive message: {err}"),
            )
