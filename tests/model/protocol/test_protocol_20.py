"""Test protocol 2.0."""

from contextlib import AbstractContextManager
from contextlib import ExitStack as DefaultContext
from typing import Any

import pytest

from aiomysensors.exceptions import MissingChildError, MissingNodeError
from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Child, Node
from aiomysensors.model.protocol import PROTOCOL_VERSIONS
from tests.common import (
    DEFAULT_NODE_CHILD_SERIALIZED,
    NODE_CHILD_SERIALIZED,
    NODE_SERIALIZED,
    MockTransport,
)

PROTOCOL_VERSIONS_2x = list(PROTOCOL_VERSIONS)
PROTOCOL_VERSIONS_2x.remove("1.4")
PROTOCOL_VERSIONS_2x.remove("1.5")


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "values_after", "writes", "node_attributes"),
    [
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            [],  # writes
            {"reboot": False},  # node_attributes
        ),  # Set message
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            ["0;255;3;0;13;\n"],  # writes
            {"reboot": True},  # node_attributes
        ),  # Set message, with node reboot true
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # values_after
            ["0;255;3;0;19;\n"],  # writes
            {"reboot": False},  # node_attributes
        ),  # Missing node
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            pytest.raises(MissingChildError),  # context
            NODE_SERIALIZED,  # node_before
            None,  # values_after
            ["0;255;3;0;19;\n"],  # writes
            {"reboot": False},  # node_attributes
        ),  # Missing child
    ],
    indirect=["command", "node_before"],
)
async def test_set(
    context: AbstractContextManager,
    values_after: dict[int, str],
    writes: list[str],
    node_attributes: dict[str, Any],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test set command."""
    for attribute, value in node_attributes.items():
        for node in gateway.nodes.values():
            setattr(node, attribute, value)

    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert transport.writes == writes


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "values_after", "writes"),
    [
        (
            Message(0, 0, 2, 0, 0),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "20.0"},  # values_after
            ["0;0;1;0;0;20.0\n"],  # writes
        ),  # Req message
        (
            Message(0, 0, 2, 0, 0),  # command
            DefaultContext(),  # context
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
    context: AbstractContextManager,
    values_after: dict[int, str],
    writes: list[str],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test req command."""
    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert transport.writes == writes


@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    ("command", "writes"),
    [
        (
            Message(0, 255, 3, 0, 14),  # command
            ["255;255;3;0;20;\n"],  # writes
        ),  # gateway ready message
    ],
    indirect=["command"],
)
async def test_gateway_ready(
    command: str,
    writes: list[str],
    gateway: Gateway,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test internal gateway ready command."""
    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    assert transport.writes == writes


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "writes"),
    [
        (
            Message(0, 255, 3, 0, 21, "0"),  # command
            DefaultContext(),  # context
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
    context: AbstractContextManager,
    writes: list[str],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test internal discover response command."""
    with context:
        await anext(gateway.listen())

    assert transport.writes == writes


@pytest.mark.usefixtures("node_before")
@pytest.mark.parametrize("message_schema", ["2.0", "2.1"], indirect=True)
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
            Message(0, 255, 3, 0, 22, "1"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            [Message(0, 0, 1, 0, 0, "25.0"), Message(1, 0, 1, 0, 0, "25.0")],  # to_send
            ["1;0;1;0;0;25.0\n"],  # writes
            ["0;0;1;0;0;25.0\n"],  # second writes
            [],  # third writes
        ),  # heartbeat
        (
            Message(0, 255, 3, 0, 22, "1"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            [Message(0, 0, 1, 0, 0, "25.0")],  # to_send
            ["0;255;3;0;19;\n", "0;0;1;0;0;25.0\n"],  # writes
            [],  # second writes
            [],  # third writes
        ),  # missing node
        (
            Message(0, 255, 3, 0, 22, "1"),  # command
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
        ),  # not heartbeat command
    ],
    indirect=["command", "node_before"],
)
async def test_heartbeat_response(
    command: str,
    context: AbstractContextManager,
    to_send: list[Message],
    writes: list[str],
    second_writes: list[str],
    third_writes: list[str],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test internal heartbeat response command."""
    # Set a node that won't send a heartbeat.
    gateway.nodes[1] = node = Node(node_id=1, node_type=17, protocol_version="2.0")
    node.children[0] = Child(child_id=0, child_type=0)

    # Receive command.
    with context:
        msg = await anext(gateway.listen())

    # Send some messages.
    for msg in to_send:
        await gateway.send(msg)

    # Check transport messages after first command and sends.
    assert transport.writes == writes
    transport.writes.clear()

    # Receive command again.
    transport.messages.append(command)

    with context:
        msg = await anext(gateway.listen())

    # Check transport messages after second command.
    assert transport.writes == second_writes
    transport.writes.clear()

    # Receive command again.
    transport.messages.append(command)

    with context:
        msg = await anext(gateway.listen())

    # Check transport messages after third command.
    assert transport.writes == third_writes


@pytest.mark.usefixtures("node_before")
@pytest.mark.parametrize("message_schema", PROTOCOL_VERSIONS_2x, indirect=True)
@pytest.mark.parametrize(
    (
        "command",
        "node_before",
        "writes",
        "second_writes",
        "third_writes",
        "fourth_writes",
    ),
    [
        (
            Message(1, 0, 1, 0, 2, "1"),  # command
            None,  # node_before
            ["1;255;3;0;19;\n"],  # writes
            [],  # second writes
            ["1;255;3;0;19;\n"],  # third writes
            [],  # fourth writes
        ),  # missing node
    ],
    indirect=["command", "node_before"],
)
async def test_missing_node(
    command: str,
    writes: list[str],
    second_writes: list[str],
    third_writes: list[str],
    fourth_writes: list[str],
    gateway: Gateway,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test missing node handling."""
    protocol = message_schema.protocol
    assert not gateway.nodes

    # Receive command for a missing node.
    with pytest.raises(MissingNodeError):
        await anext(gateway.listen())

    # Check transport messages after first command.
    assert transport.writes == writes
    transport.writes.clear()

    # Receive command again.
    transport.messages.append(command)

    with pytest.raises(MissingNodeError):
        await anext(gateway.listen())

    # Check transport messages after second command.
    assert transport.writes == second_writes
    transport.writes.clear()

    # Receive a presentation of the node.
    presentation_command = f"1;255;0;0;17;{protocol.VERSION}\n"
    transport.messages.append(presentation_command)

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == presentation_command
    assert gateway.nodes
    assert gateway.nodes[1]
    node = gateway.nodes[1]
    assert not node.children

    # Receive command again.
    transport.messages.append(command)

    with pytest.raises(MissingChildError):
        msg = await anext(gateway.listen())

    # Check transport messages after third command.
    assert transport.writes == third_writes
    transport.writes.clear()

    # Receive a presentation of the child.
    presentation_command = "1;0;0;0;3;Test Child\n"
    transport.messages.append(presentation_command)

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == presentation_command
    assert gateway.nodes
    assert gateway.nodes[1]
    node = gateway.nodes[1]
    assert node.children
    assert node.children[0]

    # Receive command again.
    transport.messages.append(command)

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    # Check transport messages after fourth command.
    assert transport.writes == fourth_writes

    assert gateway.nodes
    assert gateway.nodes[1]
    node = gateway.nodes[1]
    assert node.children
    child = node.children[0]
    assert child.values[2] == "1"
