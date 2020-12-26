"""Provide aiomysensors exceptions."""
from typing import Optional


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


class InvalidMessageError(AIOMySensorsError):
    """Represent an invalid message exception."""


class UnsupportedMessageError(AIOMySensorsError):
    """Represent an unsupported message exception."""


class TransportError(AIOMySensorsError):
    """Represent a transport error."""


class TransportReadError(TransportError):
    """The transport failed to read."""

    def __init__(self, partial_bytes: Optional[bytes] = None) -> None:
        """Set up error."""
        message = ""

        if partial_bytes is not None:
            message = f"Partial bytes read: {partial_bytes!r}"

        super().__init__(message)
        self.partial_bytes = partial_bytes


class TransportFailedError(TransportError):
    """The transport failed."""
