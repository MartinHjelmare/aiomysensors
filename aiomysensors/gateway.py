"""Provide a gateway."""
from typing import AsyncGenerator, Dict, Optional

from marshmallow import ValidationError

from .exceptions import InvalidMessageError
from .model.message import Message, MessageSchema
from .model.node import Node
from .model.const import SYSTEM_CHILD_ID
from .model.protocol import DEFAULT_PROTOCOL_VERSION, get_protocol
from .transport import Transport


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(self, transport: Transport) -> None:
        """Set up gateway."""
        self.transport = transport
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
                raise InvalidMessageError from err

            message = await self._handle_incoming(message)

            yield message

    async def send(self, message: Message) -> None:
        """Send a message."""
        try:
            decoded_message = self.message_schema.dump(message)
        except ValidationError as err:
            raise InvalidMessageError from err
        await self.transport.write(decoded_message)

    async def _handle_incoming(self, message: Message) -> Message:
        """Handle incoming message."""
        protocol_version = self.protocol_version or DEFAULT_PROTOCOL_VERSION
        protocol = get_protocol(protocol_version)

        command = protocol.Command(message.command)  # type: ignore
        message_handler = getattr(
            protocol.MessageHandler, f"handle_{command.name}"  # type: ignore
        )
        message = await message_handler(self, message)

        if self.protocol_version is None:
            version_message = Message(
                child_id=SYSTEM_CHILD_ID,
                command=protocol.Command.internal,  # type: ignore
                message_type=protocol.Internal.I_VERSION,  # type: ignore
            )
            await self.send(version_message)

        return message
