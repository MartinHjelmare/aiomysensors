"""Test the protocol."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import (
    MissingChildError,
    MissingNodeError,
    UnsupportedMessageError,
)
from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

from tests.common import DEFAULT_CHILD, NODE_SERIALIZED, NODE_CHILD_SERIALIZED

# pylint: disable=unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


CHILD_PRESENTATION = dict(NODE_SERIALIZED)
CHILD_PRESENTATION["children"] = {0: DEFAULT_CHILD}


@pytest.fixture(name="command")
def command_fixture(message_schema, transport, request):
    """Add a MySensors command to the transport."""
    message = request.param
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)
    return cmd


@pytest.fixture(name="node_before")
def node_fixture(gateway, node_schema, request):
    """Populate a node in the gateway from node data."""
    node_data = request.param
    if not node_data:
        return node_data
    node = node_schema.load(node_data)
    gateway.nodes[node.node_id] = node
    return node


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, node_after",
    [
        (
            Message(0, 255, 0, 0, 17, "2.0"),  # command
            default_context(),  # context
            None,  # node_before
            NODE_SERIALIZED,  # node_after
        ),  # Node presentation
        (
            Message(0, 0, 0, 0, 6, "test child 0"),  # command
            default_context(),  # context
            NODE_SERIALIZED,  # node_before
            CHILD_PRESENTATION,  # node_after
        ),  # Node presentation
        (
            Message(0, 1, 0, 0, 0, "child 1"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # node_after
        ),  # Child presentation, missing node
    ],
    indirect=["command", "node_before"],
)
async def test_presentation(
    command,
    context,
    node_before,
    node_after,
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
        assert node_schema.dump(_node) == node_after


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, values_after, writes",
    [
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            [],  # writes
        ),  # Set message
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            [],  # writes
        ),  # Set message, with node reboot true
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # values_after
            [],  # writes
        ),  # Missing node
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            [],  # writes
        ),  # Missing child
    ],
    indirect=["command", "node_before"],
)
async def test_set(
    command,
    context,
    node_before,
    values_after,
    writes,
    gateway,
    message_schema,
    node_schema,
    transport,
):
    """Test set command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
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


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command",
    [Message(0, 255, 3, 0, 2, "2.0")],
    indirect=["command"],
)
async def test_internal_version(command, gateway, message_schema):
    """Test internal version command."""
    gateway.protocol_version = None

    async for msg in gateway.listen():
        assert message_schema.dump(msg) == command
        break

    assert gateway.protocol_version == "2.0"
