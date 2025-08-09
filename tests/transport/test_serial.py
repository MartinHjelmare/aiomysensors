"""Test the serial transport."""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, call, patch

import pytest

from aiomysensors.exceptions import (
    TransportError,
    TransportFailedError,
    TransportReadError,
)
from aiomysensors.transport.serial import SerialTransport


@pytest.fixture(name="serial")
def serial_fixture() -> Generator[AsyncMock, None, None]:
    """Mock the serial connection."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("aiomysensors.transport.serial.open_serial_connection") as open_serial:
        open_serial.return_value = (mock_reader, mock_writer)
        yield open_serial


async def test_connect_disconnect(serial: AsyncMock) -> None:
    """Test serial transport connect and disconnect."""
    transport = SerialTransport("/test", 123456)

    await transport.connect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    await transport.disconnect()

    _, mock_writer = serial.return_value
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_disconnect_before_connected(serial: AsyncMock) -> None:
    """Test serial transport disconnect before connected."""
    transport = SerialTransport("/test", 123456)

    await transport.disconnect()

    assert transport.reader is None
    assert transport.writer is None
    assert serial.call_count == 0

    # Test connecting works
    await transport.connect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    await transport.disconnect()

    _, mock_writer = serial.return_value
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_connect_failure(serial: AsyncMock) -> None:
    """Test serial transport connect failure."""
    serial.side_effect = OSError("Boom")
    transport = SerialTransport("/test", 123456)

    with pytest.raises(TransportError):
        await transport.connect()


async def test_disconnect_failure(serial: AsyncMock) -> None:
    """Test serial transport disconnect failure."""
    _, mock_writer = serial.return_value
    mock_writer.wait_closed.side_effect = OSError("Boom")
    transport = SerialTransport("/test", 123456)

    await transport.connect()
    # Disconnect error should be caught.
    await transport.disconnect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_write(serial: AsyncMock) -> None:
    """Test serial transport read and write."""
    mock_reader, mock_writer = serial.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = SerialTransport("/test", 123456)

    await transport.connect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    read = await transport.read()
    assert read == "0;0;0;0;0;test\n"

    await transport.write(read)
    assert mock_writer.write.call_count == 1
    assert mock_writer.write.call_args == call(bytes_message)

    await transport.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_failure(serial: AsyncMock) -> None:
    """Test serial transport read failure."""
    mock_reader, mock_writer = serial.return_value
    transport = SerialTransport("/test", 123456)

    await transport.connect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    mock_reader.readuntil.side_effect = asyncio.LimitOverrunError("Boom", consumed=2)

    with pytest.raises(TransportReadError):
        await transport.read()

    mock_reader.readuntil.side_effect = asyncio.IncompleteReadError(
        partial=b"partial_test",
        expected=20,
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


async def test_write_failure(serial: AsyncMock) -> None:
    """Test serial transport write failure."""
    mock_reader, mock_writer = serial.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = SerialTransport("/test", 123456)

    await transport.connect()

    assert serial.call_count == 1
    assert serial.call_args == call(url="/test", baudrate=123456)

    read = await transport.read()

    mock_writer.write.side_effect = OSError("Boom")

    with pytest.raises(TransportFailedError):
        await transport.write(read)

    await transport.disconnect()

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
