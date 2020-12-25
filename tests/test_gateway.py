"""Test the gateway."""
import pytest

from aiomysensors.exceptions import InvalidMessageError
from aiomysensors.model.protocol import PROTOCOL_VERSIONS

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_listen(gateway, message, message_schema):
    """Test gateway listen."""
    cmd = message_schema.dump(message)

    async with gateway.transport:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == cmd
            break


async def test_listen_invalid_message(gateway):
    """Test gateway listen for invalid message."""
    gateway.transport.messages.append("invalid")

    async with gateway.transport:
        with pytest.raises(InvalidMessageError):
            async for _ in gateway.listen():
                raise Exception  # This line should not be reached.


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
async def test_send(gateway, message, message_schema):
    """Test gateway send."""
    cmd = message_schema.dump(message)

    async with gateway.transport:
        await gateway.send(message)

    assert gateway.transport.writes == [cmd]


async def test_send_invalid_message(gateway):
    """Test gateway send invalid message."""
    async with gateway.transport:
        with pytest.raises(InvalidMessageError):
            await gateway.send("invalid")
