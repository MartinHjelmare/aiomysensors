"""Test the MQTT transport."""
from unittest.mock import call, patch

import pytest

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
