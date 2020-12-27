"""Provide a package for aiomysensors."""
from pathlib import Path

from .exceptions import AIOMySensorsError
from .gateway import Config, Gateway
from .transport.serial import SerialTransport

__all__ = ["AIOMySensorsError", "Config", "Gateway", "SerialTransport"]
__version__ = (Path(__file__).parent / "VERSION").read_text().strip()
