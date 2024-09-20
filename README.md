# aiomysensors

<p align="center">
  <a href="https://github.com/MartinHjelmare/aiomysensors/actions/workflows/ci.yml?query=branch%3Amain">
    <img src="https://img.shields.io/github/actions/workflow/status/MartinHjelmare/aiomysensors/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI Status" >
  </a>
  <a href="https://codecov.io/gh/MartinHjelmare/aiomysensors">
    <img src="https://img.shields.io/codecov/c/github/MartinHjelmare/aiomysensors.svg?logo=codecov&logoColor=fff&style=flat-square" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://python-poetry.org/">
    <img src="https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json" alt="Poetry">
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/aiomysensors/">
    <img src="https://img.shields.io/pypi/v/aiomysensors.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/aiomysensors.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/aiomysensors.svg?style=flat-square" alt="License">
</p>

---

**Source Code**: <a href="https://github.com/MartinHjelmare/aiomysensors" target="_blank">https://github.com/MartinHjelmare/aiomysensors </a>

---

Python asyncio package to connect to MySensors gateways.

## Installation

Install this via pip (or your favourite package manager):

`pip install aiomysensors`

## Example

```py
"""Show a minimal example using aiomysensors."""
import asyncio

from aiomysensors import AIOMySensorsError, Gateway, SerialTransport


async def run_gateway() -> None:
    """Run a serial gateway."""
    port = "/dev/ttyACM0"
    baud = 115200
    transport = SerialTransport(port, baud)

    try:
        async with Gateway(transport) as gateway:
            async for message in gateway.listen():
                print("Message received:", message)
    except AIOMySensorsError as err:
        print("Error:", err)


if __name__ == "__main__":
    try:
        asyncio.run(run_gateway())
    except KeyboardInterrupt:
        pass
```

## Command Line Interface

There's a CLI for testing purposes.

```sh
aiomysensors --debug serial-gateway -p /dev/ttyACM0
```

## Credits

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
