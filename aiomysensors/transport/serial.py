"""Provide a serial transport."""
import asyncio
from typing import Tuple

from serial_asyncio import open_serial_connection

from . import StreamTransport


class SerialTransport(StreamTransport):
    """Represent a serial transport."""

    def __init__(self, port: str, baud: int = 115200) -> None:
        """Set up serial transport."""
        super().__init__()
        self.port = port
        self.baud = baud

    async def _open_connection(
        self,
    ) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open the stream connection."""
        reader_writer_pair: Tuple[
            asyncio.StreamReader, asyncio.StreamWriter
        ] = await open_serial_connection(url=self.port, baudrate=self.baud)
        return reader_writer_pair
