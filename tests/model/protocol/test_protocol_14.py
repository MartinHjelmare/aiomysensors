"""Test protocol 1.4."""

from collections.abc import Generator
from contextlib import AbstractContextManager
from contextlib import ExitStack as DefaultContext
import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from aiomysensors.exceptions import (
    InvalidMessageError,
    MissingChildError,
    MissingNodeError,
    TooManyNodesError,
)
from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Node
from aiomysensors.model.protocol import PROTOCOL_VERSIONS, get_protocol
from tests.common import (
    DEFAULT_CHILD,
    DEFAULT_NODE_CHILD_SERIALIZED,
    NODE_CHILD_SERIALIZED,
    NODE_SERIALIZED,
    MockTransport,
)

CHILD_PRESENTATION = dict(NODE_SERIALIZED)
CHILD_PRESENTATION["children"] = {0: DEFAULT_CHILD}


@pytest.fixture(name="mock_time")
def mock_time_fixture() -> Generator[MagicMock, None, None]:
    """Mock time."""
    with patch("aiomysensors.model.protocol.protocol_14.time") as mock_time:
        mock_time.localtime.return_value = time.gmtime(123456789)
        yield mock_time


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "node_after"),
    [
        (
            Message(0, 255, 0, 0, 17, "2.0"),  # command
            DefaultContext(),  # context
            None,  # node_before
            NODE_SERIALIZED,  # node_after
        ),  # Node presentation
        (
            Message(0, 0, 0, 0, 6, "test child 0"),  # command
            DefaultContext(),  # context
            NODE_SERIALIZED,  # node_before
            CHILD_PRESENTATION,  # node_after
        ),  # Child presentation
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
    context: AbstractContextManager,
    node_after: dict[str, Any],
    gateway: Gateway,
) -> None:
    """Test presentation command."""
    with context:
        await anext(gateway.listen())

    for _node in gateway.nodes.values():
        assert _node.to_dict() == node_after


@pytest.mark.parametrize("protocol_version", list(PROTOCOL_VERSIONS))
async def test_presentation_gateway_protocol_version(
    protocol_version: str,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test that gateway presentation sets protocol version."""
    gateway = Gateway(transport)
    message = Message(0, 255, 0, 0, 17, protocol_version)
    command = message.to_string(message_schema)
    transport.messages.append(command)
    assert gateway.protocol_version is None

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    assert gateway.protocol_version == protocol_version
    assert gateway.protocol is get_protocol(protocol_version)


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", ["1.4", "1.5"], indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "values_after", "writes", "reboot"),
    [
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            {0: "25.0"},  # values_after
            [],  # writes
            False,  # reboot
        ),  # Set message
        (
            Message(0, 0, 1, 0, 0, "25.0"),  # command
            DefaultContext(),  # context
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
    context: AbstractContextManager,
    values_after: dict[str, str],
    writes: list[str],
    reboot: bool,
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test set command."""
    if reboot:
        for node in gateway.nodes.values():
            node.reboot = True

    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        for child in node.children.values():
            assert child.values == values_after

    assert transport.writes == writes


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", ["1.4", "1.5"], indirect=True)
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
    context: AbstractContextManager,
    values_after: dict[str, str],
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


@pytest.mark.usefixtures("command")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context"),
    [
        (
            Message(0, 255, 3, 0, 2, "2.0"),  # command
            DefaultContext(),  # context
        ),  # gateway version
        (
            "0;255;3;0;9999999;\n",  # command
            pytest.raises(InvalidMessageError),  # context
        ),  # Invalid message
        (
            Message(0, 255, 3, 0, 10, ""),  # command
            DefaultContext(),  # context
        ),  # Message without special handler
    ],
    indirect=["command"],
)
async def test_internal(context: AbstractContextManager, gateway: Gateway) -> None:
    """Test internal command."""
    with context:
        await anext(gateway.listen())


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before"),
    [
        (
            Message(0, 255, 4, 0, 5),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
        ),  # Missing node
        (
            "0;255;4;0;9999999\n",  # command
            pytest.raises(InvalidMessageError),  # context
            NODE_CHILD_SERIALIZED,  # node_before
        ),  # Invalid message
        (
            Message(0, 255, 4, 0, 5),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
        ),  # Message without special handler
    ],
    indirect=["command", "node_before"],
)
async def test_stream(context: AbstractContextManager, gateway: Gateway) -> None:
    """Test stream command."""
    with context:
        await anext(gateway.listen())


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    "command",
    [Message(0, 255, 3, 0, 2, "2.0")],
    indirect=["command"],
)
async def test_internal_version(
    command: str, message_schema: MessageSchema, transport: MockTransport
) -> None:
    """Test internal version command."""
    gateway = Gateway(transport)

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    assert gateway.protocol_version == "2.0"


