"""Test the CLI for the serial gateway."""
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from aiomysensors.cli import cli
from aiomysensors.exceptions import AIOMySensorsError


@pytest.fixture(name="gateway_cli", autouse=True)
def gateway_cli_fixture():
    """Mock the CLI gateway handler."""
    with patch(
        "aiomysensors.cli.gateway_serial.Gateway", autospec=True
    ) as gateway_class:
        gateway = gateway_class.return_value
        yield gateway


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
