"""Test the protocol."""
import pytest

from aiomysensors.exceptions import MissingNodeError
from aiomysensors.model.message import Message

# pylint: disable=unused-argument

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def test_node_presentation(gateway, message_schema, transport):
    """Test a node presentation."""
    message = Message(0, 255, 0, 0, 17, "2.0")
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)

    async for msg in gateway.listen():
        assert message_schema.dump(msg) == cmd
        break

    assert gateway.nodes
    node = gateway.nodes[0]
    assert node.node_id == 0
    assert node.node_type == 17
    assert node.protocol_version == "2.0"


async def test_child_presentation(gateway, message_schema, node, transport):
    """Test a child presentation."""
    message = Message(0, 1, 0, 0, 0, "child 1")
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)

    async for msg in gateway.listen():
        assert message_schema.dump(msg) == cmd
        break

    assert gateway.nodes
    node = gateway.nodes[0]
    assert node.children
    child = node.children[1]
    assert child.child_id == 1
    assert child.child_type == 0
    assert child.description == "child 1"


async def test_presentation_missing_node(gateway, message_schema, transport):
    """Test a child presentation with missing node."""
    message = Message(0, 1, 0, 0, 0, "child 1")
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)

    with pytest.raises(MissingNodeError):
        async for _ in gateway.listen():
            raise Exception  # This line should not be reached.
