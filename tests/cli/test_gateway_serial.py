"""Test the CLI for the serial gateway."""

from unittest.mock import AsyncMock

import pytest
from typer.testing import CliRunner

from aiomysensors.cli import cli
from aiomysensors.exceptions import (
    AIOMySensorsError,
    InvalidMessageError,
    MissingChildError,
    MissingNodeError,
)


@pytest.mark.parametrize(
    "error",
    [
        None,
        MissingNodeError(1),
        MissingChildError(1),
        InvalidMessageError(),
        AIOMySensorsError(),
    ],
)
@pytest.mark.parametrize(
    "args",
    [["serial-gateway", "-p", "/test"]],
)
def test_serial_gateway(
    gateway_handler: AsyncMock, args: list[str], error: Exception | None
) -> None:
    """Test the serial gateway CLI."""
    gateway_handler.side_effect = [error, KeyboardInterrupt()]
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
