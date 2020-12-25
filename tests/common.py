"""Provide test tools."""
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

CHILDREN_SERIALIZED = {
    0: {
        "values": {0: "20.0"},
        "child_id": 0,
        "child_type": 6,
        "description": "test child 0",
    }
}

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
