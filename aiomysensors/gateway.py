"""Provide a gateway."""
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, Optional, Tuple

from marshmallow import ValidationError

from .exceptions import InvalidMessageError
from .model.message import Message, MessageSchema
from .model.node import Node
from .model.protocol import (
    DEFAULT_PROTOCOL_VERSION,
    ProtocolType,
    SYSTEM_CHILD_ID,
    get_protocol,
)
from .transport import Transport


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(
        self,
        transport: Transport,
        config: Optional["Config"] = None,
        message_schema: Optional[MessageSchema] = None,
        nodes: Optional[Dict[int, Node]] = None,
        sleep_buffer: Optional["SleepBuffer"] = None,
    ) -> None:
        """Set up gateway."""
        self.config = config or Config()
        self.message_schema = message_schema or MessageSchema()
        self.nodes = nodes or {}
        self.protocol_version: Optional[str] = None
        self.sleep_buffer = sleep_buffer or SleepBuffer()
        self.transport = transport
        self._protocol: Optional[ProtocolType] = None

    @property
    def protocol(self) -> ProtocolType:
        """Return the correct protocol."""
        if not self._protocol:
            protocol_version = self.protocol_version or DEFAULT_PROTOCOL_VERSION
            self._protocol = get_protocol(protocol_version)

        return self._protocol

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        while True:
            decoded_message = await self.transport.read()
            try:
                message = self.message_schema.load(decoded_message)
            except ValidationError as err:
                raise InvalidMessageError(err, decoded_message) from err

            message = await self._handle_incoming(message)

            yield message

    async def send(self, message: Message) -> None:
        """Send a message."""
        # Check valid message first.
        try:
            decoded_message = self.message_schema.dump(message)
        except ValidationError as err:
            raise InvalidMessageError(err, message) from err

        node = self.nodes.get(message.node_id)
        if node and node.sleeping and message.command == self.protocol.Command.set:
            self.sleep_buffer.set_messages[
                (message.node_id, message.child_id, message.message_type)
            ] = message

            return

        await self.transport.write(decoded_message)

    async def _handle_incoming(self, message: Message) -> Message:
        """Handle incoming message."""
        command = self.protocol.Command(message.command)
        message_handlers = self.protocol.MessageHandler(self.protocol)
        message_handler = getattr(message_handlers, f"handle_{command.name}")
        message = await message_handler(self, message)

        if self.protocol_version is None and (
            message.command != self.protocol.Command.internal
            or message.message_type
            not in (
                self.protocol.Internal.I_LOG_MESSAGE,
                self.protocol.Internal.I_GATEWAY_READY,
            )
        ):
            version_message = Message(
                child_id=SYSTEM_CHILD_ID,
                command=self.protocol.Command.internal,
                message_type=self.protocol.Internal.I_VERSION,
            )
            await self.send(version_message)

        return message


@dataclass
class Config:
    """Represent the gateway config."""

    metric: bool = True


@dataclass
class SleepBuffer:
    """Represent a sleep message buffer."""

    set_messages: Dict[Tuple[int, int, int], Message] = field(default_factory=dict)
