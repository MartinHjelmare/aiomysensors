"""Provide a package for aiomysensors."""
from pathlib import Path

from .exceptions import AIOMySensorsError, TransportError
from .gateway import Config, Gateway
from .transport.mqtt import MQTTTransport
from .transport.serial import SerialTransport
from .transport.tcp import TCPTransport

__all__ = [
    "AIOMySensorsError",
    "Config",
    "Gateway",
    "MQTTTransport",
    "SerialTransport",
    "TCPTransport",
    "TransportError",
]
__version__ = (Path(__file__).parent / "VERSION").read_text().strip()
