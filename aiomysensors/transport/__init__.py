"""Provide a MySensors transport."""
from abc import ABC, abstractmethod
from types import TracebackType

TERMINATOR = b"\n"


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

    @abstractmethod
    async def read(self) -> str:
        """Return a decoded message."""

    @abstractmethod
    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""

    # TODO: Move the async context to the Gateway instead.
    async def __aenter__(self) -> "Transport":
        """Connect to the transport."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: Exception, exc_value: str, traceback: TracebackType
    ) -> None:
        """Disconnect from the transport."""
        await self.disconnect()
