"""Provide test tools."""
from copy import deepcopy

NODE_SERIALIZED = {
    "children": {},
    "protocol_version": "2.0",
    "sketch_version": "",
    "node_type": 17,
    "sketch_name": "",
    "node_id": 0,
    "heartbeat": 0,
    "battery_level": 0,
}

DEFAULT_CHILD = {
    "values": {},
    "child_id": 0,
    "child_type": 6,
    "description": "test child 0",
}
DEFAULT_CHILDREN_SERIALIZED = {0: DEFAULT_CHILD}
DEFAULT_NODE_CHILD_SERIALIZED = dict(NODE_SERIALIZED)
DEFAULT_NODE_CHILD_SERIALIZED["children"] = DEFAULT_CHILDREN_SERIALIZED
MOD_CHILD = deepcopy(DEFAULT_CHILD)
MOD_CHILD["values"][0] = "20.0"
CHILDREN_SERIALIZED = {0: MOD_CHILD}

NODE_CHILD_SERIALIZED = dict(NODE_SERIALIZED)
NODE_CHILD_SERIALIZED["children"] = CHILDREN_SERIALIZED
NODE_CHILD_SERIALIZED.update(
    {
        "sketch_version": "1.0.0",
        "sketch_name": "test node 0",
        "heartbeat": 10,
        "battery_level": 100,
    }
)
