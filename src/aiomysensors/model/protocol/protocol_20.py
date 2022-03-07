"""Provide the protocol for MySensors version 2.0."""
from enum import IntEnum
from typing import Any, Callable, TypeVar, cast

# pylint: disable=unused-import
from . import SYSTEM_CHILD_ID
from ...exceptions import MissingChildError, MissingNodeError
from ...gateway import Gateway, MessageBuffer
from ..message import Message
from .protocol_15 import (  # noqa: F401
    INTERNAL_COMMAND_TYPE,
    STRICT_SYSTEM_COMMAND_TYPES,
    VALID_SYSTEM_COMMAND_TYPES,
    Command,
    IncomingMessageHandler as IncomingMessageHandler15,
    OutgoingMessageHandler as OutgoingMessageHandler15,
)
from .protocol_15 import Stream  # noqa: F401

Func = TypeVar("Func", bound=Callable[..., Any])


def handle_missing_node_child(func: Func) -> Func:
    """Handle a missing node or child."""

    async def wrapper(  # type: ignore[no-untyped-def]
        message_handlers,
        gateway,
        message,
        message_buffer,
    ):
        """Wrap a message handler."""
        try:
            message = await func(message_handlers, gateway, message, message_buffer)
        except (MissingNodeError, MissingChildError):
            presentation_message = Message(
                node_id=message.node_id,
                child_id=SYSTEM_CHILD_ID,
                command=Command.internal,
                message_type=Internal.I_PRESENTATION,
            )
            if (
                presentation_message.node_id,
                presentation_message.child_id,
                presentation_message.message_type,
            ) not in message_buffer.internal_messages:
                await gateway.send(presentation_message, message_buffer=False)
            # Buffer one message to avoid spamming gateway.
            await gateway.send(presentation_message, message_buffer=True)

            raise

        return message

    return cast(Func, wrapper)


