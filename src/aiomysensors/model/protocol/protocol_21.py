"""Provide the protocol for MySensors version 2.1."""

from enum import IntEnum

from .protocol_20 import (  # noqa: F401
    INTERNAL_COMMAND_TYPE,
    STRICT_SYSTEM_COMMAND_TYPES,
    VALID_MESSAGE_TYPES,
    VALID_SYSTEM_COMMAND_TYPES,
    Command,
    Presentation,
    SetReq,
    Stream,
)
from .protocol_20 import (
    IncomingMessageHandler as IncomingMessageHandler20,
)
from .protocol_20 import (
    OutgoingMessageHandler as OutgoingMessageHandler20,
)


class IncomingMessageHandler(IncomingMessageHandler20):
    """Represent a message handler."""


class OutgoingMessageHandler(OutgoingMessageHandler20):
    """Represent a handler for outgoing messages."""


class Internal(IntEnum):
    """MySensors internal types."""

    # Use this to report the battery level (in percent 0-100).
    I_BATTERY_LEVEL = 0
    # Sensors can request the current time from the Controller using this
    # message. The time will be reported as the seconds since 1970
    I_TIME = 1
    # Sensors report their library version at startup using this message type
    I_VERSION = 2
    # Use this to request a unique node id from the controller.
    I_ID_REQUEST = 3
    # Id response back to sensor. Payload contains sensor id.
    I_ID_RESPONSE = 4
    # Start/stop inclusion mode of the Controller (1=start, 0=stop).
    I_INCLUSION_MODE = 5
    # Config request from node. Reply with metric (M) or imperial (I) back to node.
    I_CONFIG = 6
    # When a sensor starts up, it broadcast a search request to all neighbor
    # nodes. They reply with a I_FIND_PARENT_RESPONSE.
    I_FIND_PARENT = 7
    # Reply message type to I_FIND_PARENT request.
    I_FIND_PARENT_RESPONSE = 8
    # Sent by the gateway to the Controller to trace-log a message
    I_LOG_MESSAGE = 9
    # A message that can be used to transfer child sensors
    # (from EEPROM routing table) of a repeating node.
    I_CHILDREN = 10
    # Optional sketch name that can be used to identify sensor in the
    # Controller GUI
    I_SKETCH_NAME = 11
    # Optional sketch version that can be reported to keep track of the version
    # of sensor in the Controller GUI.
    I_SKETCH_VERSION = 12
    # Used by OTA firmware updates. Request for node to reboot.
    I_REBOOT = 13
    # Send by gateway to controller when startup is complete
    I_GATEWAY_READY = 14
    # Provides signing related preferences (first byte is preference version).
    I_SIGNING_PRESENTATION = 15
    I_REQUEST_SIGNING = 15  # Alias for I_SIGNING_PRESENTATION
    # Request for a nonce.
    I_NONCE_REQUEST = 16
    I_GET_NONCE = 16  # Alias for I_NONCE_REQUEST
    # Payload is nonce data.
    I_NONCE_RESPONSE = 17
    I_GET_NONCE_RESPONSE = 17  # Alias for I_NONCE_RESPONSE
    I_HEARTBEAT_REQUEST = 18
    I_HEARTBEAT = 18  # Alias for I_HEARTBEAT_REQUEST
    I_PRESENTATION = 19
    I_DISCOVER_REQUEST = 20
    I_DISCOVER = 20  # Alias for I_DISCOVER_REQUEST
    I_DISCOVER_RESPONSE = 21
    I_HEARTBEAT_RESPONSE = 22
    # Node is locked (reason in string-payload).
    I_LOCKED = 23
    I_PING = 24  # Ping sent to node, payload incremental hop counter
    # In return to ping, sent back to sender, payload incremental hop counter
    I_PONG = 25
    I_REGISTRATION_REQUEST = 26  # Register request to GW
    I_REGISTRATION_RESPONSE = 27  # Register response from GW
    I_DEBUG = 28  # Debug message


NODE_ID_REQUEST_TYPES = {Internal.I_ID_REQUEST, Internal.I_ID_RESPONSE}

VALID_COMMAND_TYPES = {
    Command.presentation: list(Presentation),
    Command.set: list(SetReq),
    Command.req: list(SetReq),
    Command.internal: list(Internal),
    Command.stream: list(Stream),
}
