"""Provide an MQTT transport."""
import asyncio
from abc import abstractmethod
from typing import List, Optional, Tuple

from . import Transport


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
        await self._subscribe_topics(topics)

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

    async def _subscribe_topics(self, topics: List[str]) -> None:
        """Handle subscription of topics."""
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
