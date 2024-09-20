"""Provide a MySensors node and child abstraction."""

from typing import Any

from marshmallow import Schema, fields, post_load, validate
from marshmallow.decorators import pre_load

from aiomysensors.exceptions import MissingChildError

from .const import NODE_ID_FIELD


class Node:
    """Represent a MySensors node."""

    def __init__(
        self,
        node_id: int,
        node_type: int,
        protocol_version: str,
        *,
        children: dict[int, "Child"] | None = None,
        sketch_name: str = "",
        sketch_version: str = "",
        battery_level: int = 0,
        heartbeat: int = 0,
        sleeping: bool = False,
    ) -> None:
        """Set up the node."""
        self.node_id = node_id
        self.node_type = int(node_type)
        self.protocol_version = protocol_version
        self.children = children or {}
        self.sketch_name = sketch_name
        self.sketch_version = sketch_version
        self.battery_level = battery_level
        self.heartbeat = heartbeat
        self.reboot = False
        self.sleeping = sleeping

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(node_id={self.node_id!r}, "
            f"node_type={self.node_type!r}, "
            f"protocol_version={self.protocol_version!r}, "
            f"children={self.children!r}, sketch_name={self.sketch_name!r}, "
            f"sketch_version={self.sketch_version!r}, "
            f"battery_level={self.battery_level!r}, heartbeat={self.heartbeat!r}, "
            f"sleeping={self.sleeping!r})"
        )

    def add_child(
        self,
        child_id: int,
        child_type: int,
        description: str = "",
        values: dict[int, str] | None = None,
    ) -> None:
        """Create and add a child sensor."""
        self.children[child_id] = Child(
            child_id,
            child_type,
            description=description,
            values=values,
        )

    def remove_child(self, child_id: int) -> None:
        """Remove a child sensor."""
        if child_id not in self.children:
            raise MissingChildError(child_id)
        self.children.pop(child_id)

    def set_child_value(self, child_id: int, value_type: int, value: str) -> None:
        """Set a child sensor's value."""
        if child_id not in self.children:
            raise MissingChildError(child_id)

        child = self.children[child_id]
        child.values[value_type] = value


class Child:
    """Represent a MySensors child sensor."""

    def __init__(
        self,
        child_id: int,
        child_type: int,
        *,
        description: str = "",
        values: dict[int, str] | None = None,
    ) -> None:
        """Set up child sensor."""
        self.child_id = child_id
        self.child_type = child_type
        self.description = description
        self.values = values or {}

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(child_id={self.child_id!r}, "
            f"child_type={self.child_type!r}, description={self.description!r}, "
            f"values={self.values!r})"
        )


class ChildSchema(Schema):
    """Represent a child sensor schema."""

    child_id = fields.Int(required=True)
    child_type = fields.Int(required=True)
    description = fields.Str()
    values = fields.Dict(keys=fields.Int(), values=fields.Str())

    @pre_load
    def handle_compatibility(self, data: dict, **kwargs: Any) -> dict:  # noqa: ANN401, ARG002
        """Make pymysensors data compatible with aiomysensors."""
        # Conversion of pymysensors data to aiomysensors format.
        if "id" in data:
            data["child_id"] = data.pop("id")
        if "type" in data:
            data["child_type"] = data.pop("type")

        return data

    @post_load
    def make_child(self, data: dict, **kwargs: Any) -> Child:  # noqa: ANN401, ARG002
        """Make a child."""
        return Child(**data)


class NodeSchema(Schema):
    """Represent a node schema."""

    node_id = NODE_ID_FIELD
    node_type = fields.Int(required=True)
    protocol_version = fields.Str(required=True)
    children = fields.Dict(keys=fields.Int(), values=fields.Nested(ChildSchema))
    sketch_name = fields.Str()
    sketch_version = fields.Str()
    battery_level = fields.Int(validate=validate.Range(min=0, max=100))
    heartbeat = fields.Int()
    sleeping = fields.Bool()

    @pre_load
    def handle_compatibility(self, data: dict, **kwargs: Any) -> dict:  # noqa: ANN401, ARG002
        """Make pymysensors data compatible with aiomysensors."""
        # Conversion of pymysensors data to aiomysensors format.
        if "sensor_id" in data:
            data["node_id"] = data.pop("sensor_id")
        if "type" in data:
            if data["type"] is None:
                data["type"] = 18  # Set gateway type as default.
            data["node_type"] = data.pop("type")
        if "sketch_name" in data and data["sketch_name"] is None:
            data["sketch_name"] = ""
        if "sketch_version" in data and data["sketch_version"] is None:
            data["sketch_version"] = ""

        return data

    @post_load
    def make_node(self, data: dict, **kwargs: Any) -> Node:  # noqa: ANN401, ARG002
        """Make a node."""
        return Node(**data)
