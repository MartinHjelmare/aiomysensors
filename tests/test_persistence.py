"""Test persistence."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import aiofiles
import pytest

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
    return fixture_json.read_text()


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
