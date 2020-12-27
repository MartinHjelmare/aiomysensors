# aiomysensors

Python asyncio package to connect to MySensors gateways.

## MySensors version support

The following versions are supported:

- 1.4
- 1.5

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
```

## Command Line Interface

There's a CLI for testing purposes.

```sh
aiomysensors --debug serial-gateway -p /dev/ttyACM0
```

## Development

- Install and set up development environment.

  ```sh
  pip install -r requirements_dev.txt
  ```

  This will install all requirements.
It will also install this package in development mode, so that code changes are applied immediately without reinstall necessary.

- Here's a list of development tools we use.
  - [black](https://pypi.org/project/black/)
  - [flake8](https://pypi.org/project/flake8/)
  - [mypy](https://pypi.org/project/mypy/)
  - [pydocstyle](https://pypi.org/project/pydocstyle/)
  - [pylint](https://pypi.org/project/pylint/)
  - [pytest](https://pypi.org/project/pytest/)
  - [tox](https://pypi.org/project/tox/)
- It's recommended to use the corresponding code formatter and linters also in your code editor to get instant feedback. A popular editor that can do this is [`vscode`](https://code.visualstudio.com/).
- Run all tests, check formatting and linting.

  ```sh
  tox
  ```

- Run a single tox environment.

  ```sh
  tox -e lint
  ```

- Reinstall all tox environments.

  ```sh
  tox -r
  ```

- Run pytest and all tests.

  ```sh
  pytest
  ```

- Run pytest and calculate coverage for the package.

  ```sh
  pytest --cov-report term-missing --cov=aiomysensors
  ```
