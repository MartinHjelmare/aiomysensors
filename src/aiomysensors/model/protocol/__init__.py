"""Provide MySensors protocols."""

from __future__ import annotations

from enum import IntEnum
from functools import cache
from typing import (
    Protocol,
    cast,
)

from awesomeversion import AwesomeVersion

from aiomysensors.model.const import DEFAULT_PROTOCOL_VERSION

from . import protocol_14, protocol_15, protocol_20, protocol_21, protocol_22
from .message_handler import IncomingMessageHandlerBase, OutgoingMessageHandlerBase

PROTOCOL_VERSIONS = {
    DEFAULT_PROTOCOL_VERSION: protocol_14,
    "1.5": protocol_15,
    "2.0": protocol_20,
    "2.1": protocol_21,
    "2.2": protocol_22,
}


class ProtocolType(Protocol):
    """Represent a protocol module type."""

    IncomingMessageHandler: type[IncomingMessageHandlerBase]
    OutgoingMessageHandler: type[OutgoingMessageHandlerBase]
    Command: type[IntEnum]
    Presentation: type[IntEnum]
    SetReq: type[IntEnum]
    Internal: type[IntEnum]
    Stream: type[IntEnum]
    INTERNAL_COMMAND_TYPE: int
    NODE_ID_REQUEST_TYPES: set[int]
    STRICT_SYSTEM_COMMAND_TYPES: set[int]
    VALID_COMMAND_TYPES: dict[int, list[IntEnum]]
    VALID_MESSAGE_TYPES: dict[int, set[IntEnum]]
    VALID_SYSTEM_COMMAND_TYPES: set[int]
    VERSION: str


@cache
def get_protocol(protocol_version: str) -> ProtocolType:
    """Return the protocol module for the protocol_version."""
    module = next(
        (
            PROTOCOL_VERSIONS[_protocol_version]
            for _protocol_version in sorted(PROTOCOL_VERSIONS, reverse=True)
            if AwesomeVersion(protocol_version) >= AwesomeVersion(_protocol_version)
        ),
        protocol_14,
    )
    return cast("ProtocolType", module)
