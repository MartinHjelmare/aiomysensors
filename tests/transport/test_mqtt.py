"""Test the MQTT transport."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call, patch

from aiomqtt import Message as AIOMQTTMessage
from aiomqtt import MqttError
from paho.mqtt.client import MQTTMessage
import pytest

from aiomysensors.exceptions import TransportError, TransportFailedError
from aiomysensors.model.message import Message, MessageSchema
from aiomysensors.transport.mqtt import PAHO_MQTT_LOGGER, MQTTClient

HOST = "mqtt.org"
PORT = 1111
IN_PREFIX = "mysensors/test-out"
OUT_PREFIX = "mysensors/test-in"
UUID = 1234
MQTT_CLIENT_ID = f"aiomysensors-{UUID}"


@pytest.fixture(name="mqtt")
def mqtt_fixture() -> Generator[MagicMock, None, None]:
    """Mock the MQTT connection."""
    with patch(
        "aiomysensors.transport.mqtt.AsyncioClient",
        autospec=True,
    ) as asyncio_client_class:
        yield asyncio_client_class


@pytest.fixture(name="client_id", autouse=True)
def mqtt_client_id_fixture() -> Generator[str, None, None]:
    """Mock the UUID for the client id."""
    with patch("aiomysensors.transport.mqtt.uuid.uuid4") as uuid4:
        uuid4.return_value.int = UUID
        yield MQTT_CLIENT_ID


async def test_connect_disconnect(mqtt: AsyncMock, client_id: str) -> None:
    """Test MQTT transport connect and disconnect."""
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        identifier=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )
    mqtt_client = mqtt.return_value

    assert mqtt_client.__aenter__.call_count == 1

    await transport.disconnect()

    assert mqtt_client.__aexit__.call_count == 1


async def test_connect_failure(mqtt: AsyncMock) -> None:
    """Test MQTT transport connect failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.__aenter__.side_effect = MqttError("Boom")
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    with pytest.raises(TransportError):
        await transport.connect()


async def test_disconnect_failure(mqtt: AsyncMock, client_id: str) -> None:
    """Test MQTT transport disconnect failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.__aexit__.side_effect = MqttError("Boom")
    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        identifier=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    # Disconnect error should be caught.
    await transport.disconnect()

    assert mqtt_client.__aexit__.call_count == 1


async def test_read_write(mqtt: AsyncMock, client_id: str) -> None:
    """Test MQTT transport read and write."""
    mqtt_client = mqtt.return_value
    topic = f"{IN_PREFIX}/0/255/3/1/11"
    payload = "test"
    mqtt_message = MQTTMessage(topic=topic.encode(encoding="utf-8"))
    mqtt_message.payload = payload.encode()
    msg = AIOMQTTMessage._from_paho_message(mqtt_message)  # noqa: SLF001
    messages = [msg]

    async def mock_messages() -> AsyncGenerator[AIOMQTTMessage, None]:
        """Mock the messages generator."""
        for message in messages:
            yield message

    type(mqtt_client).messages = PropertyMock(return_value=mock_messages())

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        identifier=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    await asyncio.sleep(0)
    read = await transport.read()
    assert read == "0;255;3;1;11;test"

    await transport.write(read)
    assert mqtt_client.publish.call_count == 1
    assert mqtt_client.publish.call_args == call(
        f"{OUT_PREFIX}/0/255/3/1/11",
        qos=1,
        retain=False,
        timeout=10,
        payload=payload,
    )

    # Test writing with empty payload
    mqtt_client.publish.reset_mock()

    await transport.write("0;255;3;1;11;\n")
    assert mqtt_client.publish.call_count == 1
    assert mqtt_client.publish.call_args == call(
        f"{OUT_PREFIX}/0/255/3/1/11",
        qos=1,
        retain=False,
        timeout=10,
    )

    await transport.disconnect()

    assert mqtt_client.__aexit__.call_count == 1


async def test_read_failure(mqtt: AsyncMock, client_id: str) -> None:
    """Test MQTT transport read failure."""
    mqtt_client = mqtt.return_value
    topic = f"{IN_PREFIX}/0/0/0/0/0"
    payload = "test"
    mqtt_message = MQTTMessage(topic=topic.encode(encoding="utf-8"))
    mqtt_message.payload = payload.encode()
    msg = AIOMQTTMessage._from_paho_message(mqtt_message)  # noqa: SLF001
    messages = [msg]

    async def mock_messages() -> AsyncGenerator[AIOMQTTMessage, None]:
        """Mock the messages generator."""
        for message in messages:
            yield message
            raise MqttError("Boom")

    type(mqtt_client).messages = PropertyMock(return_value=mock_messages())

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        identifier=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    await asyncio.sleep(0)
    read = await transport.read()

    assert read == "0;0;0;0;0;test"

    with pytest.raises(TransportFailedError):
        await transport.read()

    await transport.disconnect()

    assert mqtt_client.__aexit__.call_count == 1


async def test_write_failure(
    mqtt: AsyncMock, client_id: str, message: Message, message_schema: MessageSchema
) -> None:
    """Test MQTT transport write failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.publish.side_effect = MqttError("Boom")
    cmd = message.to_string(message_schema)

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    await transport.connect()

    assert mqtt.call_count == 1
    assert mqtt.call_args == call(
        HOST,
        PORT,
        identifier=client_id,
        logger=PAHO_MQTT_LOGGER,
        clean_session=True,
    )

    with pytest.raises(TransportFailedError):
        await transport.write(cmd)

    assert mqtt_client.publish.call_count == 1

    await transport.disconnect()

    assert mqtt_client.__aexit__.call_count == 1


async def test_subscribe_failure(mqtt: AsyncMock) -> None:
    """Test MQTT transport subscribe failure."""
    mqtt_client = mqtt.return_value
    mqtt_client.subscribe.side_effect = MqttError("Boom")

    transport = MQTTClient(HOST, PORT, IN_PREFIX, OUT_PREFIX)

    with pytest.raises(TransportError):
        await transport.connect()

    assert mqtt.call_count == 1
