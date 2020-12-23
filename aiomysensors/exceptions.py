"""Provide aiomysensors exceptions."""


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


class InvalidMessageError(AIOMySensorsError):
    """Represent an invalid message exception."""


class UnsupportedMessageError(AIOMySensorsError):
    """Represent an unsupported message exception."""


class TransportError(AIOMySensorsError):
    """Represent a transport error."""


class TransportFailedError(TransportError):
    """The transport failed."""
