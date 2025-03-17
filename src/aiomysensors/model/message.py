"""Provide a MySensors message abstraction.

Validation should be done on a protocol level, i.e. not with gateway state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Self

from mashumaro import DataClassDictMixin

from aiomysensors.exceptions import InvalidMessageError

from .const import BROADCAST_ID, SYSTEM_CHILD_ID

if TYPE_CHECKING:
    from .protocol import ProtocolType

DELIMITER = ";"


@dataclass
class Message(DataClassDictMixin):
    """Represent a message from the gateway."""

    node_id: int = 0
    child_id: int = 0
    command: int = 0
    ack: Literal[0, 1] = 0
    message_type: int = 0
    payload: str = ""

    @classmethod
    def from_string(cls, value: str, validation_schema: MessageSchema) -> Self:
        """Create a message from a string."""
        items = value.rstrip().split(DELIMITER)
        try:
            data = {
                "node_id": items[0],
                "child_id": items[1],
                "command": items[2],
                "ack": items[3],
                "message_type": items[4],
                "payload": items[5],
            }
        except IndexError as err:
            raise InvalidMessageError(
                f"Failed to parse string {value} to message: {err}"
            ) from err

        node_id = validation_schema.validate_node_id(data=data)
        child_id = validation_schema.validate_child_id(data=data)
        command = validation_schema.validate_command(data=data)
        ack = validation_schema.validate_ack(data=data)
        message_type = validation_schema.validate_message_type(data=data)
        payload = data["payload"]
        return cls(node_id, child_id, command, ack, message_type, payload)

    def to_string(self, validation_schema: MessageSchema) -> str:
        """Serialize the message."""
        data = self.to_dict()
        validation_schema.validate_node_id(data=data)
        validation_schema.validate_child_id(data=data)
        validation_schema.validate_command(data=data)
        validation_schema.validate_ack(data=data)
        validation_schema.validate_message_type(data=data)
        return (
            f"{self.node_id};{self.child_id};{self.command};"
            f"{self.ack};{self.message_type};{self.payload}\n"
        )


@dataclass
class MessageSchema:
    """Represent the message validation schema."""

    protocol: ProtocolType

    def validate_node_id(self, *, data: Mapping[str, str]) -> int:
        """Validate the node id field."""
        value = data["node_id"]
        try:
            node_id = int(value)
        except ValueError as err:
            raise InvalidMessageError("The node_id type must be an integer.") from err

        if node_id < 0 or node_id > BROADCAST_ID:
            raise InvalidMessageError(
                f"The node_id must be between 0 and {BROADCAST_ID}, got {node_id}."
            )

        return node_id

    def validate_child_id(
        self,
        *,
        data: Mapping[str, str],
        command: int | None = None,
    ) -> int:
        """Validate the child id field."""
        value = data["child_id"]
        try:
            child_id = int(value)
        except ValueError as exc:
            raise InvalidMessageError("The child_id type must be an integer.") from exc

        if child_id < 0 or child_id > SYSTEM_CHILD_ID:
            raise InvalidMessageError(
                f"The child_id must be between 0 and {SYSTEM_CHILD_ID}, got {child_id}."
            )

        if command is None:
            command = self.validate_command(data=data, child_id=child_id)
        message_type = self.validate_message_type(data=data)

        if (
            command == self.protocol.INTERNAL_COMMAND_TYPE
            and message_type in self.protocol.NODE_ID_REQUEST_TYPES
        ):
            return child_id

        if command in self.protocol.STRICT_SYSTEM_COMMAND_TYPES:
            valid_child_id = SYSTEM_CHILD_ID
            error = (
                f"When message command is {command}, child_id must be {SYSTEM_CHILD_ID}"
            )

            if child_id != valid_child_id:
                raise InvalidMessageError(error)

        return child_id

    def validate_command(
        self,
        *,
        data: Mapping[str, str],
        child_id: int | None = None,
    ) -> int:
        """Validate a command."""
        value = data["command"]
        try:
            command = int(value)
        except ValueError as exc:
            raise InvalidMessageError("The command type must be an integer.") from exc

        command_type = self.protocol.Command

        valid_commands = {member.value for member in tuple(command_type)}
        if child_id is None:
            child_id = self.validate_child_id(data=data, command=command)
        if child_id == SYSTEM_CHILD_ID:
            valid_commands = self.protocol.VALID_SYSTEM_COMMAND_TYPES

        if command not in valid_commands:
            raise InvalidMessageError(
                f"The command type must one of {valid_commands} "
                f"when child id is {SYSTEM_CHILD_ID}.",
            )

        return command

    def validate_ack(self, *, data: Mapping[str, str]) -> Literal[0, 1]:
        """Validate an ack."""
        value = data["ack"]
        try:
            ack = int(value)
        except ValueError as exc:
            raise InvalidMessageError("The ack type must be an integer.") from exc
        if ack not in (0, 1):
            raise InvalidMessageError(f"The ack must be either 0 or 1, got {ack}.")
        return 1 if ack else 0

    def validate_message_type(self, *, data: Mapping[str, str]) -> int:
        """Validate a message type."""
        value = data["message_type"]
        try:
            return int(value)
        except ValueError as exc:
            raise InvalidMessageError("The message type must be an integer.") from exc
