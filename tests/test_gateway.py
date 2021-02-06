"""Test the gateway."""
import pytest

from aiomysensors.exceptions import InvalidMessageError
from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

# pylint: disable=unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_listen(gateway, message, message_schema, node, child):
    """Test gateway listen."""
    cmd = message_schema.dump(message)

    async with gateway:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == cmd
            break


async def test_listen_invalid_message(gateway):
    """Test gateway listen for invalid message."""
    gateway.transport.messages.append("invalid")

    async with gateway:
        with pytest.raises(InvalidMessageError):
            async for _ in gateway.listen():
                raise Exception  # This line should not be reached.


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_send(gateway, message, message_schema):
    """Test gateway send."""
    cmd = message_schema.dump(message)

    async with gateway:
        await gateway.send(message)

    assert gateway.transport.writes == [cmd]


async def test_send_invalid_message(gateway):
    """Test gateway send invalid message."""
    async with gateway:
        with pytest.raises(InvalidMessageError):
            await gateway.send("invalid")


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_unset_protocol_version(message, message_schema, node, child, transport):
    """Test gateway listen."""
    gateway = Gateway(transport)
    gateway.nodes[0] = node
    cmd = message_schema.dump(message)

    async with gateway:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == cmd
            break

    assert gateway.transport.writes == [
        message_schema.dump(Message(0, 255, 3, 0, 2, ""))
    ]
