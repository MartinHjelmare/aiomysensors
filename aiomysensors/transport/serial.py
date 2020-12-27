"""Provide a serial transport."""
import asyncio
from typing import Optional

from serial_asyncio import open_serial_connection

from ..exceptions import TransportError, TransportFailedError, TransportReadError
from . import TERMINATOR, Transport


class SerialTransport(Transport):
    """Represent a serial transport."""

    def __init__(self, port: str, baud: int = 115200) -> None:
        """Set up serial transport."""
        self.port = port
        self.baud = baud
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        """Connect the transport."""
        try:
            self.reader, self.writer = await open_serial_connection(
                url=self.port, baudrate=self.baud
            )
        except OSError as err:
            raise TransportError(
                f"Failed to connect to serial transport: {err}"
            ) from err

    async def disconnect(self) -> None:
        """Disconnect the transport."""
        assert self.writer is not None
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except OSError:
            pass

    async def read(self) -> str:
        """Return a decoded message."""
        assert self.reader is not None

        try:
            read = await self.reader.readuntil(TERMINATOR)
        except asyncio.LimitOverrunError as err:
            raise TransportReadError(err) from err
        except asyncio.IncompleteReadError as err:
            raise TransportReadError(err, err.partial) from err
        except OSError as err:
            raise TransportFailedError(
                f"Failed reading from serial transport: {err}"
            ) from err

        return read.decode()

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""
        assert self.writer is not None

        try:
            self.writer.write(decoded_message.encode())
            await self.writer.drain()
        except OSError as err:
            raise TransportFailedError(
                f"Failed writing to serial transport: {err}"
            ) from err
