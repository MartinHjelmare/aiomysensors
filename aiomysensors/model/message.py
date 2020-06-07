"""Provide a mysensors message abstraction."""
from typing import Any, Dict, Union

from marshmallow import Schema, fields, post_dump, post_load, pre_load

from .const import NODE_ID_FIELD

DELIMITER = ";"


class Message:
    """Represent a message from the gateway."""

    def __init__(
        self,
        node_id: int = 0,
        child_id: int = 0,
        command: int = 0,
        ack: int = 0,
        message_type: int = 0,
        payload: str = "",
    ) -> None:
        """Set up message."""
        self.node_id = node_id
        self.child_id = child_id
        self.command = command
        self.ack = ack
        self.message_type = message_type
        self.payload = payload

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(node_id={self.node_id}, child_id={self.child_id}, "
            f"command={self.command}, ack={self.ack}, "
            f"message_type={self.message_type}, payload={self.payload})"
        )


class MessageSchema(Schema):
    """Represent a message schema."""

    node_id = NODE_ID_FIELD
    child_id = fields.Int(required=True)
    command = fields.Int(required=True)
    ack = fields.Int(required=True)
    message_type = fields.Int(required=True)
    payload = fields.Str(required=True)

    class Meta:
        """Schema options."""

        fields = ("node_id", "child_id", "command", "ack", "message_type", "payload")
        ordered = True

    @pre_load
    def to_dict(self, in_data: str, **kwargs: Any) -> Dict[str, str]:
        """Transform message string to a dict."""
        # pylint: disable=unused-argument
        list_data = in_data.rstrip().split(DELIMITER)
        out_data = dict(zip(self.fields, list_data))
        return out_data

    @post_load
    def make_message(self, data: dict, **kwargs: Any) -> Message:
        """Make a message."""
        # pylint: disable=no-self-use, unused-argument
        return Message(**data)

    @post_dump
    def to_string(self, data: Dict[str, Union[int, str]], **kwargs: Any) -> str:
        """Serialize message from a dict to a MySensors message string."""
        # pylint: disable=unused-argument
        return f"{DELIMITER.join([str(data[field]) for field in self.fields])}\n"
