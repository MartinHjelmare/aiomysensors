"""Test the gateway."""

import asyncio
from unittest.mock import MagicMock, call

import pytest

from aiomysensors.exceptions import InvalidMessageError
from aiomysensors.gateway import Config, Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Node
from aiomysensors.model.protocol import PROTOCOL_VERSIONS
from tests.common import MockTransport


@pytest.mark.usefixtures("node", "child")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_listen(
    gateway: Gateway,
    message: Message,
    message_schema: MessageSchema,
) -> None:
    """Test gateway listen."""
    cmd = message_schema.dump(message)

    async with gateway:
        msg = await anext(gateway.listen())

    assert message_schema.dump(msg) == cmd


async def test_listen_invalid_message(
    gateway: Gateway, transport: MockTransport
) -> None:
    """Test gateway listen for invalid message."""
    transport.messages.append("invalid")

    async with gateway:
        with pytest.raises(InvalidMessageError):
            await anext(gateway.listen())


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_send(
    gateway: Gateway,
    message: Message,
    message_schema: MessageSchema,
    transport: MockTransport,
) -> None:
    """Test gateway send."""
    cmd = message_schema.dump(message)

    async with gateway:
        await gateway.send(message)

    assert transport.writes == [cmd]


async def test_send_invalid_message(gateway: Gateway) -> None:
    """Test gateway send invalid message."""
    async with gateway:
        with pytest.raises(InvalidMessageError):
            await gateway.send("invalid")  # type: ignore[arg-type]


@pytest.mark.usefixtures("child")
@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_unset_protocol_version(
    message: Message,
    message_schema: MessageSchema,
    node: Node,
    transport: MockTransport,
) -> None:
    """Test gateway listen."""
    gateway = Gateway(transport)
    gateway.nodes[0] = node
    cmd = message_schema.dump(message)

    async with gateway:
        msg = await anext(gateway.listen())

    assert message_schema.dump(msg) == cmd
    assert transport.writes == [message_schema.dump(Message(0, 255, 3, 0, 2, ""))]


async def test_persistence(
    mock_file: MagicMock, persistence_data: str, transport: MockTransport
) -> None:
    """Test gateway persistence."""
    mock_file.read.return_value = persistence_data
    gateway = Gateway(transport, Config(persistence_file="test_path.json"))

    assert not gateway.nodes

    async with gateway:
        assert mock_file.read.call_count == 1
        assert gateway.nodes
        node = gateway.nodes.get(1)
        assert node
        assert node.battery_level == 0
        assert node.children
        child = node.children.get(1)
        assert child
        assert child.child_id == 1
        assert child.child_type == 38
        assert child.values
        value = child.values.get(49)
        assert value == "40.741894,-73.989311,12"

        await asyncio.sleep(0.1)

        # First write call done by the save task.
        assert mock_file.write.call_count == 1
        assert mock_file.write.call_args == call(persistence_data)

    # Second write call done when stopping save task.
    assert mock_file.write.call_count == 2
    assert mock_file.write.call_args == call(persistence_data)
