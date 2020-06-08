"""Provide aiomysensors exceptions."""


class AIOMySensorsError(Exception):
    """Represent a base exception for aiomysensors."""


class AIOMySensorsMissingChildError(Exception):
    """Represent a missing child exception."""

    def __init__(self, child_id: int) -> None:
        """Set up error."""
        super().__init__(f"Child {child_id} not found.")
        self.child_id = child_id
