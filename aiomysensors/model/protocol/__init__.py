"""Provide MySensors protocols."""
from importlib import import_module
from types import ModuleType

from packaging import version


DEFAULT_PROTOCOL_VERSION = "1.4"
DEFAULT_PROTOCOL_PATH = "aiomysensors.model.protocol.protocol_14"
PROTOCOL_VERSIONS = {
    DEFAULT_PROTOCOL_VERSION: DEFAULT_PROTOCOL_PATH,
}


def get_protocol(protocol_version: str) -> ModuleType:
    """Return the protocol module for the protocol_version."""
    path = next(
        (
            PROTOCOL_VERSIONS[_protocol_version]
            for _protocol_version in sorted(PROTOCOL_VERSIONS, reverse=True)
            if version.parse(protocol_version) >= version.parse(_protocol_version)
        ),
        DEFAULT_PROTOCOL_PATH,
    )
    return import_module(path)
