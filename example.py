"""Show a minimal example using aiomysensors."""

import asyncio
import contextlib

from aiomysensors import AIOMySensorsError, Gateway, SerialTransport


async def run_gateway() -> None:
    """Run a serial gateway."""
    port = "/dev/ttyACM0"
    baud = 115200
    transport = SerialTransport(port, baud)

    try:
        async with Gateway(transport) as gateway:
            async for _message in gateway.listen():
                pass
    except AIOMySensorsError:
        pass


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(run_gateway())
