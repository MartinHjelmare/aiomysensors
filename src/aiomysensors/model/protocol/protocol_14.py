"""Provide the protocol for MySensors version 1.4."""

from __future__ import annotations

import calendar
from collections.abc import Awaitable, Callable, Coroutine
from enum import IntEnum
import time
from typing import TYPE_CHECKING, Any

from aiomysensors.exceptions import (
    MissingChildError,
    MissingNodeError,
    TooManyNodesError,
    UnsupportedMessageError,
)
from aiomysensors.model.const import (
    DEFAULT_PROTOCOL_VERSION,
    MAX_NODE_ID,
    SYSTEM_CHILD_ID,
)
from aiomysensors.model.message import Message
from aiomysensors.model.node import Node

from .message_handler import IncomingMessageHandlerBase

if TYPE_CHECKING:
    from aiomysensors.gateway import Gateway, MessageBuffer

VERSION = "1.4"


def handle_missing_protocol_version[
    _IncomingMessageHandlerT: type[IncomingMessageHandler],
    **_P,
](
    func: Callable[
        [_IncomingMessageHandlerT, Gateway, Message, MessageBuffer],
        Awaitable[Message],
    ],
) -> Callable[
    [_IncomingMessageHandlerT, Gateway, Message, MessageBuffer],
    Coroutine[Any, Any, Message],
]:
    """Handle a missing set protocol version."""

    async def wrapper(
        self: _IncomingMessageHandlerT,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Wrap a message handler."""
        try:
            message = await func(self, gateway, message, message_buffer)
        finally:
            if gateway.protocol_version is None and (
                message.command != Command.internal
                or message.message_type
                not in (
                    Internal.I_LOG_MESSAGE,
                    Internal.I_GATEWAY_READY,
                )
            ):
                version_message = Message(
                    child_id=SYSTEM_CHILD_ID,
                    command=Command.internal,
                    message_type=Internal.I_VERSION,
                )
                await gateway.send(version_message, message_buffer=False)

        return message

    return wrapper


class IncomingMessageHandler(IncomingMessageHandlerBase):
    """Represent a handler for incoming messages."""

    @classmethod
    async def _handle_message(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
        message_handler: Callable[[Gateway, Message, MessageBuffer], Awaitable[Message]]
        | None,
    ) -> Message:
        """Handle a message."""
        if message_handler is None:
            # No special handling required.
            return message

        return await message_handler(gateway, message, message_buffer)

    @classmethod
    @handle_missing_protocol_version
    async def handle_presentation(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a presentation message."""
        if message.child_id == SYSTEM_CHILD_ID:
            # this is a presentation of a node
            node = Node(
                node_id=message.node_id,
                node_type=message.message_type,
                protocol_version=message.payload,
            )
            gateway.nodes[node.node_id] = node
            if message.node_id == 0:
                # Set the gateway protocol version.
                message = await cls.handle_i_version(gateway, message, message_buffer)
            return message

        # this is a presentation of a child sensor
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        gateway.nodes[message.node_id].add_child(
            message.child_id,
            message.message_type,
            description=message.payload,
        )

        return message

    @classmethod
    @handle_missing_protocol_version
    async def handle_set(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process a set message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        if message.child_id not in gateway.nodes[message.node_id].children:
            raise MissingChildError(message.node_id)

        gateway.nodes[message.node_id].set_child_value(
            message.child_id,
            message.message_type,
            message.payload,
        )

        # Check if reboot is true
        if gateway.nodes[message.node_id].reboot:
            # Send a reboot command.
            reboot_message = Message(
                node_id=message.node_id,
                child_id=SYSTEM_CHILD_ID,
                command=Command.internal,
                ack=0,
                message_type=Internal.I_REBOOT,
                payload="",
            )
            await gateway.send(reboot_message, message_buffer=False)

        return message

    @classmethod
    @handle_missing_protocol_version
    async def handle_req(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process a req message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        if message.child_id not in gateway.nodes[message.node_id].children:
            raise MissingChildError(message.node_id)

        value = (
            gateway.nodes[message.node_id]
            .children[message.child_id]
            .values.get(message.message_type)
        )

        if value is not None:
            set_message = Message(
                node_id=message.node_id,
                child_id=message.child_id,
                command=Command.set,
                message_type=message.message_type,
                payload=value,
            )
            await gateway.send(set_message, message_buffer=False)

        return message

    @classmethod
    @handle_missing_protocol_version
    async def handle_internal(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process an internal message."""
        try:
            internal = gateway.protocol.Internal(message.message_type)
        except ValueError as err:
            raise UnsupportedMessageError(message, gateway.protocol_version) from err

        message_handler = getattr(cls, f"handle_{internal.name.lower()}", None)

        return await cls._handle_message(
            gateway,
            message,
            message_buffer,
            message_handler,
        )

    @classmethod
    @handle_missing_protocol_version
    async def handle_stream(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,
    ) -> Message:
        """Process a stream message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        try:
            stream = gateway.protocol.Stream(message.message_type)
        except ValueError as err:
            raise UnsupportedMessageError(message, gateway.protocol_version) from err

        message_handler = getattr(cls, f"handle_{stream.name.lower()}", None)

        return await cls._handle_message(
            gateway,
            message,
            message_buffer,
            message_handler,
        )

    @classmethod
    async def handle_i_version(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal version message."""
        gateway.protocol_version = message.payload
        return message

    @classmethod
    async def handle_i_id_request(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal id request message."""
        next_id = max(gateway.nodes) + 1 if gateway.nodes else 1

        if next_id > MAX_NODE_ID:
            raise TooManyNodesError

        # Use temporary default values for the node until node sends presentation.
        gateway.nodes[next_id] = Node(
            node_id=next_id,
            node_type=Presentation.S_ARDUINO_NODE,
            protocol_version=DEFAULT_PROTOCOL_VERSION,
        )
        id_response_message = Message(
            node_id=message.node_id,
            child_id=message.child_id,
            command=message.command,
            message_type=Internal.I_ID_RESPONSE,
            payload=str(next_id),
        )
        await gateway.send(id_response_message, message_buffer=False)

        return message

    @classmethod
    async def handle_i_config(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal config message."""
        config_message = Message(
            node_id=message.node_id,
            child_id=message.child_id,
            command=message.command,
            message_type=message.message_type,
            payload="M" if gateway.config.metric else "I",
        )
        await gateway.send(config_message, message_buffer=False)
        return message

    @classmethod
    async def handle_i_time(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal time message."""
        time_message = Message(
            node_id=message.node_id,
            child_id=message.child_id,
            command=message.command,
            message_type=message.message_type,
            payload=str(calendar.timegm(time.localtime())),
        )
        await gateway.send(time_message, message_buffer=False)
        return message

    @classmethod
    async def handle_i_battery_level(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal battery level message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        gateway.nodes[message.node_id].battery_level = round(float(message.payload))
        return message

    @classmethod
    async def handle_i_sketch_name(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal sketch name message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        gateway.nodes[message.node_id].sketch_name = message.payload
        return message

    @classmethod
    async def handle_i_sketch_version(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer,  # noqa: ARG003
    ) -> Message:
        """Process an internal sketch version message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        gateway.nodes[message.node_id].sketch_version = message.payload
        return message


class OutgoingMessageHandler:
    """Represent a handler for outgoing messages."""

    @classmethod
    async def handle_set(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer | None,
        decoded_message: str,
    ) -> None:
        """Process outgoing set messages."""
        node = gateway.nodes.get(message.node_id)
        if message_buffer and node and node.sleeping:
            message_buffer.set_messages[
                (message.node_id, message.child_id, message.message_type)
            ] = message

            return

        await gateway.transport.write(decoded_message)

    @classmethod
    async def handle_internal(
        cls,
        gateway: Gateway,
        message: Message,
        message_buffer: MessageBuffer | None,
        decoded_message: str,
    ) -> None:
        """Process outgoing internal messages."""
        if message_buffer:
            message_buffer.internal_messages[
                (message.node_id, message.child_id, message.message_type)
            ] = message

            return

        await gateway.transport.write(decoded_message)


class Command(IntEnum):
    """MySensors command types."""

    presentation = 0
    set = 1
    req = 2
    internal = 3
    stream = 4


class Presentation(IntEnum):
    """MySensors presentation types."""

    S_DOOR = 0
    S_MOTION = 1
    S_SMOKE = 2
    S_LIGHT = 3
    S_DIMMER = 4
    S_COVER = 5
    S_TEMP = 6
    S_HUM = 7
    S_BARO = 8
    S_WIND = 9
    S_RAIN = 10
    S_UV = 11
    S_WEIGHT = 12
    S_POWER = 13
    S_HEATER = 14
    S_DISTANCE = 15
    S_LIGHT_LEVEL = 16
    S_ARDUINO_NODE = 17
    S_ARDUINO_RELAY = 18
    S_LOCK = 19
    S_IR = 20
    S_WATER = 21
    S_AIR_QUALITY = 22
    S_CUSTOM = 23
    S_DUST = 24
    S_SCENE_CONTROLLER = 25


class SetReq(IntEnum):
    """MySensors set/req types."""

    V_TEMP = 0  # Temperature
    V_HUM = 1  # Humidity
    V_LIGHT = 2  # Light status. 0=off 1=on
    V_DIMMER = 3  # Dimmer value. 0-100%
    V_PRESSURE = 4  # Atmospheric Pressure
    # Weather forecast. One of "stable", "sunny", "cloudy", "unstable",
    # "thunderstorm" or "unknown"
    V_FORECAST = 5
    V_RAIN = 6  # Amount of rain
    V_RAINRATE = 7  # Rate of rain
    V_WIND = 8  # Windspeed
    V_GUST = 9  # Gust
    V_DIRECTION = 10  # Wind direction
    V_UV = 11  # UV light level
    V_WEIGHT = 12  # Weight (for scales etc)
    V_DISTANCE = 13  # Distance
    V_IMPEDANCE = 14  # Impedance value
    # Armed status of a security sensor.  1=armed, 0=bypassed
    V_ARMED = 15
    # Tripped status of a security sensor. 1=tripped, 0=untripped
    V_TRIPPED = 16
    V_WATT = 17  # Watt value for power meters
    V_KWH = 18  # Accumulated number of KWH for a power meter
    V_SCENE_ON = 19  # Turn on a scene
    V_SCENE_OFF = 20  # Turn off a scene
    # Mode of heater. One of "Off", "HeatOn", "CoolOn", or "AutoChangeOver"
    V_HEATER = 21
    V_HEATER_SW = 22  # Heater switch power. 1=On, 0=Off
    V_LIGHT_LEVEL = 23  # Light level. 0-100%
    V_VAR1 = 24  # Custom value
    V_VAR2 = 25  # Custom value
    V_VAR3 = 26  # Custom value
    V_VAR4 = 27  # Custom value
    V_VAR5 = 28  # Custom value
    V_UP = 29  # Window covering. Up.
    V_DOWN = 30  # Window covering. Down.
    V_STOP = 31  # Window covering. Stop.
    V_IR_SEND = 32  # Send out an IR-command
    V_IR_RECEIVE = 33  # This message contains a received IR-command
    V_FLOW = 34  # Flow of water (in meter)
    V_VOLUME = 35  # Water volume
    V_LOCK_STATUS = 36  # Set or get lock status. 1=Locked, 0=Unlocked
    V_DUST_LEVEL = 37  # Dust level
    V_VOLTAGE = 38  # Voltage level
    V_CURRENT = 39  # Current level


class Internal(IntEnum):
    """MySensors internal types."""

    # Use this to report the battery level (in percent 0-100).
    I_BATTERY_LEVEL = 0
    # Nodes can request the current time from the Controller using this
    # message. The time will be reported as the seconds since 1970
    I_TIME = 1
    # Nodes report their library version at startup using this message type
    I_VERSION = 2
    # Use this to request a unique node id from the controller.
    I_ID_REQUEST = 3
    # Id response back to node. Payload contains node id.
    I_ID_RESPONSE = 4
    # Start/stop inclusion mode of the Controller (1=start, 0=stop).
    I_INCLUSION_MODE = 5
    # Config request from node. Reply with metric (M) or imperial (I) back to node.
    I_CONFIG = 6
    # When a node starts up, it broadcast a search request to all neighbor
    # nodes. They reply with a I_FIND_PARENT_RESPONSE.
    I_FIND_PARENT = 7
    # Reply message type to I_FIND_PARENT request.
    I_FIND_PARENT_RESPONSE = 8
    # Sent by the gateway to the Controller to trace-log a message
    I_LOG_MESSAGE = 9
    # A message that can be used to transfer children
    # (from EEPROM routing table) of a repeating node.
    I_CHILDREN = 10
    # Optional sketch name that can be used to identify node in the
    # Controller.
    I_SKETCH_NAME = 11
    # Optional sketch version that can be reported to keep track of the version
    # of the node in the Controller.
    I_SKETCH_VERSION = 12
    # Used by OTA firmware updates. Request for node to reboot.
    I_REBOOT = 13
    # Send by gateway to controller when startup is complete
    I_GATEWAY_READY = 14


class Stream(IntEnum):
    """MySensors stream types."""

    # Request new FW, payload contains current FW details
    ST_FIRMWARE_CONFIG_REQUEST = 0
    # New FW details to initiate OTA FW update
    ST_FIRMWARE_CONFIG_RESPONSE = 1
    ST_FIRMWARE_REQUEST = 2  # Request FW block
    ST_FIRMWARE_RESPONSE = 3  # Response FW block
    ST_SOUND = 4  # Sound
    ST_IMAGE = 5  # Image


INTERNAL_COMMAND_TYPE = Command.internal

NODE_ID_REQUEST_TYPES = {Internal.I_ID_REQUEST, Internal.I_ID_RESPONSE}

STRICT_SYSTEM_COMMAND_TYPES = {
    Command.internal.value,
    Command.stream.value,
}

VALID_SYSTEM_COMMAND_TYPES = {
    Command.presentation.value,
    Command.internal.value,
    Command.stream.value,
}

VALID_COMMAND_TYPES = {
    Command.presentation: list(Presentation),
    Command.set: list(SetReq),
    Command.req: list(SetReq),
    Command.internal: list(Internal),
    Command.stream: list(Stream),
}

VALID_MESSAGE_TYPES = {
    Presentation.S_DOOR: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_MOTION: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_SMOKE: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_LIGHT: [SetReq.V_LIGHT, SetReq.V_WATT],
    Presentation.S_DIMMER: [SetReq.V_LIGHT, SetReq.V_DIMMER, SetReq.V_WATT],
    Presentation.S_COVER: [SetReq.V_UP, SetReq.V_DOWN, SetReq.V_STOP, SetReq.V_DIMMER],
    Presentation.S_TEMP: [SetReq.V_TEMP],
    Presentation.S_HUM: [SetReq.V_HUM],
    Presentation.S_BARO: [SetReq.V_PRESSURE, SetReq.V_FORECAST],
    Presentation.S_WIND: [SetReq.V_WIND, SetReq.V_GUST, SetReq.V_DIRECTION],
    Presentation.S_RAIN: [SetReq.V_RAIN, SetReq.V_RAINRATE],
    Presentation.S_UV: [SetReq.V_UV],
    Presentation.S_WEIGHT: [SetReq.V_WEIGHT, SetReq.V_IMPEDANCE],
    Presentation.S_POWER: [SetReq.V_WATT, SetReq.V_KWH],
    Presentation.S_HEATER: [SetReq.V_HEATER, SetReq.V_HEATER_SW, SetReq.V_TEMP],
    Presentation.S_DISTANCE: [SetReq.V_DISTANCE],
    Presentation.S_LIGHT_LEVEL: [SetReq.V_LIGHT_LEVEL],
    Presentation.S_ARDUINO_NODE: [],
    Presentation.S_ARDUINO_RELAY: [],
    Presentation.S_LOCK: [SetReq.V_LOCK_STATUS],
    Presentation.S_IR: [SetReq.V_IR_SEND, SetReq.V_IR_RECEIVE],
    Presentation.S_WATER: [SetReq.V_FLOW, SetReq.V_VOLUME],
    Presentation.S_AIR_QUALITY: [SetReq.V_DUST_LEVEL],
    Presentation.S_CUSTOM: list(SetReq),
    Presentation.S_DUST: [SetReq.V_DUST_LEVEL],
    Presentation.S_SCENE_CONTROLLER: [SetReq.V_SCENE_ON, SetReq.V_SCENE_OFF],
}
