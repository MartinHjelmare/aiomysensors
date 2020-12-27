"""Test the protocol."""
import time
from contextlib import ExitStack as default_context
from unittest.mock import patch

import pytest

from aiomysensors.exceptions import (
    MissingChildError,
    MissingNodeError,
    TooManyNodesError,
    UnsupportedMessageError,
)
from aiomysensors.model.message import Message
from aiomysensors.model.node import Node
from aiomysensors.model.protocol import PROTOCOL_VERSIONS
from tests.common import (
    DEFAULT_CHILD,
    DEFAULT_NODE_CHILD_SERIALIZED,
    NODE_CHILD_SERIALIZED,
    NODE_SERIALIZED,
)

# pylint: disable=too-many-arguments,unused-argument

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


@pytest.fixture(name="mock_time")
def mock_time_fixture():
    """Mock time."""
    with patch("aiomysensors.model.protocol.protocol_14.time") as mock_time:
        mock_time.localtime.return_value = time.gmtime(123456789)
        yield mock_time


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
    "command, context, node_before, values_after, writes, reboot",
    [
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            [],  # writes
            False,  # reboot
        ),  # Set message
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            ["0;255;3;0;13;\n"],  # writes
            True,  # reboot
        ),  # Set message, with node reboot true
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # values_after
            [],  # writes
            False,  # reboot
        ),  # Missing node
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            [],  # writes
            False,  # reboot
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
    reboot,
    gateway,
    message_schema,
    node_schema,
):
    """Test set command."""
    if reboot:
        for node in gateway.nodes.values():
            node.reboot = True

    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert gateway.transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, values_after, writes",
    [
        (
            Message(0, 0, 2, 0, 0),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "20.0"},  # values_after
            ["0;0;1;0;0;20.0\n"],  # writes
        ),  # Req message
        (
            Message(0, 0, 2, 0, 0),  # command
            default_context(),  # context
            DEFAULT_NODE_CHILD_SERIALIZED,  # node_before
            {},  # values_after
            [],  # writes
        ),  # Req message, with missing child value
        (
            Message(0, 0, 2, 0, 0),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # values_after
            [],  # writes
        ),  # Missing node
        (
            Message(0, 0, 2, 0, 0),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            [],  # writes
        ),  # Missing child
    ],
    indirect=["command", "node_before"],
)
async def test_req(
    command,
    context,
    node_before,
    values_after,
    writes,
    gateway,
    message_schema,
    node_schema,
):
    """Test req command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert gateway.transport.writes == writes


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
    "command, context, node_before",
    [
        (
            Message(0, 255, 4, 0, 5),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
        ),  # Missing node
        (
            Message(0, 255, 4, 0, 9999999),  # command
            pytest.raises(UnsupportedMessageError),  # context
            NODE_CHILD_SERIALIZED,  # node_before
        ),  # Unsupported message
        (
            Message(0, 255, 4, 0, 5),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
        ),  # Message without special handler
    ],
    indirect=["command", "node_before"],
)
async def test_stream(command, context, node_before, gateway, message_schema):
    """Test stream command."""
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


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, nodes_before, writes",
    [
        (
            Message(255, 255, 3, 0, 3),  # command
            default_context(),  # context
            0,  # nodes_before
            ["255;255;3;0;4;1\n"],  # writes
        ),  # Valid id request message
        (
            Message(255, 255, 3, 0, 3),  # command
            pytest.raises(TooManyNodesError),  # context
            255,  # nodes_before
            [],  # writes
        ),  # Too many nodes
    ],
    indirect=["command"],
)
async def test_internal_id_request(
    command,
    context,
    nodes_before,
    writes,
    gateway,
    message_schema,
):
    """Test internal id request command."""
    for node_id in range(nodes_before):
        gateway.nodes[node_id] = Node(node_id, 17, "1.4")

    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    assert gateway.transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, metric, writes",
    [
        (
            Message(0, 255, 3, 0, 6),  # command
            True,  # metric
            ["0;255;3;0;6;M\n"],  # writes
        ),  # metric config message
        (
            Message(0, 255, 3, 0, 6),  # command
            False,  # metric
            ["0;255;3;0;6;I\n"],  # writes
        ),  # imperial config message
    ],
    indirect=["command"],
)
async def test_internal_config(
    command,
    metric,
    writes,
    gateway,
    message_schema,
):
    """Test internal config command."""
    gateway.config.metric = metric

    async for msg in gateway.listen():
        assert message_schema.dump(msg) == command
        break

    assert gateway.transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, writes",
    [
        (
            Message(0, 255, 3, 0, 1),  # command
            ["0;255;3;0;1;123456789\n"],  # writes
        ),  # time message
    ],
    indirect=["command"],
)
async def test_internal_time(
    command,
    writes,
    gateway,
    message_schema,
    mock_time,
):
    """Test internal time command."""
    async for msg in gateway.listen():
        assert message_schema.dump(msg) == command
        break

    assert gateway.transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, battery_level",
    [
        (
            Message(0, 255, 3, 0, 0, "55"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            100,  # battery level
        ),  # Missing node
        (
            Message(0, 255, 3, 0, 0, "55"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            55,  # battery level
        ),  # battery level
    ],
    indirect=["command", "node_before"],
)
async def test_internal_battery_level(
    command,
    context,
    node_before,
    battery_level,
    gateway,
    message_schema,
):
    """Test internal battery level command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        assert node.battery_level == battery_level


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, sketch_name",
    [
        (
            Message(0, 255, 3, 0, 11, "sketch name set ok"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            "test node 0",  # sketch_name
        ),  # Missing node
        (
            Message(0, 255, 3, 0, 11, "sketch name set ok"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            "sketch name set ok",  # sketch_name
        ),  # sketch name
    ],
    indirect=["command", "node_before"],
)
async def test_internal_sketch_name(
    command,
    context,
    node_before,
    sketch_name,
    gateway,
    message_schema,
):
    """Test internal battery level command."""
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    for node in gateway.nodes.values():
        assert node.sketch_name == sketch_name
