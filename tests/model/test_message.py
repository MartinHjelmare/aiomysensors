"""Test the message model."""

import pytest

from aiomysensors.exceptions import InvalidMessageError
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.model.protocol import PROTOCOL_VERSIONS


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
def test_dump(message_schema: MessageSchema) -> None:
    """Test dump of message."""
    msg = Message()

    cmd = msg.to_string(message_schema)

    assert cmd == "0;0;0;0;0;\n"

    msg.node_id = 1
    msg.child_id = 255
    msg.command = 3
    msg.ack = 0
    msg.message_type = 0
    msg.payload = "57"

    cmd = msg.to_string(message_schema)

    assert cmd == "1;255;3;0;0;57\n"


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
def test_load(message_schema: MessageSchema) -> None:
    """Test load of message."""
    msg = Message.from_string("1;255;3;0;0;57\n", message_schema)
    assert msg.node_id == 1
    assert msg.child_id == 255
    assert msg.command == 3
    assert msg.ack == 0
    assert msg.message_type == 0
    assert msg.payload == "57"


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
def test_load_internal_id_request(message_schema: MessageSchema) -> None:
    """Test load internal id request message."""
    msg = Message.from_string("1;5;3;0;3;\n", message_schema)
    assert msg.node_id == 1
    assert msg.child_id == 5
    assert msg.command == 3
    assert msg.ack == 0
    assert msg.message_type == 3
    assert msg.payload == ""


@pytest.mark.parametrize("message_schema", list(PROTOCOL_VERSIONS), indirect=True)
def test_load_bad_message(message_schema: MessageSchema) -> None:
    """Test load of bad message."""
    # Message that fails on bad node id
    with pytest.raises(InvalidMessageError):
        Message.from_string("bad;0;0;0;0;0\n", message_schema)

    # Message that fails on bad child id
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;bad;0;0;0;0\n", message_schema)

    # Message that fails on bad command type
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;0;bad;0;0;0\n", message_schema)

    # Message that fails on bad ack flag
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;0;0;bad;0;0\n", message_schema)

    # Message that fails on bad message type
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;0;0;0;bad;0\n", message_schema)

    # Message that fails on range of node id
    with pytest.raises(InvalidMessageError):
        Message.from_string("300;0;0;0;0;0\n", message_schema)

    # Message that fails on range of child id
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;300;0;0;0;0\n", message_schema)

    # Message that fails on range of command type
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;0;-1;0;0;0\n", message_schema)

    # Message that fails on range of ack flag
    with pytest.raises(InvalidMessageError):
        Message.from_string("0;0;0;3;0;0\n", message_schema)

    # Message with incorrect child id and command type combination
    with pytest.raises(InvalidMessageError):
        Message.from_string("1;5;3;0;0;0\n", message_schema)

    # Message with incorrect child id and command type combination
    with pytest.raises(InvalidMessageError):
        Message.from_string("1;255;1;0;0;0\n", message_schema)
