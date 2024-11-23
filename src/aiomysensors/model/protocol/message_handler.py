"""Provide common message handlers for the MySensors protocol."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiomysensors.gateway import Gateway, MessageBuffer
    from aiomysensors.model.message import Message


class IncomingMessageHandlerBase:
    """Represent a handler for incoming messages."""

    @classmethod
    @abstractmethod
    async def handle_presentation(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a presentation message."""

    @classmethod
    @abstractmethod
    async def handle_set(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a set message."""

    @classmethod
    @abstractmethod
    async def handle_req(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a req message."""

    @classmethod
    @abstractmethod
    async def handle_internal(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process an internal message."""

    @classmethod
    @abstractmethod
    async def handle_stream(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a stream message."""


class OutgoingMessageHandlerBase:
    """Represent a handler for outgoing messages."""

    @classmethod
    @abstractmethod
    async def handle_set(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer | None,
        decoded_message: str,
    ) -> None:
        """Process outgoing set messages."""

    @classmethod
    @abstractmethod
    async def handle_internal(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer | None,
        decoded_message: str,
    ) -> None:
        """Process outgoing internal messages."""
