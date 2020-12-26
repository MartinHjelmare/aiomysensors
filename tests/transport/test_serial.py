"""Test the serial transport."""
import asyncio
from unittest.mock import AsyncMock, call, patch

import pytest

from aiomysensors.gateway import Gateway
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
    serial_transport = SerialTransport("/test", 123456)
    gateway = Gateway(serial_transport)

    async with gateway.transport:
        assert serial.call_count == 1
        assert serial.call_args == call(url="/test", baudrate=123456)

    _, mock_writer = serial.return_value
    assert mock_writer.close.call_count == 1
    assert mock_writer.wait_closed.call_count == 1
