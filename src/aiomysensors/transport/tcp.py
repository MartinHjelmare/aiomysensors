"""Provide a TCP transport."""

import asyncio

from . import StreamTransport


class TCPTransport(StreamTransport):
    """Represent a TCP transport."""

    def __init__(self, host: str, port: int = 5003) -> None:
        """Set up TCP transport."""
        super().__init__()
        self.host = host
        self.port = port

    async def _open_connection(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open the stream connection."""
        reader_writer_pair: tuple[
            asyncio.StreamReader,
            asyncio.StreamWriter,
        ] = await asyncio.open_connection(host=self.host, port=self.port)
        return reader_writer_pair
