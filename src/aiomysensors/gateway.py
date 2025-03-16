"""Provide a gateway."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
import logging
from types import TracebackType
from typing import Self

from .model.message import Message, MessageSchema
from .model.node import Node
from .model.protocol import (
    DEFAULT_PROTOCOL_VERSION,
    ProtocolType,
    get_incoming_message_handler,
    get_outgoing_message_handler,
    get_protocol,
)
from .persistence import Persistence
from .transport import Transport

LOGGER = logging.getLogger(__package__)


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(self, transport: Transport, config: Config | None = None) -> None:
        """Set up gateway."""
        self.config = config or Config()
        self.nodes: dict[int, Node] = {}
        self.persistence: Persistence | None = None
        if self.config.persistence_file:
            self.persistence = Persistence(self.nodes, self.config.persistence_file)
        self.transport = transport
        protocol = self._protocol = get_protocol(DEFAULT_PROTOCOL_VERSION)
        self._message_schema = MessageSchema(protocol)
        self._protocol_version: str | None = None
        self._message_buffer = MessageBuffer()

    @property
    def protocol(self) -> ProtocolType:
        """Return the correct protocol."""
        return self._protocol

    @property
    def protocol_version(self) -> str | None:
        """Return the protocol version."""
        return self._protocol_version

    @protocol_version.setter
    def protocol_version(self, value: str) -> None:
        """Return the protocol version."""
        self._protocol_version = value
        protocol = self._protocol = get_protocol(self._protocol_version)
        self._message_schema = MessageSchema(protocol)

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        while True:
            decoded_message = await self.transport.read()
            message = Message.from_string(decoded_message, self._message_schema)
            message_handler = get_incoming_message_handler(self.protocol, message)
            message = await message_handler(self, message, self._message_buffer)

            yield message

    async def send(self, message: Message, *, message_buffer: bool = True) -> None:
        """Send a message."""
        # Check valid message first.
        decoded_message = message.to_string(self._message_schema)
        _message_buffer = self._message_buffer if message_buffer else None
        message_handler = get_outgoing_message_handler(self.protocol, message)
        LOGGER.debug("Sending: %s", message)
        await message_handler(self, message, _message_buffer, decoded_message)

    async def __aenter__(self) -> Self:
        """Connect to the transport."""
        if self.persistence:
            await self.persistence.load()
            await self.persistence.start()
        await self.transport.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Disconnect from the transport."""
        await self.transport.disconnect()
        if self.persistence:
            await self.persistence.stop()


@dataclass
class Config:
    """Represent the gateway config."""

    metric: bool = True
    persistence_file: str | None = None


@dataclass
class MessageBuffer:
    """Represent a sleep message buffer."""

    internal_messages: dict[tuple[int, int, int], Message] = field(default_factory=dict)
    set_messages: dict[tuple[int, int, int], Message] = field(default_factory=dict)
