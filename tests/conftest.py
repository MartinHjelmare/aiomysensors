"""Provide common fixtures."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import aiofiles
import pytest

from aiomysensors.gateway import Gateway
from aiomysensors.model.const import DEFAULT_PROTOCOL_VERSION
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.node import Child, Node, NodeSchema
from aiomysensors.model.protocol import get_protocol
from tests.common import MockTransport

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(name="message_schema")
def message_schema_fixture(request: pytest.FixtureRequest) -> MessageSchema:
    """Apply protocol version to schema."""
    if not (protocol_version := getattr(request, "param", None)):
        return MessageSchema(get_protocol(DEFAULT_PROTOCOL_VERSION))

    return MessageSchema(get_protocol(protocol_version))


@pytest.fixture(name="node_schema")
def node_schema_fixture() -> NodeSchema:
    """Return a node schema."""
    return NodeSchema()


@pytest.fixture(name="node")
def node_fixture(gateway: Gateway) -> Node:
    """Return a node."""
    node = Node(0, 17, "2.0")
    gateway.nodes[node.node_id] = node
    return node


@pytest.fixture(name="child")
def child_fixture(node: Node) -> Child:
    """Return a child on a node."""
    child = node.children[0] = Child(
        0,
        6,
        description="test child 0",
        values={0: "20.0"},
    )
    return child


@pytest.fixture(name="transport")
def transport_fixture() -> MockTransport:
    """Mock a transport."""
    messages: list[str] = []
    return MockTransport(messages)


@pytest.fixture(name="message")
def message_fixture(message_schema: MessageSchema, transport: MockTransport) -> Message:
    """Mock a message."""
    message = Message(0, 0, 1, 0, 0, "20.0")
    cmd = message.to_string(message_schema)
    transport.messages.append(cmd)
    return message


@pytest.fixture(name="gateway")
def gateway_fixture(message_schema: MessageSchema, transport: MockTransport) -> Gateway:
    """Mock a gateway."""
    gateway = Gateway(transport)
    protocol = message_schema.protocol
    gateway.protocol_version = protocol.VERSION
    return gateway


@pytest.fixture(name="mock_file")
def mock_file_fixture() -> Generator[MagicMock, None, None]:
    """Patch aiofiles."""
    mock_file = MagicMock()
    io_base = aiofiles.threadpool.AsyncBufferedIOBase  # type: ignore[attr-defined]
    aiofiles.threadpool.wrap.register(MagicMock)(  # type: ignore[attr-defined]
        lambda *args, **kwargs: io_base(*args, **kwargs),
    )

    with patch("aiofiles.threadpool.sync_open", return_value=mock_file):
        yield mock_file


@pytest.fixture(name="persistence_data", scope="session")
def persistence_data_fixture(request: pytest.FixtureRequest) -> str:
    """Return a JSON string with persistence data saved in aiomysensors."""
    fixture = "test_aiomysensors_persistence.json"
    if hasattr(request, "param") and request.param:
        fixture = request.param
    fixture_json = FIXTURES_DIR / fixture
    return fixture_json.read_text().strip()
