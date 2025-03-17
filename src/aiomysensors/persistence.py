"""Provide persistence."""

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
import json
import logging
from typing import Any

import aiofiles

from .exceptions import PersistenceReadError, PersistenceWriteError
from .model.node import Node

LOGGER = logging.getLogger(__package__)
SAVE_INTERVAL = 900


@dataclass
class Persistence:
    """Represent the persistence feature."""

    nodes: dict[int, Node]
    path: str
    _cancel_save: Callable[[], Coroutine[Any, Any, None]] | None = field(
        default=None,
        init=False,
    )

    async def load(self, path: str | None = None) -> None:
        """Load the stored data."""
        path = path or self.path

        try:
            async with aiofiles.open(path) as fil:
                read = await fil.read()
            data: dict = json.loads(read or "{}")
        except FileNotFoundError:
            LOGGER.debug("Persistence file missing, creating file: %s", path)
            await self.save()
            return
        except (OSError, ValueError) as err:
            raise PersistenceReadError(err) from err

        for node_data in data.values():
            node = Node.from_dict(node_data)
            self.nodes[node.node_id] = node

    async def save(self) -> None:
        """Save data."""
        data = {}
        for node in self.nodes.values():
            data[node.node_id] = node.to_dict()

        try:
            async with aiofiles.open(self.path, mode="w") as fil:
                await fil.write(json.dumps(data, sort_keys=True, indent=2))
        except OSError as err:
            raise PersistenceWriteError(err) from err

    async def start(self) -> None:
        """Start the scheduled saving of data."""

        async def save_on_schedule() -> None:
            """Save data and sleep until next save."""
            while True:
                await self.save()
                try:
                    await asyncio.sleep(SAVE_INTERVAL)
                except asyncio.CancelledError:
                    break

        task = asyncio.create_task(save_on_schedule())

        async def cancel_save() -> None:
            """Cancel the save task."""
            task.cancel()
            await task

        self._cancel_save = cancel_save

    async def stop(self) -> None:
        """Stop the scheduled saving of data and save a final time."""
        if self._cancel_save:
            await self._cancel_save()
            self._cancel_save = None

        await self.save()
