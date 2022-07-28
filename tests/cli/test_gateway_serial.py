"""Test the CLI for the serial gateway."""
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from aiomysensors.cli import cli
from aiomysensors.exceptions import (
    AIOMySensorsError,
    MissingChildError,
    MissingNodeError,
    UnsupportedMessageError,
)
from aiomysensors.model.message import Message


@pytest.fixture(name="gateway_cli", autouse=True)
def gateway_cli_fixture():
    """Mock the CLI gateway handler."""
    with patch(
        "aiomysensors.cli.gateway_serial.Gateway", autospec=True
    ) as gateway_class:
        gateway = gateway_class.return_value
        yield gateway


@pytest.mark.parametrize(
    "error",
    [
        None,
        MissingNodeError(1),
        MissingChildError(1),
        UnsupportedMessageError(Message()),
        AIOMySensorsError(),
    ],
)
@pytest.mark.parametrize(
    "args",
    [["serial-gateway", "-p", "/test"], ["--debug", "serial-gateway", "-p", "/test"]],
)
def test_serial_gateway(gateway_handler, args, error):
    """Test the serial gateway CLI."""
    gateway_handler.side_effect = [error, KeyboardInterrupt()]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
