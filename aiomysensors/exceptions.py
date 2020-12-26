"""Provide aiomysensors exceptions."""
from typing import Any, Optional


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

    def __init__(self, error: Exception, message: Any) -> None:
        """Set up error."""
        super().__init__(f"Invalid message {message} received: {error}")
        self.message = message


class UnsupportedMessageError(AIOMySensorsError):
    """Represent an unsupported message exception."""


class TransportError(AIOMySensorsError):
    """Represent a transport error."""


class TransportReadError(TransportError):
    """The transport failed to read."""

    def __init__(self, error: Exception, partial_bytes: Optional[bytes] = None) -> None:
        """Set up error."""
        message = f"Failed to read from transport: {error}."

        if partial_bytes is not None:
            message = f"{message} Partial bytes read: {partial_bytes!r}"

        super().__init__(message)
        self.partial_bytes = partial_bytes


class TransportFailedError(TransportError):
    """The transport failed."""
