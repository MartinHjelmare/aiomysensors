"""Provide MySensors protocols."""
from abc import abstractmethod
from enum import IntEnum
from functools import cache
from importlib import import_module
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Optional,
    Protocol,
    Set,
    Type,
    cast,
)

from awesomeversion import AwesomeVersion

if TYPE_CHECKING:
    from ...gateway import Gateway, MessageBuffer
    from ..message import Message

BROADCAST_ID = 255
DEFAULT_PROTOCOL_VERSION = "1.4"
DEFAULT_PROTOCOL_PATH = "aiomysensors.model.protocol.protocol_14"
MAX_NODE_ID = 254
PROTOCOL_VERSIONS = {
    DEFAULT_PROTOCOL_VERSION: DEFAULT_PROTOCOL_PATH,
    "1.5": "aiomysensors.model.protocol.protocol_15",
    "2.0": "aiomysensors.model.protocol.protocol_20",
    "2.1": "aiomysensors.model.protocol.protocol_21",
    "2.2": "aiomysensors.model.protocol.protocol_22",
}
SYSTEM_CHILD_ID = 255


class IncomingMessageHandlerBase:
    """Represent a handler for incoming messages."""

    @classmethod
    @abstractmethod
    async def handle_presentation(
        cls, gateway: "Gateway", message: "Message", message_buffer: "MessageBuffer"
    ) -> "Message":
        """Process a presentation message."""

    @classmethod
    @abstractmethod
    async def handle_set(
        cls, gateway: "Gateway", message: "Message", message_buffer: "MessageBuffer"
    ) -> "Message":
        """Process a set message."""

    @classmethod
    @abstractmethod
    async def handle_req(
        cls, gateway: "Gateway", message: "Message", message_buffer: "MessageBuffer"
    ) -> "Message":
        """Process a req message."""

    @classmethod
    @abstractmethod
    async def handle_internal(
        cls, gateway: "Gateway", message: "Message", message_buffer: "MessageBuffer"
    ) -> "Message":
        """Process an internal message."""

    @classmethod
    @abstractmethod
    async def handle_stream(
        cls, gateway: "Gateway", message: "Message", message_buffer: "MessageBuffer"
    ) -> "Message":
        """Process a stream message."""


class OutgoingMessageHandlerBase:
    """Represent a handler for outgoing messages."""

    @classmethod
    @abstractmethod
    async def handle_set(
        cls,
        gateway: "Gateway",
        message: "Message",
        message_buffer: Optional["MessageBuffer"],
        decoded_message: str,
    ) -> None:
        """Process outgoing set messages."""

    @classmethod
    @abstractmethod
    async def handle_internal(
        cls,
        gateway: "Gateway",
        message: "Message",
        message_buffer: Optional["MessageBuffer"],
        decoded_message: str,
    ) -> None:
        """Process outgoing internal messages."""


class ProtocolType(Protocol):
    """Represent a protocol module type."""

    IncomingMessageHandler: Type[IncomingMessageHandlerBase]
    OutgoingMessageHandler: Type[OutgoingMessageHandlerBase]
    Command: Type[IntEnum]
    Presentation: Type[IntEnum]
    SetReq: Type[IntEnum]
    Internal: Type[IntEnum]
    Stream: Type[IntEnum]
    INTERNAL_COMMAND_TYPE: int
    NODE_ID_REQUEST_TYPES: Set[int]
    STRICT_SYSTEM_COMMAND_TYPES: Set[int]
    VALID_SYSTEM_COMMAND_TYPES: Set[int]


@cache
def get_protocol(protocol_version: str) -> ProtocolType:
    """Return the protocol module for the protocol_version."""
    path = next(
        (
            PROTOCOL_VERSIONS[_protocol_version]
            for _protocol_version in sorted(PROTOCOL_VERSIONS, reverse=True)
            if AwesomeVersion(protocol_version) >= AwesomeVersion(_protocol_version)
        ),
        DEFAULT_PROTOCOL_PATH,
    )
    return cast(ProtocolType, import_module(path))


def get_incoming_message_handler(
    protocol: ProtocolType, message: "Message"
) -> Callable[["Gateway", "Message", "MessageBuffer"], Coroutine[Any, Any, "Message"]]:
    """Return the correct message handler from the protocol."""
    command: IntEnum = protocol.Command(message.command)
    message_handlers = protocol.IncomingMessageHandler
    message_handler: Callable[
        ["Gateway", "Message", "MessageBuffer"], Coroutine[Any, Any, "Message"]
    ] = getattr(message_handlers, f"handle_{command.name}")
    return message_handler


def get_outgoing_message_handler(
    protocol: ProtocolType, message: "Message"
) -> Callable[
    ["Gateway", "Message", Optional["MessageBuffer"], str], Coroutine[Any, Any, None]
]:
    """Return the correct message handler from the protocol."""
    command: IntEnum = protocol.Command(message.command)
    message_handlers = protocol.OutgoingMessageHandler
    message_handler: Callable[
        ["Gateway", "Message", Optional["MessageBuffer"], str],
        Coroutine[Any, Any, None],
    ] = getattr(message_handlers, f"handle_{command.name}")
    return message_handler