@pytest.mark.usefixtures("command")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "nodes_before", "writes"),
    [
        (
            Message(255, 255, 3, 0, 3),  # command
            DefaultContext(),  # context
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
    context: AbstractContextManager,
    nodes_before: int,
    writes: list[str],
    gateway: Gateway,
    transport: MockTransport,
) -> None:
    """Test internal id request command."""
    for node_id in range(nodes_before):
        gateway.nodes[node_id] = Node(
            node_id=node_id,
            node_type=17,
            protocol_version="1.4",
        )

    with context:
        await anext(gateway.listen())

    assert transport.writes == writes


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "metric", "writes"),
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
    command: str,
    metric: bool,
    writes: list[str],
    gateway: Gateway,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test internal config command."""
    gateway.config.metric = metric

    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    assert transport.writes == writes


@pytest.mark.usefixtures("mock_time")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "writes"),
    [
        (
            Message(0, 255, 3, 0, 1),  # command
            ["0;255;3;0;1;123456789\n"],  # writes
        ),  # time message
    ],
    indirect=["command"],
)
async def test_internal_time(
    command: str,
    writes: list[str],
    gateway: Gateway,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test internal time command."""
    msg = await anext(gateway.listen())

    assert msg.to_string(message_schema) == command
    assert transport.writes == writes


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "battery_level"),
    [
        (
            Message(0, 255, 3, 0, 0, "55"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            100,  # battery level
        ),  # Missing node
        (
            Message(0, 255, 3, 0, 0, "55"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            55,  # battery level
        ),  # battery level
    ],
    indirect=["command", "node_before"],
)
async def test_internal_battery_level(
    context: AbstractContextManager,
    battery_level: int,
    gateway: Gateway,
) -> None:
    """Test internal battery level command."""
    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        assert node.battery_level == battery_level


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "sketch_name"),
    [
        (
            Message(0, 255, 3, 0, 11, "sketch name set ok"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # sketch_name
        ),  # Missing node
        (
            Message(0, 255, 3, 0, 11, "sketch name set ok"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            "sketch name set ok",  # sketch_name
        ),  # sketch name
    ],
    indirect=["command", "node_before"],
)
async def test_internal_sketch_name(
    context: AbstractContextManager,
    sketch_name: str,
    gateway: Gateway,
) -> None:
    """Test internal sketch name command."""
    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        assert node.sketch_name == sketch_name


@pytest.mark.usefixtures("command", "node_before")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
@pytest.mark.parametrize(
    ("command", "context", "node_before", "sketch_version"),
    [
        (
            Message(0, 255, 3, 0, 12, "1.2.3"),  # command
            pytest.raises(MissingNodeError),  # context
            None,  # node_before
            None,  # sketch_version
        ),  # Missing node
        (
            Message(0, 255, 3, 0, 12, "1.2.3"),  # command
            DefaultContext(),  # context
            NODE_CHILD_SERIALIZED,  # node_before
            "1.2.3",  # sketch_version
        ),  # sketch version ok
    ],
    indirect=["command", "node_before"],
)
async def test_internal_sketch_version(
    context: AbstractContextManager,
    sketch_version: str,
    gateway: Gateway,
) -> None:
    """Test internal sketch version command."""
    with context:
        await anext(gateway.listen())

    for node in gateway.nodes.values():
        assert node.sketch_version == sketch_version
