"""Provide a gateway."""
from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable, Dict, Optional, Tuple

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

    def __init__(self, transport: Transport, config: Optional["Config"] = None) -> None:
        """Set up gateway."""
        self.config = config or Config()
        self.nodes: Dict[int, Node] = {}
        self.transport = transport
        self._message_schema = MessageSchema()
        self._protocol: Optional[ProtocolType] = None
        self._protocol_version: Optional[str] = None
        self._sleep_buffer = SleepBuffer()

    @property
    def protocol(self) -> ProtocolType:
        """Return the correct protocol."""
        if not self._protocol or not self.protocol_version:
            protocol_version = self.protocol_version or DEFAULT_PROTOCOL_VERSION
            self._protocol = get_protocol(protocol_version)

        return self._protocol

    @property
    def protocol_version(self) -> Optional[str]:
        """Return the protocol version."""
        return self._protocol_version

    @protocol_version.setter
    def protocol_version(self, value: str) -> None:
        """Return the protocol version."""
        self._message_schema.context[
            "protocol_version"
        ] = self._protocol_version = value

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        while True:
            decoded_message = await self.transport.read()
            try:
                message = self._message_schema.load(decoded_message)
            except ValidationError as err:
                raise InvalidMessageError(err, decoded_message) from err

            message = await self._handle_incoming(message)

            yield message

    async def send(self, message: Message, sleep_buffer: bool = True) -> None:
        """Send a message."""
        # Check valid message first.
        try:
            decoded_message = self._message_schema.dump(message)
        except ValidationError as err:
            raise InvalidMessageError(err, message) from err

        _sleep_buffer = self._sleep_buffer if sleep_buffer else None

        message_handler = self._get_message_handler(message, "OutgoingMessageHandler")
        await message_handler(self, message, _sleep_buffer, decoded_message)

    def _get_message_handler(self, message: Message, handler_name: str) -> Callable:
        """Return the correct message handler."""
        command = self.protocol.Command(message.command)
        message_handlers = getattr(self.protocol, handler_name)
        message_handler: Callable = getattr(message_handlers, f"handle_{command.name}")
        return message_handler

    async def _handle_incoming(self, message: Message) -> Message:
        """Handle incoming message."""
        message_handler = self._get_message_handler(message, "IncomingMessageHandler")
        message = await message_handler(self, message, self._sleep_buffer)

        # TODO: Move this to the protocol instead. Probably as a decorator.
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
