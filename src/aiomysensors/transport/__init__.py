"""Provide a MySensors transport."""

from abc import ABC, abstractmethod
import asyncio

from aiomysensors.exceptions import (
    TransportError,
    TransportFailedError,
    TransportReadError,
)

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


class StreamTransport(Transport):
    """Represent a stream transport."""

    def __init__(self) -> None:
        """Set up stream transport."""
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    @abstractmethod
    async def _open_connection(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open the stream connection."""

    async def connect(self) -> None:
        """Connect the transport."""
        try:
            self.reader, self.writer = await self._open_connection()
        except OSError as err:
            raise TransportError(
                f"Failed to connect to stream transport: {err}",
            ) from err

    async def disconnect(self) -> None:
        """Disconnect the transport."""
        if self.writer is None:
            return
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except OSError:
            pass

    async def read(self) -> str:
        """Return a decoded message."""
        if self.reader is None:
            raise TransportError("Not connected to stream transport.")

        try:
            read = await self.reader.readuntil(TERMINATOR)
        except asyncio.LimitOverrunError as err:
            raise TransportReadError(err) from err
        except asyncio.IncompleteReadError as err:
            raise TransportReadError(err, err.partial) from err
        except OSError as err:
            raise TransportFailedError(
                f"Failed reading from stream transport: {err}",
            ) from err

        return read.decode()

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""
        if self.writer is None:
            raise TransportError("Not connected to stream transport.")

        try:
            self.writer.write(decoded_message.encode())
            await self.writer.drain()
        except OSError as err:
            raise TransportFailedError(
                f"Failed writing to stream transport: {err}",
            ) from err
