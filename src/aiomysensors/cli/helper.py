"""Provide CLI helpers."""

import asyncio
from collections.abc import Awaitable, Callable
import logging

from aiomysensors.exceptions import (
    AIOMySensorsError,
    MissingChildError,
    MissingNodeError,
    UnsupportedMessageError,
)
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
    gateway = await gateway_factory()

    async with gateway:
        while True:
            try:
                await handle_gateway(gateway)
            except MissingNodeError as err:
                LOGGER.debug("Missing node: %s", err.node_id)
            except MissingChildError as err:
                LOGGER.debug("Missing child: %s", err.child_id)
            except UnsupportedMessageError as err:
                LOGGER.warning("Unsupported message: %s", err)
            except AIOMySensorsError:
                LOGGER.exception("Error")
                break


async def handle_gateway(gateway: Gateway) -> None:
    """Handle the gateway calls."""
    async for msg in gateway.listen():  # pragma: no cover
        level = logging.DEBUG if msg.message_type == 9 else logging.INFO
        LOGGER.log(level, "Received: %s", msg)
