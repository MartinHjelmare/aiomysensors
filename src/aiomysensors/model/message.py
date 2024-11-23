"""Provide a MySensors message abstraction.

Validation should be done on a protocol level, i.e. not with gateway state.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from .protocol import ProtocolType

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
        self.node_id = int(node_id)  # handle IntEnum
        self.child_id = int(child_id)
        self.command = int(command)
        self.ack = ack
        self.message_type = int(message_type)
        self.payload = payload

    def __repr__(self) -> str:
        """Return the representation."""
        return (
            f"{type(self).__name__}(node_id={self.node_id!r}, "
            f"child_id={self.child_id!r}, command={self.command!r}, ack={self.ack!r}, "
            f"message_type={self.message_type!r}, payload={self.payload!r})"
        )


class ChildIdField(fields.Field):
    """Represent a child id field."""

    def _deserialize(
        self,
        value: str,
        attr: str | None,  # noqa: ARG002
        data: Mapping[str, Any] | None,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> int:
        if data is None:
            raise ValidationError("Data must be provided.")
        protocol = self.context.get("protocol")
        if protocol is None:
            raise ValidationError("Protocol not set on MessageSchema.")
        return validate_child_id(value=value, data=data, protocol=protocol)


class CommandField(fields.Field):
    """Represent a command field."""

    def validate_command(self, *, value: str, data: Mapping[str, Any]) -> int:
        """Validate the command field."""
        command = validate_command(value)

        protocol = self.context.get("protocol")
        if protocol is None:
            raise ValidationError("Protocol not set on MessageSchema.")

        command_type = protocol.Command

        valid_commands = {member.value for member in tuple(command_type)}
        child_id = validate_child_id(
            value=data["child_id"],
            data=data,
            protocol=protocol,
        )
        if child_id == SYSTEM_CHILD_ID:
            valid_commands = protocol.VALID_SYSTEM_COMMAND_TYPES

        if command not in valid_commands:
            raise ValidationError(
                f"The command type must one of {valid_commands} "
                f"when child id is {SYSTEM_CHILD_ID}.",
            )

        return command

    def _deserialize(
        self,
        value: str,
        attr: str | None,  # noqa: ARG002
        data: Mapping[str, Any] | None,
        **kwargs: Any,  # noqa: ANN401, ARG002
    ) -> int:
        if data is None:
            raise ValidationError("Data must be provided.")
        return self.validate_command(value=value, data=data)


class MessageSchema(Schema):
    """Represent a message schema."""

    node_id = NODE_ID_FIELD
    child_id = ChildIdField(required=True)
    command = CommandField(required=True)
    ack = fields.Int(required=True, validate=validate.OneOf((0, 1)))
    message_type = fields.Int(required=True)
    payload = fields.Str(required=True)

    class Meta:
        """Schema options."""

        fields = ("node_id", "child_id", "command", "ack", "message_type", "payload")
        ordered = True

    def set_protocol(self, protocol: ProtocolType) -> None:
        """Set the protocol."""
        self.context["protocol"] = protocol

    @pre_load
    def to_dict(self, in_data: str, **kwargs: Any) -> dict[str, str]:  # noqa: ANN401, ARG002
        """Transform message string to a dict."""
        list_data = in_data.rstrip().split(DELIMITER)
        return dict(zip(self.fields, list_data, strict=False))

    @post_load
    def make_message(self, data: dict, **kwargs: Any) -> Message:  # noqa: ANN401, ARG002
        """Make a message."""
        return Message(**data)

    @post_dump
    def to_string(self, data: dict[str, int | str], **kwargs: Any) -> str:  # noqa: ANN401, ARG002
        """Serialize message from a dict to a MySensors message string."""
        try:
            string = f"{DELIMITER.join([str(data[field]) for field in self.fields])}\n"
        except KeyError as err:
            raise ValidationError("Not a valid Message instance") from err
        return string


def validate_child_id(
    *,
    value: str,
    data: Mapping[str, Any],
    protocol: ProtocolType,
) -> int:
    """Validate the child id field."""
    try:
        child_id = int(value)
    except ValueError as exc:
        raise ValidationError("The child_id type must be an integer.") from exc

    child_range = validate.Range(
        min=0,
        max=SYSTEM_CHILD_ID,
        error="Not valid child_id: {input}",
    )
    child_range(child_id)

    command = validate_command(data["command"])
    message_type = validate_message_type(data["message_type"])

    if (
        command == protocol.INTERNAL_COMMAND_TYPE
        and message_type in protocol.NODE_ID_REQUEST_TYPES
    ):
        return child_id

    if command in protocol.STRICT_SYSTEM_COMMAND_TYPES:
        valid_child_id = SYSTEM_CHILD_ID
        error = f"When message command is {command}, child_id must be {SYSTEM_CHILD_ID}"

        if child_id != valid_child_id:
            raise ValidationError(error)

    return child_id


def validate_command(value: str) -> int:
    """Validate a command."""
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError("The command type must be an integer.") from exc


def validate_message_type(value: str) -> int:
    """Validate a message type."""
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError("The message type must be an integer.") from exc
