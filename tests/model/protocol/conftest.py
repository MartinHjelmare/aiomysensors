"""Provide common protocol fixtures."""

from typing import cast

import pytest

from aiomysensors.gateway import Gateway
from aiomysensors.model.message import MessageSchema
from aiomysensors.model.node import Node, NodeSchema
from tests.common import MockTransport


@pytest.fixture(name="command")
def command_fixture(
    message_schema: MessageSchema,
    transport: MockTransport,
    request: pytest.FixtureRequest,
) -> str:
    """Add a MySensors command to the transport."""
    message = request.param
    cmd = cast(str, message_schema.dump(message))
    transport.messages.append(cmd)
    return cmd


@pytest.fixture(name="node_before")
def node_fixture(
    gateway: Gateway, node_schema: NodeSchema, request: pytest.FixtureRequest
) -> Node | None:
    """Populate a node in the gateway from node data."""
    if not (node_data := request.param):
        return None
    node = cast(Node, node_schema.load(node_data))
    gateway.nodes[node.node_id] = node
    return node
