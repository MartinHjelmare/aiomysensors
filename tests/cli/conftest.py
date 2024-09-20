"""Provide common fixtures for the CLI."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from aiomysensors.gateway import Gateway


@pytest.fixture(name="gateway_cli", autouse=True)
def gateway_cli_fixture() -> Generator[Gateway, None, None]:
    """Mock the CLI gateway handler."""
    with patch("aiomysensors.cli.Gateway", autospec=True) as gateway_class:
        gateway = gateway_class.return_value
        yield gateway


@pytest.fixture(name="gateway_handler")
def gateway_handler_fixture() -> Generator[AsyncMock, None, None]:
    """Mock the CLI gateway handler."""
    with patch("aiomysensors.cli.helper.handle_gateway") as handler:
        yield handler
