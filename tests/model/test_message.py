"""Test the message model."""
import pytest
from marshmallow.exceptions import ValidationError

from aiomysensors.model.message import Message, MessageSchema


@pytest.fixture(name="schema")
def schema_fixture():
    """Return a schema."""
    return MessageSchema()


def test_dump(schema):
    """Test dump of message."""
    msg = Message()

    cmd = schema.dump(msg)

    assert cmd == "0;0;0;0;0;\n"

    msg.node_id = 1
    msg.child_id = 255
    msg.command = 3
    msg.ack = 0
    msg.message_type = 0
    msg.payload = 57

    cmd = schema.dump(msg)

    assert cmd == "1;255;3;0;0;57\n"


def test_load(schema):
    """Test load of message."""
    msg = schema.load("1;255;3;0;0;57\n")
    assert msg.node_id == 1
    assert msg.child_id == 255
    assert msg.command == 3
    assert msg.ack == 0
    assert msg.message_type == 0
    assert msg.payload == "57"


def test_load_bad_message(schema):
    """Test load of bad message."""
    # Message that fails loading
    with pytest.raises(ValidationError):
        schema.load("bad;bad;bad;bad;bad;bad\n")
