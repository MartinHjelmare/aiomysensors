"""Test the protocol."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import MissingNodeError, UnsupportedMessageError
from aiomysensors.model.message import Message

from tests.common import NODE_SERIALIZED

# pylint: disable=unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


CHILD_PRESENTATION = dict(NODE_SERIALIZED)
CHILD_PRESENTATION["children"] = {
    0: {
        "values": {},
        "child_id": 0,
        "child_type": 6,
        "description": "test child 0",
    }
}


@pytest.fixture(name="command")
def command_fixture(message_schema, transport, request):
    """Add a MySensors command to the transport."""
    message = request.param
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)
    return cmd


@pytest.fixture(name="node")
def node_fixture(gateway, node_schema, request):
    """Populate a node in the gateway from node data."""
    node_data = request.param
    if not node_data:
        return node_data
    node = node_schema.load(node_data)
    gateway.nodes[node.node_id] = node
    return node


@pytest.mark.parametrize(
    "command, context, node, node_serialized",
    [
        (
            Message(0, 255, 0, 0, 17, "2.0"),  # command
            default_context(),  # context
            None,  # node
            NODE_SERIALIZED,  # node_serialized
        ),  # Node presentation
        (
            Message(0, 0, 0, 0, 6, "test child 0"),  # command
            default_context(),  # context
            NODE_SERIALIZED,  # node
            CHILD_PRESENTATION,  # node_serialized
        ),  # Node presentation
        (
            Message(0, 1, 0, 0, 0, "child 1"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node
            None,  # node_serialized
        ),  # Child presentation, missing node
    ],
    indirect=["command", "node"],
)
async def test_presentation(
    command,
    context,
    node,
    node_serialized,
    gateway,
    message_schema,
    node_schema,
):
    """Test presentation command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for _node in gateway.nodes.values():
        assert node_schema.dump(_node) == node_serialized


@pytest.mark.parametrize(
    "command, context",
    [
        (
            Message(0, 255, 3, 0, 2, "2.0"),  # command
            default_context(),  # context
        ),  # gateway version
        (
            Message(0, 255, 3, 0, 9999999, ""),  # command
            pytest.raises(UnsupportedMessageError),  # context
        ),  # Unsupported message
        (
            Message(0, 255, 3, 0, 10, ""),  # command
            default_context(),  # context
        ),  # Message without special handler
    ],
    indirect=["command"],
)
async def test_internal(command, context, gateway, message_schema):
    """Test internal command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break


@pytest.mark.parametrize(
    "command",
    [Message(0, 255, 3, 0, 2, "2.0")],
    indirect=["command"],
)
async def test_internal_version(command, gateway, message_schema):
    """Test internal version command."""
    assert gateway.protocol_version is None

    async for msg in gateway.listen():
        assert message_schema.dump(msg) == command
        break

    assert gateway.protocol_version == "2.0"
