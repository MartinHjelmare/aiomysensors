"""Provide aiomysensors exceptions."""


class AIOMySensorsError(Exception):
    """Represent a base exception for aiomysensors."""


class AIOMySensorsMissingChildError(AIOMySensorsError):
    """Represent a missing child exception."""

    def __init__(self, child_id: int) -> None:
        """Set up error."""
        super().__init__(f"Child {child_id} not found.")
        self.child_id = child_id


class AIOMySensorsInvalidMessageError(AIOMySensorsError):
    """Represent an invalid message exception."""


class TransportError(AIOMySensorsError):
    """Represent a transport error."""


class TransportFailedError(TransportError):
    """The transport failed."""
