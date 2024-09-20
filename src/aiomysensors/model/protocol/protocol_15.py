"""Provide the protocol for MySensors version 1.5."""

from enum import IntEnum

from .protocol_14 import (  # noqa: F401
    INTERNAL_COMMAND_TYPE,
    STRICT_SYSTEM_COMMAND_TYPES,
    VALID_SYSTEM_COMMAND_TYPES,
    Command,
    Stream,
)
from .protocol_14 import (
    IncomingMessageHandler as IncomingMessageHandler14,
)
from .protocol_14 import (
    OutgoingMessageHandler as OutgoingMessageHandler14,
)


class IncomingMessageHandler(IncomingMessageHandler14):
    """Represent a message handler."""


class OutgoingMessageHandler(OutgoingMessageHandler14):
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


class SetReq(IntEnum):
    """MySensors set/req types."""

    V_TEMP = 0  # Temperature
    V_HUM = 1  # Humidity
    V_STATUS = 2  # Binary status, 0=off, 1=on
    # Deprecated. Alias for V_STATUS. Light Status.0=off 1=on
    V_LIGHT = 2
    V_PERCENTAGE = 3  # Percentage value. 0-100 (%)
    # Deprecated. Alias for V_PERCENTAGE. Dimmer value. 0-100 (%)
    V_DIMMER = 3
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
    # Armed status of a security sensor.  1=Armed, 0=Bypassed
    V_ARMED = 15
    # Tripped status of a security sensor. 1=Tripped, 0=Untripped
    V_TRIPPED = 16
    V_WATT = 17  # Watt value for power meters
    V_KWH = 18  # Accumulated number of KWH for a power meter
    V_SCENE_ON = 19  # Turn on a scene
    V_SCENE_OFF = 20  # Turn off a scene
    # Mode of heater. One of "Off", "HeatOn", "CoolOn", or "AutoChangeOver"
    V_HVAC_FLOW_STATE = 21
    # HVAC/Heater fan speed ("Min", "Normal", "Max", "Auto")
    V_HVAC_SPEED = 22
    # Uncalibrated light level. 0-100%. Use V_LEVEL for light level in lux.
    V_LIGHT_LEVEL = 23
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
    V_LEVEL = 37  # Used for sending level-value
    V_DUST_LEVEL = 37  # Dust level
    V_VOLTAGE = 38  # Voltage level
    V_CURRENT = 39  # Current level
    # RGB value transmitted as ASCII hex string (I.e "ff0000" for red)
    V_RGB = 40
    # RGBW value transmitted as ASCII hex string (I.e "ff0000ff" for red +
    # full white)
    V_RGBW = 41
    # Optional unique sensor id (e.g. OneWire DS1820b ids)
    V_ID = 42
    # Allows sensors to send in a string representing the unit prefix to be
    # displayed in GUI.
    # This is not parsed by controller! E.g. cm, m, km, inch.
    V_UNIT_PREFIX = 43
    V_HVAC_SETPOINT_COOL = 44  # HVAC cold setpoint (Integer between 0-100)
    V_HVAC_SETPOINT_HEAT = 45  # HVAC/Heater setpoint (Integer between 0-100)
    # Flow mode for HVAC ("Auto", "ContinuousOn", "PeriodicOn")
    V_HVAC_FLOW_MODE = 46


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
    # Used between sensors when initiating signing.
    I_REQUEST_SIGNING = 15
    # Used between sensors when requesting nonce.
    I_GET_NONCE = 16
    # Used between sensors for nonce response.
    I_GET_NONCE_RESPONSE = 17


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
    Presentation.S_POWER: [SetReq.V_WATT, SetReq.V_KWH, SetReq.V_UNIT_PREFIX],
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
    Presentation.S_IR: [SetReq.V_IR_SEND, SetReq.V_IR_RECEIVE],
    Presentation.S_WATER: [SetReq.V_FLOW, SetReq.V_VOLUME, SetReq.V_UNIT_PREFIX],
    Presentation.S_AIR_QUALITY: [SetReq.V_LEVEL, SetReq.V_UNIT_PREFIX],
    Presentation.S_CUSTOM: [
        SetReq.V_VAR1,
        SetReq.V_VAR2,
        SetReq.V_VAR3,
        SetReq.V_VAR4,
        SetReq.V_VAR5,
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
}
