"""Test the node and child model."""

from mashumaro.exceptions import MissingField
import pytest

from aiomysensors.exceptions import MissingChildError
from aiomysensors.model.node import Child, Node
from tests.common import NODE_CHILD_SERIALIZED, NODE_SERIALIZED


def test_dump(child: Child) -> None:
    """Test dump of node."""
    node = Node(node_id=0, node_type=17, protocol_version="2.0")

    node_dump = node.to_dict()

    assert node_dump == NODE_SERIALIZED

    node = Node(
        node_id=0,
        node_type=17,
        protocol_version="2.0",
        children={0: child},
        sketch_name="test node 0",
        sketch_version="1.0.0",
        battery_level=100,
    )

    node_dump = node.to_dict()

    assert node_dump == NODE_CHILD_SERIALIZED


def test_load() -> None:
    """Test load of message."""
    node = Node.from_dict(NODE_CHILD_SERIALIZED)
    assert node.node_id == 0
    assert node.node_type == 17
    assert node.protocol_version == "2.0"
    assert node.sketch_name == "test node 0"
    assert node.sketch_version == "1.0.0"
    assert node.battery_level == 100
    assert node.reboot is False

    children = node.children
    assert len(children) == 1
    assert 0 in children
    child = children[0]
    assert child.child_id == 0
    assert child.child_type == 6
    assert child.description == "test child 0"
    assert child.values == {0: "20.0"}


def test_load_bad_node() -> None:
    """Test load of bad node."""
    with pytest.raises(MissingField) as exc_info:
        Node.from_dict({"bad": "bad"})

    assert (
        str(exc_info.value) == 'Field "node_id" of type int is missing in Node instance'
    )


def test_add_child(node: Node) -> None:
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


def test_remove_child(node: Node, child: Child) -> None:
    """Test remove child."""
    assert child.child_id in node.children

    node.remove_child(child.child_id)

    assert child.child_id not in node.children

    with pytest.raises(MissingChildError) as exc:
        node.remove_child(child.child_id)

    assert exc.value.child_id == child.child_id


def test_set_child_value(node: Node, child: Child) -> None:
    """Test set child value."""
    child_id = child.child_id
    value_type = 0
    value = "25.0"

    assert child.values[value_type] == "20.0"

    child.set_value(value_type, value)

    assert len(node.children) == 1
    child = node.children[child_id]
    assert child.child_id == child_id
    assert child.values[value_type] == value
