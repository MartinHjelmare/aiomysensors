"""Test persistence."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, call

import pytest

from aiomysensors.exceptions import PersistenceReadError, PersistenceWriteError
from aiomysensors.model.node import Node
from aiomysensors.persistence import Persistence


@pytest.mark.parametrize(
    "persistence_data",
    ["test_aiomysensors_persistence.json", "test_pymysensors_persistence.json"],
    indirect=True,
)
async def test_persistence_load(mock_file: MagicMock, persistence_data: str) -> None:
    """Test persistence load."""
    mock_file.read.return_value = persistence_data
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert mock_file.read.call_count == 1
    assert nodes
    node = nodes.get(1)
    assert node
    assert node.battery_level == 0
    assert node.children
    child = node.children.get(1)
    assert child
    assert child.child_id == 1
    assert child.child_type == 38
    assert child.values
    value = child.values.get(49)
    assert value == "40.741894,-73.989311,12"


async def test_persistence_load_no_data(mock_file: MagicMock) -> None:
    """Test persistence load."""
    mock_file.read.return_value = ""
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert mock_file.read.call_count == 1
    assert not nodes


async def test_persistence_load_missing_file(mock_file: MagicMock) -> None:
    """Test persistence load missing file error."""
    mock_file.read.side_effect = FileNotFoundError("Missing file.")
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert not nodes
    assert mock_file.write.call_count == 1
    assert mock_file.write.call_args == call("{}")


@pytest.mark.parametrize(
    ("error", "read_return_value", "read_side_effect"),
    [
        (PersistenceReadError, None, OSError("Boom")),
        (PersistenceReadError, "bad content", None),
    ],
)
async def test_persistence_load_error(
    mock_file: MagicMock,
    error: type[Exception],
    read_return_value: str | None,
    read_side_effect: Exception | None,
) -> None:
    """Test persistence load error."""
    mock_file.read.return_value = read_return_value
    mock_file.read.side_effect = read_side_effect
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    with pytest.raises(error):
        await persistence.load()

    assert mock_file.read.call_count == 1


async def test_persistence_save(mock_file: MagicMock, persistence_data: str) -> None:
    """Test persistence save."""
    mock_file.read.return_value = persistence_data
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert mock_file.read.call_count == 1
    assert mock_file.write.call_count == 0
    assert nodes
    node = nodes.get(1)
    assert node
    assert node.battery_level == 0
    assert node.children
    child = node.children.get(1)
    assert child
    assert child.child_id == 1
    assert child.child_type == 38
    assert child.values
    value = child.values.get(49)
    assert value == "40.741894,-73.989311,12"

    await persistence.save()

    assert mock_file.read.call_count == 1
    assert mock_file.write.call_count == 1
    assert mock_file.write.call_args == call(persistence_data)


@pytest.mark.parametrize(
    ("error", "write_side_effect"),
    [
        (PersistenceWriteError, OSError("Boom")),
    ],
)
async def test_persistence_save_error(
    mock_file: MagicMock, error: type[Exception], write_side_effect: Exception
) -> None:
    """Test persistence save error."""
    mock_file.write.side_effect = write_side_effect
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    with pytest.raises(error):
        await persistence.save()

    assert mock_file.write.call_count == 1


async def test_persistence_start_stop(
    mock_file: MagicMock, persistence_data: str
) -> None:
    """Test persistence start and stop."""
    mock_file.read.return_value = persistence_data
    nodes: dict[int, Node] = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.start()
    await asyncio.sleep(0.1)

    assert mock_file.read.call_count == 0
    assert mock_file.write.call_count == 1

    await persistence.stop()

    assert mock_file.read.call_count == 0
    assert mock_file.write.call_count == 2
