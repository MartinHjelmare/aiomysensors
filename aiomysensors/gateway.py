"""Provide a gateway."""
from typing import AsyncGenerator

from marshmallow import ValidationError

from .exceptions import AIOMySensorsInvalidMessageError
from .model.message import Message, MessageSchema
from .transport import Transport


class Gateway:
    """Represent a MySensors gateway."""

    def __init__(self, transport: Transport) -> None:
        """Set up gateway."""
        self.transport = transport
        self.message_schema = MessageSchema()

    async def listen(self) -> AsyncGenerator[Message, None]:
        """Listen and yield a message."""
        async for decoded_message in self.transport.listen():
            try:
                message = self.message_schema.load(decoded_message)  # type: ignore
            except ValidationError as err:
                raise AIOMySensorsInvalidMessageError from err

            yield message

    async def send_message(self, message: Message) -> None:
        """Send a message."""
        decoded_message = self.message_schema.dump(message)
        await self.transport.write(decoded_message)
