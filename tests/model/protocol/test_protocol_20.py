"""Test protocol 2.0."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import MissingNodeError
from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

from tests.common import NODE_CHILD_SERIALIZED

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


@pytest.mark.parametrize("message_schema", SPECIFIC_PROTOCOL_VERSIONS, indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, writes",
    [
        (
            Message(0, 255, 3, 0, 21, "0"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [],  # writes
        ),  # gateway ready message
        (
            Message(0, 255, 3, 0, 21, "0"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            ["0;255;3;0;19;\n"],  # writes
        ),  # gateway ready message
    ],
    indirect=["command", "node_before"],
)
async def test_discover_response(
    command,
    context,
    node_before,
    writes,
    gateway,
    message_schema,
):
    """Test internal discover response command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    assert gateway.transport.writes == writes
