"""Test the protocol package."""

from aiomysensors.model.const import DEFAULT_PROTOCOL_VERSION
from aiomysensors.model.protocol import get_protocol


def test_get_protocol() -> None:
    """Test get protocol."""
    protocol = get_protocol("0.0")

    assert protocol.VERSION == DEFAULT_PROTOCOL_VERSION

    protocol = get_protocol("2.2")

    assert protocol.VERSION == "2.2"

    protocol = get_protocol("9999999999999.0")

    assert protocol.VERSION == "2.2"
