"""Provide a package for aiomysensors."""
from pathlib import Path

from .exceptions import AIOMySensorsError
from .gateway import Config, Gateway
from .transport.serial import SerialTransport
from .transport.tcp import TCPTransport

__all__ = ["AIOMySensorsError", "Config", "Gateway", "SerialTransport", "TCPTransport"]
__version__ = (Path(__file__).parent / "VERSION").read_text().strip()
