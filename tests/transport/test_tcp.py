"""Test the tcp transport."""

import asyncio
from unittest.mock import AsyncMock, call, patch

import pytest

from aiomysensors.exceptions import (
    TransportError,
    TransportFailedError,
    TransportReadError,
)
from aiomysensors.transport.tcp import TCPTransport


@pytest.fixture(name="tcp")
def tcp_fixture():
    """Mock the tcp connection."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("aiomysensors.transport.tcp.asyncio.open_connection") as open_tcp:
        open_tcp.return_value = (mock_reader, mock_writer)
        yield open_tcp


async def test_connect_disconnect(tcp):
    """Test TCP transport connect and disconnect."""
    transport = TCPTransport("1.1.1.1", 9999)

    await transport.connect()

    assert tcp.call_count == 1
    assert tcp.call_args == call(host="1.1.1.1", port=9999)

    await transport.disconnect()

    _, mock_writer = tcp.return_value
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_connect_failure(tcp):
    """Test TCP transport connect failure."""
    tcp.side_effect = OSError("Boom")
    transport = TCPTransport("1.1.1.1", 9999)

    with pytest.raises(TransportError):
        await transport.connect()


async def test_disconnect_failure(tcp):
    """Test TCP transport disconnect failure."""
    _, mock_writer = tcp.return_value
    mock_writer.wait_closed.side_effect = OSError("Boom")
    transport = TCPTransport("1.1.1.1", 9999)

    await transport.connect()
    # Disconnect error should be caught.
    await transport.disconnect()

    assert tcp.call_count == 1
    assert tcp.call_args == call(host="1.1.1.1", port=9999)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_write(tcp):
    """Test TCP transport read and write."""
    mock_reader, mock_writer = tcp.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = TCPTransport("1.1.1.1", 9999)

    await transport.connect()

    assert tcp.call_count == 1
    assert tcp.call_args == call(host="1.1.1.1", port=9999)

    read = await transport.read()
    assert read == "0;0;0;0;0;test\n"

    await transport.write(read)
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(bytes_message)

    await transport.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_failure(tcp):
    """Test TCP transport read failure."""
    mock_reader, mock_writer = tcp.return_value
    transport = TCPTransport("1.1.1.1", 9999)

    await transport.connect()

    assert tcp.call_count == 1
    assert tcp.call_args == call(host="1.1.1.1", port=9999)

    mock_reader.readuntil.side_effect = asyncio.LimitOverrunError("Boom", consumed=2)

    with pytest.raises(TransportReadError):
        await transport.read()

    mock_reader.readuntil.side_effect = asyncio.IncompleteReadError(
        partial=b"partial_test", expected=20
    )

    with pytest.raises(TransportReadError) as exc_info:
        await transport.read()

    assert exc_info.value.partial_bytes == b"partial_test"

    mock_reader.readuntil.side_effect = OSError("Boom")

    with pytest.raises(TransportFailedError):
        await transport.read()

    await transport.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_write_failure(tcp):
    """Test TCP transport write failure."""
    mock_reader, mock_writer = tcp.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = TCPTransport("1.1.1.1", 9999)

    await transport.connect()

    assert tcp.call_count == 1
    assert tcp.call_args == call(host="1.1.1.1", port=9999)

    read = await transport.read()

    mock_writer.write.side_effect = OSError("Boom")

    with pytest.raises(TransportFailedError):
        await transport.write(read)

    await transport.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
