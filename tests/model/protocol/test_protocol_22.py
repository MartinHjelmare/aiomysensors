"""Test protocol 2.2."""

from contextlib import AbstractContextManager
from contextlib import ExitStack as DefaultContext

import pytest

from aiomysensors.exceptions import MissingNodeError
from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message
from aiomysensors.model.node import Child, Node
from aiomysensors.model.protocol import PROTOCOL_VERSIONS
from tests.common import NODE_CHILD_SERIALIZED, MockTransport

HEARTBEAT_PAYLOAD = "1111"
PROTOCOL_VERSIONS_22 = list(PROTOCOL_VERSIONS)
PROTOCOL_VERSIONS_22.remove("1.4")
PROTOCOL_VERSIONS_22.remove("1.5")
PROTOCOL_VERSIONS_22.remove("2.0")
PROTOCOL_VERSIONS_22.remove("2.1")


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_22, indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "writes", "heartbeat"),
    [
        (
            Message(0, 255, 3, 0, 22, HEARTBEAT_PAYLOAD),  # command
            DefaultContext(),  # context
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
    context: AbstractContextManager,
    writes: list[str],
    heartbeat: int,
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test internal heartbeat response command."""
    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        assert node.heartbeat == heartbeat

    assert transport.writes == writes


@pytest.mark.usefixtures("node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_22, indirect=True)
@pytest.mark.parametrize(
    (
        "command",
        "context",
        "node_before",
        "to_send",
        "writes",
        "second_writes",
        "third_writes",
    ),
    [
        (
            Message(0, 255, 3, 0, 32, "1"),  # command
            DefaultContext(),  # context
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
            [],  # second writes
            [],  # third writes
        ),  # missing node
        (
            Message(0, 255, 3, 0, 32, "1"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [],  # to_send
            [],  # writes
            [],  # second writes
            [],  # third writes
        ),  # nothing to send
        (
            Message(0, 255, 3, 0, 24, "1"),  # command
            DefaultContext(),  # context
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
    command: str,
    context: AbstractContextManager,
    to_send: list[Message],
    writes: list[str],
    second_writes: list[str],
    third_writes: list[str],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test internal pre sleep notification command."""
    protocol_version = gateway.protocol.VERSION
    # Set a node that won't send a pre sleep notification.
    gateway.nodes[1] = node = Node(
        node_id=1,
        node_type=17,
        protocol_version=protocol_version,
    )
    node.children[0] = Child(child_id=0, child_type=0)

    # Receive command.
    with context:
        await anext(gateway.listen())

    # Send some messages.
    for msg in to_send:
        await gateway.send(msg)

    # Check transport messages after first command and sends.
    assert transport.writes == writes
    transport.writes.clear()

    # Receive command again.
    transport.messages.append(command)

    with context:
        await anext(gateway.listen())

    # Check transport messages after second command.
    assert transport.writes == second_writes
    transport.writes.clear()

    # Receive command again.
    transport.messages.append(command)

    with context:
        await anext(gateway.listen())

    # Check transport messages after third command.
    assert transport.writes == third_writes
