"""Provide common fixtures."""
from typing import List

import pytest

from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Child, Node, NodeSchema
from aiomysensors.transport import Transport


@pytest.fixture(name="message_schema")
def message_schema_fixture(request):
    """Apply protocol version to schema."""
    message_schema = MessageSchema()
    protocol_version = getattr(request, "param", None)
    if not protocol_version:
        return message_schema

    message_schema.context["protocol_version"] = protocol_version
    return message_schema


@pytest.fixture(name="node_schema")
def node_schema_fixture():
    """Return a node schema."""
    return NodeSchema()


@pytest.fixture(name="node")
def node_fixture(gateway):
    """Return a node."""
    node = Node(0, 17, "2.0")
    gateway.nodes[node.node_id] = node
    return node


@pytest.fixture(name="child")
def child_fixture(node):
    """Return a child on a node."""
    child = node.children[0] = Child(
        0, 6, description="test child 0", values={0: "20.0"}
    )
    return child


class MockTransport(Transport):
    """Represent a mock transport."""

    def __init__(self, messages: List[str]):
        """Set up a mock transport."""
        self.messages = messages
        self.writes: List[str] = []

    async def connect(self) -> None:
        """Connect the transport."""

    async def disconnect(self) -> None:
        """Disconnect the transport."""

    async def read(self) -> str:
        """Return the received message."""
        return self.messages.pop(0)

    async def write(self, decoded_message: str) -> None:
        """Write a decoded message to the transport."""
        self.writes.append(decoded_message)


@pytest.fixture(name="transport")
def transport_fixture():
    """Mock a transport."""
    messages = []
    transport = MockTransport(messages)
    return transport


@pytest.fixture(name="message")
def message_fixture(message_schema, transport):
    """Mock a message."""
    message = Message(0, 0, 1, 0, 0, "20.0")
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)
    return message


@pytest.fixture(name="gateway")
def gateway_fixture(message_schema, transport):
    """Mock a gateway."""
    gateway = Gateway(transport)
    gateway.protocol_version = message_schema.context.get("protocol_version", "1.4")
    return gateway
