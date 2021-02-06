"""Test the CLI for the TCP gateway."""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from click.testing import CliRunner

from aiomysensors.cli import cli
from aiomysensors.exceptions import AIOMySensorsError


@pytest.fixture(name="gateway_handler", autouse=True)
def gateway_handler_fixture():
    """Mock the CLI gateway handler."""
    with patch("aiomysensors.cli.gateway_tcp.handle_gateway") as handler:
        yield handler


@pytest.fixture(name="tcp", autouse=True)
def tcp_fixture():
    """Mock the TCP connection."""
    mock_reader = AsyncMock(spec=asyncio.StreamReader)
    mock_writer = AsyncMock(spec=asyncio.StreamWriter)
    with patch("aiomysensors.transport.tcp.asyncio.open_connection") as open_tcp:
        open_tcp.return_value = (mock_reader, mock_writer)
        yield open_tcp


def test_tcp_gateway():
    """Test the TCP gateway CLI."""
    runner = CliRunner()
    result = runner.invoke(cli, ["tcp-gateway", "-H", "1.1.1.1"])
    assert result.exit_code == 0


def test_tcp_gateway_debug():
    """Test the TCP gateway CLI."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "tcp-gateway", "-H", "1.1.1.1"])
    assert result.exit_code == 0


def test_tcp_error(gateway_handler):
    """Test the TCP gateway CLI with TCP error."""
    gateway_handler.side_effect = AIOMySensorsError
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "tcp-gateway", "-H", "1.1.1.1"])
    assert result.exit_code == 0


def test_keyboard_interrupt(gateway_handler):
    """Test the TCP gateway CLI with KeyboardInterrupt error."""
    gateway_handler.side_effect = KeyboardInterrupt
    runner = CliRunner()
    result = runner.invoke(cli, ["--debug", "tcp-gateway", "-H", "1.1.1.1"])
    assert result.exit_code == 0
