"""Provide MySensors protocols."""
from importlib import import_module
from typing import Any, Protocol, cast

from packaging import version

BROADCAST_ID = 255
DEFAULT_PROTOCOL_VERSION = "1.4"
DEFAULT_PROTOCOL_PATH = "aiomysensors.model.protocol.protocol_14"
MAX_NODE_ID = 254
PROTOCOL_VERSIONS = {
    DEFAULT_PROTOCOL_VERSION: DEFAULT_PROTOCOL_PATH,
    "1.5": "aiomysensors.model.protocol.protocol_15",
    "2.0": "aiomysensors.model.protocol.protocol_20",
}
SYSTEM_CHILD_ID = 255


class ProtocolType(Protocol):
    """Represent a protocol module type."""

    IncomingMessageHandler: Any
    OutgoingMessageHandler: Any
    Command: Any
    Presentation: Any
    SetReq: Any
    Internal: Any
    Stream: Any


def get_protocol(protocol_version: str) -> ProtocolType:
    """Return the protocol module for the protocol_version."""
    path = next(
        (
            PROTOCOL_VERSIONS[_protocol_version]
            for _protocol_version in sorted(PROTOCOL_VERSIONS, reverse=True)
            if version.parse(protocol_version) >= version.parse(_protocol_version)
        ),
        DEFAULT_PROTOCOL_PATH,
    )
    return cast(ProtocolType, import_module(path))
