"""Provide a MySensors message abstraction."""
from typing import Any, Dict, Mapping, Optional, Union

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_dump,
    post_load,
    pre_load,
    validate,
)

from .const import NODE_ID_FIELD, SYSTEM_CHILD_ID
from .protocol import DEFAULT_PROTOCOL_VERSION, get_protocol

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


class CommandField(fields.Field):
    """Represent a command field."""

    def validate_command(self, *, value: str, data: Optional[Mapping[str, Any]]) -> int:
        """Validate the command field."""
        assert data is not None  # Satisfy typing.
        try:
            command = int(value)
        except ValueError as exc:
            raise ValidationError("The command type must be an integer.") from exc

        protocol_version = self.context.get(
            "protocol_version", DEFAULT_PROTOCOL_VERSION
        )
        protocol = get_protocol(protocol_version)
        # Dynamic import of the protocol makes typing hard.
        command_enum = protocol.Command  # type: ignore

        valid_commands = [member.value for member in tuple(command_enum)]
        child_id = int(data["child_id"])
        if child_id == SYSTEM_CHILD_ID:
            valid_commands = [
                command_enum.presentation.value,
                command_enum.internal.value,
                command_enum.stream.value,
            ]

        if command not in valid_commands:
            raise ValidationError(
                f"The command type must one of {valid_commands} "
                f"when child id is {SYSTEM_CHILD_ID}."
            )

        return command

    def _deserialize(
        self,
        value: str,
        attr: Optional[str],
        data: Optional[Mapping[str, Any]],
        **kwargs: Any,
    ) -> int:
        return self.validate_command(value=value, data=data)


class MessageSchema(Schema):
    """Represent a message schema."""

    node_id = NODE_ID_FIELD
    child_id = fields.Int(required=True)
    command = CommandField(required=True)
    ack = fields.Int(required=True, validate=validate.OneOf((0, 1)))
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
