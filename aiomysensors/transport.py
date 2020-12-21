"""Provide a MySensors transport."""
from abc import ABC, abstractmethod
from types import TracebackType
from typing import AsyncGenerator


class Transport(ABC):
    """Represent a MySensors transport.

    Method callers should handle TransportError.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Connect the transport."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect the transport."""

    async def listen(self) -> AsyncGenerator[str, None]:
        """Listen and yield a decoded message."""
        while True:
            decoded_message = await self._listen()
            yield decoded_message

    @abstractmethod
    async def _listen(self) -> str:
        """Return the received message."""

    @abstractmethod
    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""

    async def __aenter__(self) -> "Transport":
        """Connect to the transport."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the transport."""
        await self.disconnect()
