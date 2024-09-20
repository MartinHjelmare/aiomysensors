"""Test the CLI for the MQTT gateway."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

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
    with patch("aiomysensors.cli.Gateway", autospec=True) as gateway_class:
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
    [
        [
            "mqtt-gateway",
            "-H test.org",
            "-i mysensors/test-out",
            "-o mysensors/test-in",
        ],
    ],
)
def test_mqtt_gateway(gateway_handler, args, error):
    """Test the MQTT gateway CLI."""
    gateway_handler.side_effect = [error, KeyboardInterrupt()]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
