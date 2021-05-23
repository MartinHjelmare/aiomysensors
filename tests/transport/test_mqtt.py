"""Test the MQTT transport."""
import asyncio
from contextlib import asynccontextmanager
from unittest.mock import call, patch

from asyncio_mqtt import MqttError
from paho.mqtt.client import MQTTMessage
import pytest

from aiomysensors.exceptions import TransportError, TransportFailedError
from aiomysensors.transport.mqtt import PAHO_MQTT_LOGGER, MQTTClient

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

HOST = "mqtt.org"
PORT = 1111
IN_PREFIX = "mysensors/test-out"
OUT_PREFIX = "mysensors/test-in"
MQTT_CLIENT_ID = "mqtt_client_id"


@pytest.fixture(name="mqtt")
def mqtt_fixture():
    """Mock the MQTT connection."""
    with patch(
        "aiomysensors.transport.mqtt.AsyncioClient", autospec=True
    ) as asyncio_client_class:
        yield asyncio_client_class


@pytest.fixture(name="client_id", autouse=True)
def mqtt_client_id_fixture():
    """Mock the client id."""
    with patch("aiomysensors.transport.mqtt.mqtt.base62", return_value=MQTT_CLIENT_ID):
        yield MQTT_CLIENT_ID


async def test_connect_disconnect(mqtt, client_id):
    """Test MQTT transport connect and disconnect."""
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        client_id=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )
    mqtt_client = mqtt.return_value

    assert mqtt_client.connect.call_count == 1
    assert mqtt_client.connect.call_args == call(timeout=10)

    await transport.disconnect()

    assert mqtt_client.disconnect.call_count == 1
    assert mqtt_client.disconnect.call_args == call(timeout=10)


async def test_connect_failure(mqtt):
    """Test MQTT transport connect failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.connect.side_effect = MqttError("Boom")
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    with pytest.raises(TransportError):
        await transport.connect()


async def test_disconnect_failure(mqtt, client_id):
    """Test MQTT transport disconnect failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.disconnect.side_effect = MqttError("Boom")
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        client_id=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    # Disconnect error should be caught.
    await transport.disconnect()

    assert mqtt_client.disconnect.call_count == 1


async def test_read_write(mqtt, client_id):
    """Test MQTT transport read and write."""
    mqtt_client = mqtt.return_value
    topic = f"{IN_PREFIX}/0/255/3/1/11"
    payload = "test"
    msg = MQTTMessage()
    msg.topic = topic.encode()
    msg.payload = payload.encode()
    messages = [msg]

    async def mock_messages():
        """Mock the messages generator."""
        for message in messages:
            yield message

    @asynccontextmanager
    async def filter_messages():
        """Mock filter messages."""
        yield mock_messages()

    mqtt_client.unfiltered_messages.side_effect = filter_messages

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        client_id=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    await asyncio.sleep(0)
    read = await transport.read()
    assert read == "0;255;3;1;11;test"

    await transport.write(read)
    assert mqtt_client.publish.call_count == 1
    assert mqtt_client.publish.call_args == call(
        f"{OUT_PREFIX}/0/255/3/1/11", qos=1, retain=False, timeout=10, payload=payload
    )

    await transport.disconnect()

    assert mqtt_client.disconnect.call_count == 1


async def test_read_failure(mqtt, client_id):
    """Test MQTT transport read failure."""
    mqtt_client = mqtt.return_value
    topic = f"{IN_PREFIX}/0/0/0/0/0"
    payload = "test"
    msg = MQTTMessage()
    msg.topic = topic.encode()
    msg.payload = payload.encode()
    messages = [msg]

    async def mock_messages():
        """Mock the messages generator."""
        for message in messages:
            yield message

    @asynccontextmanager
    async def filter_messages():
        """Mock filter messages."""
        yield mock_messages()
        raise MqttError("Boom")

    mqtt_client.unfiltered_messages.side_effect = filter_messages

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        client_id=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    await asyncio.sleep(0)
    read = await transport.read()

    assert read == "0;0;0;0;0;test"

    with pytest.raises(TransportFailedError):
        await transport.read()

    await transport.disconnect()

    assert mqtt_client.disconnect.call_count == 1


async def test_write_failure(mqtt, client_id, message, message_schema):
    """Test MQTT transport write failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.publish.side_effect = MqttError("Boom")
    cmd = message_schema.dump(message)

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        client_id=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    with pytest.raises(TransportFailedError):
        await transport.write(cmd)

    assert mqtt_client.publish.call_count == 1

    await transport.disconnect()

    assert mqtt_client.disconnect.call_count == 1


async def test_subscribe_failure(mqtt):
    """Test MQTT transport subscribe failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.subscribe.side_effect = MqttError("Boom")

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    with pytest.raises(TransportError):
        await transport.connect()

    assert mqtt.call_count == 1
