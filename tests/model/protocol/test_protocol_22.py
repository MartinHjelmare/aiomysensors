"""Test protocol 2.2."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import MissingNodeError
from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

from tests.common import NODE_CHILD_SERIALIZED

# pylint: disable=unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

HEARTBEAT_PAYLOAD = "1111"
PROTOCOL_VERSIONS_2x = list(PROTOCOL_VERSIONS)
PROTOCOL_VERSIONS_2x.remove("1.4")
PROTOCOL_VERSIONS_2x.remove("1.5")
PROTOCOL_VERSIONS_2x.remove("2.0")
PROTOCOL_VERSIONS_2x.remove("2.1")


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, writes, heartbeat",
    [
        (
            Message(0, 255, 3, 0, 22, HEARTBEAT_PAYLOAD),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [],  # writes
            int(HEARTBEAT_PAYLOAD),  # heartbeat
        ),  # heartbeat
        (
            Message(0, 255, 3, 0, 22, HEARTBEAT_PAYLOAD),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            ["0;255;3;0;19;\n"],  # writes
            None,  # heartbeat
        ),  # missing node
    ],
    indirect=["command", "node_before"],
)
async def test_heartbeat_response(
    command,
    context,
    node_before,
    writes,
    heartbeat,
    gateway,
    message_schema,
):
    """Test internal heartbeat response command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        assert node.heartbeat == heartbeat

    assert gateway.transport.writes == writes
