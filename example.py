"""Show a minimal example using aiomysensors."""
import asyncio

from aiomysensors import AIOMySensorsError, Gateway, SerialTransport


async def run_gateway() -> None:
    """Run a serial gateway."""
    port = "/dev/ttyACM0"
    baud = 115200
    transport = SerialTransport(port, baud)
    gateway = Gateway(transport)

    try:
        async with gateway.transport:
            async for message in gateway.listen():
                print("Message received:", message)
    except AIOMySensorsError as err:
        print("Error:", err)


if __name__ == "__main__":
    try:
        asyncio.run(run_gateway())
    except KeyboardInterrupt:
        pass
