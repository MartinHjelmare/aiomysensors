"""Test the serial transport."""
import asyncio
from unittest.mock import AsyncMock, call, patch

import pytest

from aiomysensors.exceptions import (
    TransportError,
    TransportFailedError,
    TransportReadError,
)
from aiomysensors.transport.serial import SerialTransport

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.fixture(name="serial")
def serial_fixture():
    """Mock the serial connection."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("aiomysensors.transport.serial.open_serial_connection") as open_serial:
        open_serial.return_value = (mock_reader, mock_writer)
        yield open_serial


async def test_connect_disconnect(serial):
    """Test serial transport connect and disconnect."""
    transport = SerialTransport("/test", 123456)

    async with transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)

    _, mock_writer = serial.return_value
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_connect_failure(serial):
    """Test serial transport connect failure."""
    serial.side_effect = OSError("Boom")
    transport = SerialTransport("/test", 123456)

    with pytest.raises(TransportError):
        async with transport:
            pass


async def test_disconnect_failure(serial):
    """Test serial transport disconnect failure."""
    _, mock_writer = serial.return_value
    mock_writer.wait_closed.side_effect = OSError("Boom")
    transport = SerialTransport("/test", 123456)

    async with transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)
        # Disconnect error should be caught.

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_write(serial):
    """Test serial transport read and write."""
    mock_reader, mock_writer = serial.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = SerialTransport("/test", 123456)

    async with transport as transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)

        read = await transport.read()
        assert read == "0;0;0;0;0;test\n"

        await transport.write(read)
        assert mock_writer.write.call_count == 1
        assert mock_writer.write.call_args == call(bytes_message)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_read_failure(serial):
    """Test serial transport read failure."""
    mock_reader, mock_writer = serial.return_value
    transport = SerialTransport("/test", 123456)

    async with transport as transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)

        mock_reader.readuntil.side_effect = asyncio.LimitOverrunError(
            "Boom", consumed=2
        )

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

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1


async def test_write_failure(serial):
    """Test serial transport write failure."""
    mock_reader, mock_writer = serial.return_value
    bytes_message = b"0;0;0;0;0;test\n"
    mock_reader.readuntil.return_value = bytes_message
    transport = SerialTransport("/test", 123456)

    async with transport as transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)

        read = await transport.read()

        mock_writer.write.side_effect = OSError("Boom")

        with pytest.raises(TransportFailedError):
            await transport.write(read)

    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
