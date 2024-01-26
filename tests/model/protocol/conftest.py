"""Provide common protocol fixtures."""

import pytest


@pytest.fixture(name="command")
def command_fixture(message_schema, transport, request):
    """Add a MySensors command to the transport."""
    message = request.param
    cmd = message_schema.dump(message)
    transport.messages.append(cmd)
    return cmd


@pytest.fixture(name="node_before")
def node_fixture(gateway, node_schema, request):
    """Populate a node in the gateway from node data."""
    if not (node_data := request.param):
        return node_data
    node = node_schema.load(node_data)
    gateway.nodes[node.node_id] = node
    return node
