"""Provide CLI helpers."""
import asyncio
import logging
from typing import Callable

from aiomysensors.exceptions import AIOMySensorsError
from aiomysensors.gateway import Gateway

LOGGER = logging.getLogger("aiomysensors")


def run_gateway(handler: Callable, gateway: Gateway) -> None:
    """Run a gateway."""
    LOGGER.info("Starting gateway")
    try:
        asyncio.run(start_gateway(handler, gateway))
    except KeyboardInterrupt:
        pass
    finally:
        LOGGER.info("Exiting CLI")


async def start_gateway(handler: Callable, gateway: Gateway) -> None:
    """Start the gateway."""
    try:
        await handler(gateway)
    except AIOMySensorsError as err:
        LOGGER.error("Error '%s'", err)


async def handle_gateway(gateway: Gateway) -> None:
    """Handle the gateway calls."""
    async with gateway.transport:  # pragma: no cover
        async for msg in gateway.listen():
            level = logging.DEBUG if msg.message_type == 9 else logging.INFO
            LOGGER.log(level, "Received message: %s", msg)
