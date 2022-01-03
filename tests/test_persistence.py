"""Test persistence."""
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import aiofiles
import pytest

from aiomysensors.exceptions import PersistenceReadError, PersistenceWriteError
from aiomysensors.persistence import Persistence

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(name="mock_file")
def mock_file_fixture():
    """Patch aiofiles."""
    mock_file = MagicMock()
    # pylint: disable=unnecessary-lambda
    aiofiles.threadpool.wrap.register(MagicMock)(
        lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(*args, **kwargs)
    )

    with patch("aiofiles.threadpool.sync_open", return_value=mock_file):
        yield mock_file


@pytest.fixture(name="persistence_data", scope="session")
def persistence_data_fixture(request):
    """Return a JSON string with persistence data saved in aiomysensors."""
    fixture = "test_aiomysensors_persistence.json"
    if hasattr(request, "param") and request.param:
        fixture = request.param
    fixture_json = FIXTURES_DIR / fixture
    return fixture_json.read_text().strip()


@pytest.mark.parametrize(
    "persistence_data",
    ["test_aiomysensors_persistence.json", "test_pymysensors_persistence.json"],
    indirect=True,
)
async def test_persistence_load(mock_file, persistence_data):
    """Test persistence load."""
    mock_file.read.return_value = persistence_data
    nodes = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert mock_file.read.call_count == 1
    assert nodes
    node = nodes.get(1)
    assert node.battery_level == 0
    assert node.children
    child = node.children.get(1)
    assert child.child_id == 1
    assert child.child_type == 38
    assert child.values
    value = child.values.get(49)
    assert value == "40.741894,-73.989311,12"


@pytest.mark.parametrize(
    "error, read_return_value, read_side_effect",
    [
        (PersistenceReadError, None, OSError("Boom")),
        (PersistenceReadError, "bad content", None),
    ],
)
async def test_persistence_load_error(
    mock_file, error, read_return_value, read_side_effect
):
    """Test persistence load error."""
    mock_file.read.return_value = read_return_value
    mock_file.read.side_effect = read_side_effect
    nodes = {}
    persistence = Persistence(nodes, "test_path")

    with pytest.raises(error):
        await persistence.load()

    assert mock_file.read.call_count == 1


async def test_persistence_save(mock_file, persistence_data):
    """Test persistence save."""
    mock_file.read.return_value = persistence_data
    nodes = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.load()

    assert mock_file.read.call_count == 1
    assert mock_file.write.call_count == 0
    assert nodes
    node = nodes.get(1)
    assert node.battery_level == 0
    assert node.children
    child = node.children.get(1)
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
    "error, write_side_effect",
    [
        (PersistenceWriteError, OSError("Boom")),
    ],
)
async def test_persistence_save_error(mock_file, error, write_side_effect):
    """Test persistence save error."""
    mock_file.write.side_effect = write_side_effect
    nodes = {}
    persistence = Persistence(nodes, "test_path")

    with pytest.raises(error):
        await persistence.save()

    assert mock_file.write.call_count == 1


async def test_persistence_start_stop(mock_file, persistence_data):
    """Test persistence start and stop."""
    mock_file.read.return_value = persistence_data
    nodes = {}
    persistence = Persistence(nodes, "test_path")

    await persistence.start()
    await asyncio.sleep(0.1)

    assert mock_file.read.call_count == 0
    assert mock_file.write.call_count == 1

    await persistence.stop()

    assert mock_file.read.call_count == 0
    assert mock_file.write.call_count == 2