class IncomingMessageHandler(IncomingMessageHandler15):
    """Represent a message handler."""

    # pylint: disable=unused-argument

    @classmethod
    async def _handle_sleep_buffer(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process the sleep buffer and send it to the woken node."""
        node_messages = {
            key: buffer_message
            for key, buffer_message in message_buffer.set_messages.items()
            if buffer_message.node_id == message.node_id
        }
        for key, buffer_message in node_messages.items():
            await gateway.send(buffer_message, message_buffer=False)
            # clear the sleep buffer for this node
            message_buffer.set_messages.pop(key)

        return message

    @classmethod
    @handle_missing_node_child
    async def handle_presentation(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process a presentation message."""
        key = (
            message.node_id,
            message.child_id,
            Internal.I_PRESENTATION,
        )
        if key in message_buffer.internal_messages:
            message_buffer.internal_messages.pop(key)
        return await super().handle_presentation(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_set(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process a set message."""
        return await super().handle_set(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_req(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process a req message."""
        return await super().handle_req(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_stream(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process a stream message."""
        return await super().handle_stream(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_i_battery_level(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal battery level message."""
        return await super().handle_i_battery_level(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_i_sketch_name(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal sketch name message."""
        return await super().handle_i_sketch_name(gateway, message, message_buffer)

    @classmethod
    @handle_missing_node_child
    async def handle_i_sketch_version(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal sketch version message."""
        return await super().handle_i_sketch_version(gateway, message, message_buffer)

    @classmethod
    async def handle_i_gateway_ready(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal gateway ready message."""
        discover_message = Message(
            node_id=255,
            child_id=message.child_id,
            command=message.command,
            message_type=Internal.I_DISCOVER,
        )
        await gateway.send(discover_message, message_buffer=False)
        return message

    @classmethod
    @handle_missing_node_child
    async def handle_i_discover_response(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal discover response message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        return message

    @classmethod
    @handle_missing_node_child
    async def handle_i_heartbeat_response(
        cls, gateway: Gateway, message: Message, message_buffer: MessageBuffer
    ) -> Message:
        """Process an internal heartbeat response message."""
        if message.node_id not in gateway.nodes:
            raise MissingNodeError(message.node_id)

        node = gateway.nodes[message.node_id]
        node.sleeping = True
        node.heartbeat = int(message.payload)

        message = await cls._handle_sleep_buffer(gateway, message, message_buffer)

        return message


class OutgoingMessageHandler(OutgoingMessageHandler15):
    """Represent a handler for outgoing messages."""


class Presentation(IntEnum):
    """MySensors presentation types."""

    S_DOOR = 0
    S_MOTION = 1
    S_SMOKE = 2
    S_BINARY = 3
    S_LIGHT = 3  # Alias for S_BINARY
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
    S_ARDUINO_REPEATER_NODE = 18
    S_ARDUINO_RELAY = 18  # Alias for S_ARDUINO_REPEATER_NODE
    S_LOCK = 19
    S_IR = 20
    S_WATER = 21
    S_AIR_QUALITY = 22
    S_CUSTOM = 23
    S_DUST = 24
    S_SCENE_CONTROLLER = 25
    S_RGB_LIGHT = 26
    S_RGBW_LIGHT = 27
    S_COLOR_SENSOR = 28
    S_HVAC = 29
    S_MULTIMETER = 30
    S_SPRINKLER = 31
    S_WATER_LEAK = 32
    S_SOUND = 33
    S_VIBRATION = 34
    S_MOISTURE = 35
    S_INFO = 36
    S_GAS = 37
    S_GPS = 38
    S_WATER_QUALITY = 39


class SetReq(IntEnum):
    """MySensors set/req types."""

    V_TEMP = 0  # S_TEMP, S_HEATER, S_HVAC. Temperature.
    V_HUM = 1  # S_HUM. Humidity.
    # S_LIGHT, S_DIMMER, S_SPRINKLER, S_HVAC, S_HEATER.
    # Binary status, 0=off, 1=on.
    V_STATUS = 2
    # Deprecated. Alias for V_STATUS. Light Status.0=off 1=on.
    V_LIGHT = 2
    V_PERCENTAGE = 3  # S_DIMMER. Percentage value 0-100 (%).
    # Deprecated. Alias for V_PERCENTAGE. Dimmer value. 0-100 (%).
    V_DIMMER = 3
    V_PRESSURE = 4  # S_BARO. Atmospheric Pressure.
    # S_BARO. Weather forecast. One of "stable", "sunny", "cloudy", "unstable",
    # "thunderstorm" or "unknown".
    V_FORECAST = 5
    V_RAIN = 6  # S_RAIN. Amount of rain.
    V_RAINRATE = 7  # S_RAIN. Rate of rain.
    V_WIND = 8  # S_WIND. Wind speed.
    V_GUST = 9  # S_WIND. Gust.
    V_DIRECTION = 10  # S_WIND. Wind direction 0-360 (degrees).
    V_UV = 11  # S_UV. UV light level.
    V_WEIGHT = 12  # S_WEIGHT. Weight(for scales etc).
    V_DISTANCE = 13  # S_DISTANCE. Distance.
    V_IMPEDANCE = 14  # S_MULTIMETER, S_WEIGHT. Impedance value.
    # S_DOOR, S_MOTION, S_SMOKE, S_SPRINKLER.
    # Armed status of a security sensor.  1=Armed, 0=Bypassed.
    V_ARMED = 15
    # S_DOOR, S_MOTION, S_SMOKE, S_SPRINKLER, S_WATER_LEAK, S_SOUND,
    # S_VIBRATION, S_MOISTURE.
    # Tripped status of a security sensor. 1=Tripped, 0=Untripped.
    V_TRIPPED = 16
    # S_POWER, S_LIGHT, S_DIMMER, S_RGB_LIGHT, S_RGBW_LIGHT.
    # Watt value for power meters.
    V_WATT = 17
    # S_POWER. Accumulated number of KWH for a power meter.
    V_KWH = 18
    V_SCENE_ON = 19  # S_SCENE_CONTROLLER. Turn on a scene.
    V_SCENE_OFF = 20  # S_SCENE_CONTROLLER. Turn off a scene.
    # S_HEATER, S_HVAC.
    # Mode of heater. One of "Off", "HeatOn", "CoolOn", or "AutoChangeOver"
    V_HVAC_FLOW_STATE = 21
    # S_HEATER, S_HVAC. HVAC/Heater fan speed ("Min", "Normal", "Max", "Auto")
    V_HVAC_SPEED = 22
    # S_LIGHT_LEVEL.
    # Uncalibrated light level. 0-100%. Use V_LEVEL for light level in lux.
    V_LIGHT_LEVEL = 23
    V_VAR1 = 24  # Custom value
    V_VAR2 = 25  # Custom value
    V_VAR3 = 26  # Custom value
    V_VAR4 = 27  # Custom value
    V_VAR5 = 28  # Custom value
    V_UP = 29  # S_COVER. Window covering. Up.
    V_DOWN = 30  # S_COVER. Window covering. Down.
    V_STOP = 31  # S_COVER. Window covering. Stop.
    V_IR_SEND = 32  # S_IR. Send out an IR-command.
    # S_IR. This message contains a received IR-command.
    V_IR_RECEIVE = 33
    V_FLOW = 34  # S_WATER. Flow of water (in meter).
    V_VOLUME = 35  # S_WATER. Water volume.
    # S_LOCK. Set or get lock status. 1=Locked, 0=Unlocked.
    V_LOCK_STATUS = 36
    # S_DUST, S_AIR_QUALITY, S_SOUND (dB), S_VIBRATION (hz),
    # S_LIGHT_LEVEL (lux).
    V_LEVEL = 37
    V_DUST_LEVEL = 37  # Dust level
    V_VOLTAGE = 38  # S_MULTIMETER. Voltage level.
    V_CURRENT = 39  # S_MULTIMETER. Current level.
    # S_RGB_LIGHT, S_COLOR_SENSOR.
    # RGB value transmitted as ASCII hex string (I.e "ff0000" for red)
    V_RGB = 40
    # S_RGBW_LIGHT.
    # RGBW value transmitted as ASCII hex string (I.e "ff0000ff" for red +
    # full white)
    V_RGBW = 41
    # Optional unique sensor id (e.g. OneWire DS1820b ids)
    V_ID = 42  # S_TEMP.
    # S_DUST, S_AIR_QUALITY, S_DISTANCE.
    # Allows sensors to send in a string representing the unit prefix to be
    # displayed in GUI.
    # This is not parsed by controller! E.g. cm, m, km, inch.
    V_UNIT_PREFIX = 43
    # S_HVAC. HVAC cool setpoint (Integer between 0-100).
    V_HVAC_SETPOINT_COOL = 44
    # S_HEATER, S_HVAC. HVAC/Heater setpoint (Integer between 0-100).
    V_HVAC_SETPOINT_HEAT = 45
    # S_HVAC. Flow mode for HVAC ("Auto", "ContinuousOn", "PeriodicOn").
    V_HVAC_FLOW_MODE = 46
    # S_INFO. Text message to display on LCD or controller device
    V_TEXT = 47
    # S_CUSTOM.
    # Custom messages used for controller/inter node specific commands,
    # preferably using S_CUSTOM device type.
    V_CUSTOM = 48
    # S_GPS.
    # GPS position and altitude. Payload: latitude;longitude;altitude(m).
    # E.g. "55.722526;13.017972;18"
    V_POSITION = 49
    V_IR_RECORD = 50  # S_IR. Record IR codes for playback
    V_PH = 51  # S_WATER_QUALITY, water pH.
    # S_WATER_QUALITY, water ORP : redox potential in mV.
    V_ORP = 52
    # S_WATER_QUALITY, water electric conductivity μS/cm (microSiemens/cm).
    V_EC = 53
    V_VAR = 54  # S_POWER, Reactive power: volt-ampere reactive (var)
    V_VA = 55  # S_POWER, Apparent power: volt-ampere (VA)
    # S_POWER
    # Ratio of real power to apparent power.
    # Floating point value in the range [-1,..,1]
    V_POWER_FACTOR = 56


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
    I_HEARTBEAT = 18
    I_PRESENTATION = 19
    I_DISCOVER = 20
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

VALID_MESSAGE_TYPES = {
    Presentation.S_DOOR: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_MOTION: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_SMOKE: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_BINARY: [SetReq.V_STATUS, SetReq.V_WATT],
    Presentation.S_DIMMER: [SetReq.V_STATUS, SetReq.V_PERCENTAGE, SetReq.V_WATT],
    Presentation.S_COVER: [
        SetReq.V_UP,
        SetReq.V_DOWN,
        SetReq.V_STOP,
        SetReq.V_PERCENTAGE,
    ],
    Presentation.S_TEMP: [SetReq.V_TEMP, SetReq.V_ID, SetReq.V_UNIT_PREFIX],
    Presentation.S_HUM: [SetReq.V_HUM, SetReq.V_UNIT_PREFIX],
    Presentation.S_BARO: [SetReq.V_PRESSURE, SetReq.V_FORECAST, SetReq.V_UNIT_PREFIX],
    Presentation.S_WIND: [
        SetReq.V_WIND,
        SetReq.V_GUST,
        SetReq.V_DIRECTION,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_RAIN: [SetReq.V_RAIN, SetReq.V_RAINRATE, SetReq.V_UNIT_PREFIX],
    Presentation.S_UV: [SetReq.V_UV, SetReq.V_UNIT_PREFIX],
    Presentation.S_WEIGHT: [SetReq.V_WEIGHT, SetReq.V_IMPEDANCE, SetReq.V_UNIT_PREFIX],
    Presentation.S_POWER: [
        SetReq.V_WATT,
        SetReq.V_KWH,
        SetReq.V_VAR,
        SetReq.V_VA,
        SetReq.V_POWER_FACTOR,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_HEATER: [
        SetReq.V_STATUS,
        SetReq.V_TEMP,
        SetReq.V_HVAC_SETPOINT_HEAT,
        SetReq.V_HVAC_FLOW_STATE,
    ],
    Presentation.S_DISTANCE: [SetReq.V_DISTANCE, SetReq.V_UNIT_PREFIX],
    Presentation.S_LIGHT_LEVEL: [
        SetReq.V_LIGHT_LEVEL,
        SetReq.V_LEVEL,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_ARDUINO_NODE: [],
    Presentation.S_ARDUINO_REPEATER_NODE: [],
    Presentation.S_LOCK: [SetReq.V_LOCK_STATUS],
    Presentation.S_IR: [SetReq.V_IR_SEND, SetReq.V_IR_RECEIVE, SetReq.V_IR_RECORD],
    Presentation.S_WATER: [SetReq.V_FLOW, SetReq.V_VOLUME, SetReq.V_UNIT_PREFIX],
    Presentation.S_AIR_QUALITY: [SetReq.V_LEVEL, SetReq.V_UNIT_PREFIX],
    Presentation.S_CUSTOM: [
        SetReq.V_VAR1,
        SetReq.V_VAR2,
        SetReq.V_VAR3,
        SetReq.V_VAR4,
        SetReq.V_VAR5,
        SetReq.V_CUSTOM,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_DUST: [SetReq.V_LEVEL, SetReq.V_UNIT_PREFIX],
    Presentation.S_SCENE_CONTROLLER: [SetReq.V_SCENE_ON, SetReq.V_SCENE_OFF],
    Presentation.S_RGB_LIGHT: [SetReq.V_RGB, SetReq.V_WATT, SetReq.V_PERCENTAGE],
    Presentation.S_RGBW_LIGHT: [SetReq.V_RGBW, SetReq.V_WATT, SetReq.V_PERCENTAGE],
    Presentation.S_COLOR_SENSOR: [SetReq.V_RGB, SetReq.V_UNIT_PREFIX],
    Presentation.S_HVAC: [
        SetReq.V_STATUS,
        SetReq.V_TEMP,
        SetReq.V_HVAC_SETPOINT_HEAT,
        SetReq.V_HVAC_SETPOINT_COOL,
        SetReq.V_HVAC_FLOW_STATE,
        SetReq.V_HVAC_FLOW_MODE,
        SetReq.V_HVAC_SPEED,
    ],
    Presentation.S_MULTIMETER: [
        SetReq.V_VOLTAGE,
        SetReq.V_CURRENT,
        SetReq.V_IMPEDANCE,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_SPRINKLER: [SetReq.V_STATUS, SetReq.V_TRIPPED],
    Presentation.S_WATER_LEAK: [SetReq.V_TRIPPED, SetReq.V_ARMED],
    Presentation.S_SOUND: [
        SetReq.V_LEVEL,
        SetReq.V_TRIPPED,
        SetReq.V_ARMED,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_VIBRATION: [
        SetReq.V_LEVEL,
        SetReq.V_TRIPPED,
        SetReq.V_ARMED,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_MOISTURE: [
        SetReq.V_LEVEL,
        SetReq.V_TRIPPED,
        SetReq.V_ARMED,
        SetReq.V_UNIT_PREFIX,
    ],
    Presentation.S_INFO: [SetReq.V_TEXT],
    Presentation.S_GAS: [SetReq.V_FLOW, SetReq.V_VOLUME, SetReq.V_UNIT_PREFIX],
    Presentation.S_GPS: [SetReq.V_POSITION],
    Presentation.S_WATER_QUALITY: [
        SetReq.V_TEMP,
        SetReq.V_PH,
        SetReq.V_ORP,
        SetReq.V_EC,
        SetReq.V_STATUS,
        SetReq.V_UNIT_PREFIX,
    ],
}
