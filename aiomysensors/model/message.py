"""Provide a mysensors message abstraction."""
import logging
from typing import Any, Dict, Union

from marshmallow import Schema, fields, post_dump, post_load, pre_load, validate

from ..exceptions import AIOMySensorsMessageError

_LOGGER = logging.getLogger(__name__)

BROADCAST_ID = 255
DELIMITER = ";"


class Message:
    """Represent a message from the gateway."""

    # pylint: disable=too-few-public-methods

    def __init__(self, **data: Any) -> None:
        """Set up message."""
        self.node_id: int = data.get("node_id", 0)
        self.child_id: int = data.get("child_id", 0)
        self.command: int = data.get("command", 0)
        self.ack: int = data.get("ack", 0)
        self.type: int = data.get("type", 0)
        self.payload: str = data.get("payload", "")

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(node_id={self.node_id}, child_id={self.child_id}, "
            f"command={self.command}, ack={self.ack}, type={self.type}, "
            f"payload={self.payload})"
        )


class MessageSchema(Schema):
    """Represent a message schema."""

    node_id = fields.Int(
        required=True,
        validate=validate.Range(
            min=0, max=BROADCAST_ID, error="Not valid node_id: {input}",
        ),
    )
    child_id = fields.Int(required=True)
    command = fields.Int(required=True)
    ack = fields.Int(required=True)
    type = fields.Int(required=True)
    payload = fields.Str(required=True)

    class Meta:
        """Schema options."""

        # pylint: disable=too-few-public-methods

        fields = ("node_id", "child_id", "command", "ack", "type", "payload")
        ordered = True

    @pre_load
    def to_dict(self, in_data: str, **kwargs: Any) -> Dict[str, str]:
        """Transform message string to a dict."""
        # pylint: disable=unused-argument
        try:
            list_data = in_data.rstrip().split(DELIMITER)
            out_data = dict(zip(self.fields, list_data))
        except ValueError as exc:
            _LOGGER.warning(
                "Error decoding message from gateway, bad data received: %s",
                in_data.rstrip(),
            )
            raise AIOMySensorsMessageError from exc
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
