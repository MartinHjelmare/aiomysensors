"""Test the node and child model."""
from marshmallow.exceptions import ValidationError
import pytest

from aiomysensors.exceptions import MissingChildError
from aiomysensors.model.node import Node

from tests.common import NODE_CHILD_SERIALIZED, NODE_SERIALIZED


def test_dump(child, node_schema):
    """Test dump of node."""
    node = Node(0, 17, "2.0")

    node_dump = node_schema.dump(node)

    assert node_dump == NODE_SERIALIZED

    node = Node(
        0,
        17,
        "2.0",
        children={0: child},
        sketch_name="test node 0",
        sketch_version="1.0.0",
        battery_level=100,
        heartbeat=10,
    )

    node_dump = node_schema.dump(node)

    assert node_dump == NODE_CHILD_SERIALIZED


def test_load(node_schema):
    """Test load of message."""
    node = node_schema.load(NODE_CHILD_SERIALIZED)
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


def test_add_child(node):
    """Test add child."""
    assert not node.children

    child_id = 0
    child_type = 6
    description = "test child 0"
    values = {0: "20.0"}

    node.add_child(child_id, child_type, description, values)

    assert len(node.children) == 1
    child = node.children[child_id]
    assert child.child_id == child_id
    assert child.child_type == child_type
    assert child.description == description
    assert child.values == values


def test_remove_child(node, child):
    """Test remove child."""
    assert child.child_id in node.children

    node.remove_child(child.child_id)

    assert child.child_id not in node.children

    with pytest.raises(MissingChildError) as exc:
        node.remove_child(child.child_id)

        assert exc.value.child_id == child.child_id


def test_set_child_value(node, child):
    """Test set child value."""
    child_id = child.child_id
    value_type = 0
    value = "25.0"

    assert child.values[value_type] == "20.0"

    node.set_child_value(child_id, value_type, value)

    assert len(node.children) == 1
    child = node.children[child_id]
    assert child.child_id == child_id
    assert child.values[value_type] == value


def test_set_child_value_no_child(node):
    """Test set child value without child."""
    child_id = 0
    value_type = 0
    value = "25.0"

    assert not node.children

    with pytest.raises(MissingChildError) as exc:
        node.set_child_value(child_id, value_type, value)

        assert exc.value.child_id == child_id

    assert not node.children
