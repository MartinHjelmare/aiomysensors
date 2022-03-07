"""Provide a gateway."""
from dataclasses import dataclass, field
import logging
from types import TracebackType
from typing import AsyncGenerator, Dict, Optional, Tuple

from marshmallow import ValidationError

from .exceptions import InvalidMessageError
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

    def __init__(self, transport: Transport, config: Optional["Config"] = None) -> None:
        """Set up gateway."""
        self.config = config or Config()
        self.nodes: Dict[int, Node] = {}
        self.persistence: Optional[Persistence] = None
        if self.config.persistence_file:
            self.persistence = Persistence(self.nodes, self.config.persistence_file)
        self.transport = transport
        self._message_schema = MessageSchema()
        self._protocol: Optional[ProtocolType] = None
        self._protocol_version: Optional[str] = None
        self._message_buffer = MessageBuffer()

    @property
    def protocol(self) -> ProtocolType:
        """Return the correct protocol."""
        if not self._protocol:
            protocol_version = self._protocol_version or DEFAULT_PROTOCOL_VERSION
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
        self._protocol = get_protocol(self._protocol_version)

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        while True:
            decoded_message = await self.transport.read()
            try:
                message = self._message_schema.load(
                    decoded_message  # type: ignore[arg-type]
                )
            except ValidationError as err:
                raise InvalidMessageError(err, decoded_message) from err

            message_handler = get_incoming_message_handler(self.protocol, message)
            message = await message_handler(self, message, self._message_buffer)

            yield message

    async def send(self, message: Message, message_buffer: bool = True) -> None:
        """Send a message."""
        # Check valid message first.
        try:
            decoded_message: str = self._message_schema.dump(message)
        except ValidationError as err:
            raise InvalidMessageError(err, message) from err

        _message_buffer = self._message_buffer if message_buffer else None

        message_handler = get_outgoing_message_handler(self.protocol, message)
        LOGGER.debug("Sending: %s", message)
        await message_handler(self, message, _message_buffer, decoded_message)

    async def __aenter__(self) -> "Gateway":
        """Connect to the transport."""
        if self.persistence:
            await self.persistence.load()
            await self.persistence.start()
        await self.transport.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the transport."""
        await self.transport.disconnect()
        if self.persistence:
            await self.persistence.stop()


@dataclass
class Config:
    """Represent the gateway config."""

    metric: bool = True
    persistence_file: Optional[str] = None


@dataclass
class MessageBuffer:
    """Represent a sleep message buffer."""

    internal_messages: Dict[Tuple[int, int, int], Message] = field(default_factory=dict)
    set_messages: Dict[Tuple[int, int, int], Message] = field(default_factory=dict)
