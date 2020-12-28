"""Provide a gateway."""
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Optional

from marshmallow import ValidationError

from .exceptions import InvalidMessageError
from .model.message import Message, MessageSchema
from .model.node import Node
from .model.protocol import DEFAULT_PROTOCOL_VERSION, SYSTEM_CHILD_ID, get_protocol
from .transport import Transport


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(self, transport: Transport, config: Optional["Config"] = None) -> None:
        """Set up gateway."""
        self.transport = transport
        self.config = config or Config()
        self.message_schema = MessageSchema()
        self.nodes: Dict[int, Node] = {}
        self.protocol_version: Optional[str] = None

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
        try:
            decoded_message = self.message_schema.dump(message)
        except ValidationError as err:
            raise InvalidMessageError(err, message) from err
        await self.transport.write(decoded_message)

    async def _handle_incoming(self, message: Message) -> Message:
        """Handle incoming message."""
        protocol_version = self.protocol_version or DEFAULT_PROTOCOL_VERSION
        protocol = get_protocol(protocol_version)

        command = protocol.Command(message.command)
        message_handlers = protocol.MessageHandler(protocol)
        message_handler = getattr(message_handlers, f"handle_{command.name}")
        message = await message_handler(self, message)

        if self.protocol_version is None and (
            message.command != protocol.Command.internal
            or message.message_type
            not in (protocol.Internal.I_LOG_MESSAGE, protocol.Internal.I_GATEWAY_READY)
        ):
            version_message = Message(
                child_id=SYSTEM_CHILD_ID,
                command=protocol.Command.internal,
                message_type=protocol.Internal.I_VERSION,
            )
            await self.send(version_message)

        return message


@dataclass
class Config:
    """Represent the gateway config."""

    metric: bool = True
