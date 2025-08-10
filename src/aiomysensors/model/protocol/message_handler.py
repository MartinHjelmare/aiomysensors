"""Provide common message handlers for the MySensors protocol."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable, Coroutine
from enum import IntEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiomysensors.gateway import Gateway, MessageBuffer
    from aiomysensors.model.message import Message, MessageSchema
    from aiomysensors.model.protocol import ProtocolType


class MessageHandlerBase:
    """Represent a base class for message handlers."""

    def __init__(
        self,
        gateway: Gateway,
        message_buffer: MessageBuffer,
        message_schema: MessageSchema,
    ) -> None:
        """Initialize the message handler base class."""
        self._gateway = gateway
        self._message_buffer = message_buffer
        self._message_schema = message_schema

    def get_message_handler(
        self,
        protocol: ProtocolType,
        message: Message,
    ) -> Callable[[Message], Coroutine[Any, Any, Message]]:
        """Return the correct message handler from the protocol."""
        command: IntEnum = protocol.Command(message.command)
        message_handler: Callable[
            [Message],
            Coroutine[Any, Any, Message],
        ] = getattr(self, f"handle_{command.name}")
        return message_handler


class IncomingMessageHandlerBase(MessageHandlerBase):
    """Represent a handler for incoming messages."""

    @abstractmethod
    async def handle_presentation(
        self,
        message: Message,
    ) -> Message:
        """Process a presentation message."""

    @abstractmethod
    async def handle_set(
        self,
        message: Message,
    ) -> Message:
        """Process a set message."""

    @abstractmethod
    async def handle_req(
        self,
        message: Message,
    ) -> Message:
        """Process a req message."""

    @abstractmethod
    async def handle_internal(
        self,
        message: Message,
    ) -> Message:
        """Process an internal message."""

    @abstractmethod
    async def handle_stream(
        self,
        message: Message,
    ) -> Message:
        """Process a stream message."""


class OutgoingMessageHandlerBase(MessageHandlerBase):
    """Represent a handler for outgoing messages."""

    async def handle_set(
        self,
        message: Message,
    ) -> None:
        """Process outgoing set messages."""
        node = self._gateway.nodes.get(message.node_id)
        if node and node.sleeping:
            self._message_buffer.set_messages[
                (message.node_id, message.child_id, message.message_type)
            ] = message

            return

        decoded_message = message.to_string(self._message_schema)

        await self._gateway.transport.write(decoded_message)

    async def handle_internal(
        self,
        message: Message,
    ) -> None:
        """Process outgoing internal messages."""
        self._message_buffer.internal_messages[
            (message.node_id, message.child_id, message.message_type)
        ] = message
