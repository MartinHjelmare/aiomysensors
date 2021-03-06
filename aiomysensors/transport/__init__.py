"""Provide a MySensors transport."""
from abc import ABC, abstractmethod

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
