"""Provide common fixtures for the CLI."""

from unittest.mock import patch

import pytest


@pytest.fixture(name="gateway_handler")
def gateway_handler_fixture():
    """Mock the CLI gateway handler."""
    with patch("aiomysensors.cli.helper.handle_gateway") as handler:
        yield handler
