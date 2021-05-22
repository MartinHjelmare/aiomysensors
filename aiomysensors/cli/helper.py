"""Provide CLI helpers."""
import asyncio
import logging
from typing import Awaitable, Callable

from aiomysensors.exceptions import AIOMySensorsError
from aiomysensors.gateway import Gateway

LOGGER = logging.getLogger("aiomysensors")

GatewayFactory = Callable[[], Awaitable[Gateway]]


def run_gateway(gateway_factory: GatewayFactory) -> None:
    """Run a gateway."""
    LOGGER.info("Starting gateway")
    try:
        asyncio.run(start_gateway(gateway_factory))
    except KeyboardInterrupt:
        pass
    finally:
        LOGGER.info("Exiting CLI")


async def start_gateway(gateway_factory: GatewayFactory) -> None:
    """Start the gateway."""
    try:
        await handle_gateway(gateway_factory)
    except AIOMySensorsError as err:
        LOGGER.error("Error '%s'", err)


async def handle_gateway(gateway_factory: GatewayFactory) -> None:
    """Handle the gateway calls."""
    gateway = await gateway_factory()

    async with gateway:  # pragma: no cover
        async for msg in gateway.listen():
            level = logging.DEBUG if msg.message_type == 9 else logging.INFO
            LOGGER.log(level, "Received message: %s", msg)
