"""Provide common fixtures."""
from unittest.mock import AsyncMock

import pytest

from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Child, Node, NodeSchema
from aiomysensors.transport import Transport


@pytest.fixture(name="message_schema")
def message_schema_fixture():
    """Return a schema."""
    return MessageSchema()


@pytest.fixture(name="node_schema")
def node_schema_fixture():
    """Return a node schema."""
    return NodeSchema()


@pytest.fixture(name="node")
def node_fixture():
    """Return a node."""
    return Node(0, 17, "2.0")


@pytest.fixture(name="child")
def child_fixture(node):
    """Return a child on a node."""
    child = node.children[0] = Child(
        0, 6, description="test child 0", values={0: "20.0"}
    )
    return child


class MockTransport(Transport):
    """Represent a mock transport."""

    def __init__(self, messages=None):
        """Set up a mock transport."""
        if messages is None:
            messages = []
        self.messages = messages

    async def connect(self) -> None:
        """Connect the transport."""

    async def disconnect(self) -> None:
        """Disconnect the transport."""

    async def listen(self) -> str:
        """Return the received message."""
        return self.messages.pop(0)

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""


@pytest.fixture(name="transport")
def transport_fixture():
    """Mock a transport."""
    messages = []
    transport = AsyncMock(wraps=MockTransport(messages), messages=messages)
    return transport


@pytest.fixture(name="message")
def message_fixture():
    """Mock a message."""
    message = Message(1, 255, 0, 0, 17, "node 1")
    return message


@pytest.fixture(name="gateway")
def gateway_fixture(message, message_schema, transport):
    """Mock a gateway."""
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)
    gateway = Gateway(transport)
    return gateway
