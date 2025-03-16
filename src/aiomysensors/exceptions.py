"""Provide aiomysensors exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model.message import Message


class AIOMySensorsError(Exception):
    """Represent a base exception for aiomysensors."""


class MissingNodeError(AIOMySensorsError):
    """Represent a missing node exception."""

    def __init__(self, node_id: int) -> None:
        """Set up error."""
        super().__init__(f"Node {node_id} not found.")
        self.node_id = node_id


class MissingChildError(AIOMySensorsError):
    """Represent a missing child exception."""

    def __init__(self, child_id: int) -> None:
        """Set up error."""
        super().__init__(f"Child {child_id} not found.")
        self.child_id = child_id


class TooManyNodesError(AIOMySensorsError):
    """Represent too many nodes in the network."""

    def __init__(self) -> None:
        """Set up error."""
        super().__init__("More than 255 nodes present in network.")


class InvalidMessageError(AIOMySensorsError):
    """Represent an invalid message exception."""


class UnsupportedMessageError(AIOMySensorsError):
    """Represent an unsupported message exception."""

    def __init__(
        self,
        message: Message,
        protocol_version: str | None = None,
    ) -> None:
        """Set up error."""
        protocol_version = protocol_version or "1.4"
        super().__init__(
            f"Message type is not supported for protocol {protocol_version}: {message}",
        )
        self.message = message
        self.protocol_version = protocol_version


class PersistenceError(AIOMySensorsError):
    """Represent a persistence error."""


class PersistenceReadError(PersistenceError):
    """Represent a persistence read error."""

    def __init__(self, err: Exception) -> None:
        """Set up error."""
        super().__init__(f"Failed to read persistence file: {err}")


class PersistenceWriteError(PersistenceError):
    """Represent a persistence write error."""

    def __init__(self, err: Exception) -> None:
        """Set up error."""
        super().__init__(f"Failed to write persistence file: {err}")


class TransportError(AIOMySensorsError):
    """Represent a transport error."""


class TransportReadError(TransportError):
    """The transport failed to read."""

    def __init__(self, error: Exception, partial_bytes: bytes | None = None) -> None:
        """Set up error."""
        message = f"Failed to read from transport: {error}."

        if partial_bytes is not None:
            message = f"{message} Partial bytes read: {partial_bytes!r}"

        super().__init__(message)
        self.partial_bytes = partial_bytes


class TransportFailedError(TransportError):
    """The transport failed."""
