"""Provide common protocol fixtures."""

import pytest

from aiomysensors.gateway import Gateway
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Node
from tests.common import MockTransport


@pytest.fixture(name="command")
def command_fixture(
    message_schema: MessageSchema,
    transport: MockTransport,
    request: pytest.FixtureRequest,
) -> str:
    """Add a MySensors command to the transport."""
    param: Message | str = request.param
    cmd = param.to_string(message_schema) if isinstance(param, Message) else param
    transport.messages.append(cmd)
    return cmd


@pytest.fixture(name="node_before")
def node_fixture(gateway: Gateway, request: pytest.FixtureRequest) -> Node | None:
    """Populate a node in the gateway from node data."""
    if not (node_data := request.param):
        return None
    node = Node.from_dict(node_data)
    gateway.nodes[node.node_id] = node
    return node
