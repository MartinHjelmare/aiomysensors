"""Test protocol 2.2."""
from contextlib import ExitStack as default_context

import pytest

from aiomysensors.exceptions import MissingNodeError
from aiomysensors.model.message import Message
from aiomysensors.model.node import Child, Node
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


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    "command, context, node_before, to_send, writes, second_writes, third_writes",
    [
        (
            Message(0, 255, 3, 0, 32, "1"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [Message(0, 0, 1, 0, 0, "25.0"), Message(1, 0, 1, 0, 0, "25.0")],  # to_send
            ["1;0;1;0;0;25.0\n"],  # writes
            ["0;0;1;0;0;25.0\n"],  # second writes
            [],  # third writes
        ),  # pre sleep notification
        (
            Message(0, 255, 3, 0, 32, "1"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            [Message(0, 0, 1, 0, 0, "25.0")],  # to_send
            ["0;255;3;0;19;\n", "0;0;1;0;0;25.0\n"],  # writes
            ["0;255;3;0;19;\n"],  # second writes
            ["0;255;3;0;19;\n"],  # third writes
        ),  # missing node
        (
            Message(0, 255, 3, 0, 32, "1"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [],  # to_send
            [],  # writes
            [],  # second writes
            [],  # third writes
        ),  # nothing to send
        (
            Message(0, 255, 3, 0, 24, "1"),  # command
            default_context(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [Message(0, 0, 1, 0, 0, "25.0")],  # to_send
            ["0;0;1;0;0;25.0\n"],  # writes
            [],  # second writes
            [],  # third writes
        ),  # not pre sleep notification command
    ],
    indirect=["command", "node_before"],
)
async def test_pre_sleep_notification(
    command,
    context,
    node_before,
    to_send,
    writes,
    second_writes,
    third_writes,
    gateway,
    message_schema,
):
    """Test internal pre sleep notification command."""
    # Set a node that won't send a pre sleep notification.
    gateway.nodes[1] = node = Node(1, 17, "2.2")
    node.children[0] = Child(0, 0)

    # Receive command.
    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    # Send some messages.
    for msg in to_send:
        await gateway.send(msg)

    # Check transport messages after first command and sends.
    assert gateway.transport.writes == writes
    gateway.transport.writes.clear()

    # Receive command again.
    gateway.transport.messages.append(command)

    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    # Check transport messages after second command.
    assert gateway.transport.writes == second_writes
    gateway.transport.writes.clear()

    # Receive command again.
    gateway.transport.messages.append(command)

    with context:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == command
            break

    # Check transport messages after third command.
    assert gateway.transport.writes == third_writes
