"""Provide a MySensors node and child abstraction."""
from typing import Any, Dict, Optional

from marshmallow import Schema, fields, post_load, validate
from marshmallow.exceptions import ValidationError

from ..exceptions import AIOMySensorsInvalidMessageError, AIOMySensorsMissingChildError
from .const import NODE_ID_FIELD
from .message import Message, MessageSchema


class Node:
    """Represent a MySensors node."""

    def __init__(
        self,
        node_id: int,
        node_type: int,
        protocol_version: str,
        *,
        children: Optional[Dict[int, "Child"]] = None,
        sketch_name: str = "",
        sketch_version: str = "",
        battery_level: int = 0,
        heartbeat: int = 0,
    ) -> None:
        """Set up the node."""
        self.node_id = node_id
        self.node_type = node_type
        self.protocol_version = protocol_version
        self.children = children or {}
        self.sketch_name = sketch_name
        self.sketch_version = sketch_version
        self.battery_level = battery_level
        self.heartbeat = heartbeat
        self.reboot = False

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(node_id={self.node_id}, "
            f"node_type={self.node_type}, protocol_version={self.protocol_version}, "
            f"children={self.children}, sketch_name={self.sketch_name}, "
            f"sketch_version={self.sketch_version}, "
            f"battery_level={self.battery_level}, heartbeat={self.heartbeat})"
        )

    def add_child(
        self,
        child_id: int,
        child_type: int,
        description: str = "",
        values: Optional[Dict[int, str]] = None,
    ) -> None:
        """Create and add a child sensor."""
        self.children[child_id] = Child(
            child_id, child_type, description=description, values=values
        )

    def remove_child(self, child_id: int) -> None:
        """Remove a child sensor."""
        if child_id not in self.children:
            raise AIOMySensorsMissingChildError(child_id)
        self.children.pop(child_id)

    def set_child_value(
        self, child_id: int, value_type: int, value: str, ack: int = 0
    ) -> None:
        """Set a child sensor's value."""
        if child_id not in self.children:
            raise AIOMySensorsMissingChildError(child_id)

        command = 1
        msg = Message(
            node_id=self.node_id,
            child_id=child_id,
            command=command,
            ack=ack,
            message_type=value_type,
            payload=value,
        )
        msg_schema = MessageSchema()
        try:  # Do roundtrip to validate message
            msg_dump = msg_schema.dump(msg)
            msg = msg_schema.load(msg_dump)
        except (ValueError, ValidationError) as exc:
            raise AIOMySensorsInvalidMessageError from exc

        child = self.children[msg.child_id]
        child.values[msg.message_type] = msg.payload


class Child:
    """Represent a MySensors child sensor."""

    def __init__(
        self,
        child_id: int,
        child_type: int,
        *,
        description: str = "",
        values: Optional[Dict[int, str]] = None,
    ) -> None:
        """Set up child sensor."""
        self.child_id = child_id
        self.child_type = child_type
        self.description = description
        self.values = values or {}

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(child_id={self.child_id}, "
            f"child_type={self.child_type}, description={self.description}, "
            f"values={self.values})"
        )


class ChildSchema(Schema):
    """Represent a child sensor schema."""

    child_id = fields.Int(required=True)
    child_type = fields.Int(required=True)
    description = fields.Str()
    values = fields.Dict(keys=fields.Int(), values=fields.Str())

    @post_load
    def make_child(self, data: dict, **kwargs: Any) -> Child:
        """Make a child."""
        # pylint: disable=no-self-use, unused-argument
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

    @post_load
    def make_node(self, data: dict, **kwargs: Any) -> Node:
        """Make a node."""
        # pylint: disable=no-self-use, unused-argument
        return Node(**data)