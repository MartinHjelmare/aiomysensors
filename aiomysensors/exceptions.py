"""Provide aiomysensors exceptions."""


class AIOMySensorsError(Exception):
    """Represent a base exception for aiomysensors."""


class AIOMySensorsMessageError(AIOMySensorsError):
    """Represent a message error for aiomysensors."""
