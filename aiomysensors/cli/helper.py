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
        LOGGER.info("Exiting CLI")


async def start_gateway(handler: Callable, gateway: Gateway) -> None:
    """Start the gateway."""
    reconnect_interval = 3

    while True:
        try:
            await handler(gateway)
        except AIOMySensorsError as err:
            LOGGER.error(
                "Error '%s'. Reconnecting in %s seconds", err, reconnect_interval
            )
            await asyncio.sleep(reconnect_interval)


async def handle_gateway(gateway: Gateway) -> None:
    """Handle the gateway calls."""
    async with gateway.transport:
        async for msg in gateway.listen():
            level = logging.DEBUG if msg.message_type == 9 else logging.INFO
            LOGGER.log(level, "Received message: %s", msg)
