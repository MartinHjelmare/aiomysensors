"""Test protocol 2.0."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import MissingChildError, MissingNodeError
from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS
from tests.common import (
    DEFAULT_NODE_CHILD_SERIALIZED,
    NODE_CHILD_SERIALIZED,
    NODE_SERIALIZED,
)

# pylint: disable=too-many-arguments,unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

PROTOCOL_VERSIONS_2x = list(PROTOCOL_VERSIONS)
PROTOCOL_VERSIONS_2x.remove("1.4")
PROTOCOL_VERSIONS_2x.remove("1.5")


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
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
            ["0;255;3;0;19;\n"],  # writes
            False,  # reboot
        ),  # Missing node
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            ["0;255;3;0;19;\n"],  # writes
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


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
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
            ["0;255;3;0;19;\n"],  # writes
        ),  # Missing node
        (
            Message(0, 0, 2, 0, 0),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            ["0;255;3;0;19;\n"],  # writes
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


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
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


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
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
