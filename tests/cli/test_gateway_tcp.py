"""Test the CLI for the TCP gateway."""
from unittest.mock import patch

import pytest
from click.testing import CliRunner

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
    with patch("aiomysensors.cli.gateway_tcp.Gateway", autospec=True) as gateway_class:
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
    [["tcp-gateway", "-H", "1.1.1.1"], ["--debug", "tcp-gateway", "-H", "1.1.1.1"]],
)
def test_tcp_gateway(gateway_handler, args, error):
    """Test the tcp gateway CLI."""
    gateway_handler.side_effect = [error, KeyboardInterrupt()]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
