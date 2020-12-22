"""Test the gateway."""
import pytest

from aiomysensors.exceptions import AIOMySensorsInvalidMessageError

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_listen(gateway, message, message_schema):
    """Test gateway listen."""
    cmd = message_schema.dump(message)

    async with gateway.transport:
        async for msg in gateway.listen():
            assert message_schema.dump(msg) == cmd
            break


async def test_listen_invalid_message(gateway, message, message_schema):
    """Test gateway listen for invalid message."""
    cmd = message_schema.dump(message)
    gateway.transport.messages.append("invalid")

    async with gateway.transport:
        with pytest.raises(AIOMySensorsInvalidMessageError):
            async for msg in gateway.listen():
                assert message_schema.dump(msg) == cmd


async def test_send(gateway, message, message_schema):
    """Test gateway send."""
    cmd = message_schema.dump(message)

    async with gateway.transport:
        await gateway.send(message)

    assert gateway.transport.writes == [cmd]
