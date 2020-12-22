"""Provide a gateway."""
from typing import AsyncGenerator, Dict

from marshmallow import ValidationError

from .exceptions import AIOMySensorsInvalidMessageError
from .model.message import Message, MessageSchema
from .model.node import Node
from .model.protocol import get_protocol
from .transport import Transport


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(self, transport: Transport) -> None:
        """Set up gateway."""
        self.transport = transport
        self.message_schema = MessageSchema()
        self.nodes: Dict[int, Node] = {}

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        while True:
            decoded_message = await self.transport.listen()
            try:
                message = self.message_schema.load(decoded_message)  # type: ignore
            except ValidationError as err:
                raise AIOMySensorsInvalidMessageError from err

            message = await self._handle_incoming(message)

            yield message

    async def send(self, message: Message) -> None:
        """Send a message."""
        decoded_message = self.message_schema.dump(message)
        await self.transport.write(decoded_message)

    async def _handle_incoming(self, message: Message) -> Message:
        """Handle incoming message."""
        protocol = get_protocol("1.4")  # TODO: Get the correct protocol

        command = protocol.Command(message.command)  # type: ignore
        message_handler = getattr(
            protocol.MessageHandler, f"handle_{command.name}"  # type: ignore
        )
        message = await message_handler(self, message)

        return message
