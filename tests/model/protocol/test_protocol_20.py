"""Test protocol 2.0."""
import pytest

from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

# pylint: disable=too-many-arguments,unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

SPECIFIC_PROTOCOL_VERSIONS = list(PROTOCOL_VERSIONS)
SPECIFIC_PROTOCOL_VERSIONS.remove("1.4")
SPECIFIC_PROTOCOL_VERSIONS.remove("1.5")


@pytest.mark.parametrize("message_schema", SPECIFIC_PROTOCOL_VERSIONS, indirect=True)
@pytest.mark.parametrize(
    "command, writes",
    [
        (
            Message(0, 255, 3, 0, 14),  # command
            ["255;255;3;0;20;\n"],  # writes
        ),  # gateway ready message
    ],
    indirect=["command"],
)
async def test_gateway_ready(
    command,
    writes,
    gateway,
    message_schema,
):
    """Test internal gateway ready command."""
    async for msg in gateway.listen():
        assert message_schema.dump(msg) == command
        break

    assert gateway.transport.writes == writes
