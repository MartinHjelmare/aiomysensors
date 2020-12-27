"""Test the CLI for the serial gateway."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from aiomysensors.cli import cli
from aiomysensors.exceptions import AIOMySensorsError


@pytest.fixture(name="gateway_handler", autouse=True)
def gateway_handler_fixture():
    """Mock the CLI gateway handler."""
    with patch("aiomysensors.cli.gateway_serial.handle_gateway") as handler:
        yield handler


@pytest.fixture(name="serial", autouse=True)
def serial_fixture():
    """Mock the serial connection."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("aiomysensors.transport.serial.open_serial_connection") as open_serial:
        open_serial.return_value = (mock_reader, mock_writer)
        yield open_serial


def test_serial_gateway():
    """Test the serial gateway CLI."""
    runner = CliRunner()
    result = runner.invoke(cli, ["serial-gateway", "-p", "/test"])
    assert result.exit_code == 0


def test_serial_gateway_debug():
    """Test the serial gateway CLI."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "serial-gateway", "-p", "/test"])
    assert result.exit_code == 0


def test_serial_error(gateway_handler):
    """Test the serial gateway CLI with serial error."""
    gateway_handler.side_effect = AIOMySensorsError
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "serial-gateway", "-p", "/test"])
    assert result.exit_code == 0


def test_keyboard_interrupt(gateway_handler):
    """Test the serial gateway CLI with KeyboardInterrupt error."""
    gateway_handler.side_effect = KeyboardInterrupt
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "serial-gateway", "-p", "/test"])
    assert result.exit_code == 0
