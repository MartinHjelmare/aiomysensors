"""Test the node and child model."""
import pytest
from marshmallow.exceptions import ValidationError

from aiomysensors.model.node import Child, Node, NodeSchema

NODE_SERIALIZED_FIXTURE = {
    "children": {
        0: {
            "values": {0: "20.0"},
            "child_id": 0,
            "child_type": 6,
            "description": "test child 0",
        }
    },
    "protocol_version": "2.0",
    "sketch_version": "1.0.0",
    "node_type": 17,
    "sketch_name": "test node 0",
    "node_id": 0,
    "heartbeat": 10,
    "battery_level": 100,
}

CHILD_FIXTURE = Child(0, 6, description="test child 0", values={0: "20.0"})


@pytest.fixture(name="node_schema")
def node_schema_fixture():
    """Return a node schema."""
    return NodeSchema()


def test_dump(node_schema):
    """Test dump of node."""
    node = Node(0, 17, "2.0")

    node_dump = node_schema.dump(node)

    assert node_dump == {
        "children": {},
        "protocol_version": "2.0",
        "sketch_version": "",
        "node_type": 17,
        "sketch_name": "",
        "node_id": 0,
        "heartbeat": 0,
        "battery_level": 0,
    }

    node = Node(
        0,
        17,
        "2.0",
        children={0: CHILD_FIXTURE},
        sketch_name="test node 0",
        sketch_version="1.0.0",
        battery_level=100,
        heartbeat=10,
    )

    node_dump = node_schema.dump(node)

    assert node_dump == NODE_SERIALIZED_FIXTURE


def test_load(node_schema):
    """Test load of message."""
    node = node_schema.load(NODE_SERIALIZED_FIXTURE)
    assert node.node_id == 0
    assert node.node_type == 17
    assert node.protocol_version == "2.0"
    assert node.sketch_name == "test node 0"
    assert node.sketch_version == "1.0.0"
    assert node.battery_level == 100
    assert node.heartbeat == 10
    assert node.reboot is False

    children = node.children
    assert len(children) == 1
    assert 0 in children
    child = children[0]
    assert child.child_id == 0
    assert child.child_type == 6
    assert child.description == "test child 0"
    assert child.values == {0: "20.0"}


def test_load_bad_node(node_schema):
    """Test load of bad node."""
    with pytest.raises(ValidationError):
        node_schema.load({"bad": "bad"})
