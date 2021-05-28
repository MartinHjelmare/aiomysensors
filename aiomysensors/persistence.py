"""Provide persistence."""
import json
from dataclasses import dataclass
from typing import Dict

import aiofiles

from .model.node import Node, NodeSchema


@dataclass
class Persistence:
    """Represent the persistence feature."""

    nodes: Dict[int, Node]
    path: str

    async def load(self, path: str = None) -> None:
        """Load the stored data."""
        path = path or self.path

        async with aiofiles.open(path, mode="r") as fil:
            read = await fil.read()

        data: dict = json.loads(read)
        node_schema = NodeSchema()
        for node_data in data.values():
            node: Node = node_schema.load(node_data)
            self.nodes[node.node_id] = node

    async def save(self) -> None:
        """Save data."""
        data = {}
        node_schema = NodeSchema()
        for node in self.nodes.values():
            data[node.node_id] = node_schema.dump(node)

        async with aiofiles.open(self.path, mode="w") as fil:
            await fil.write(json.dumps(data, sort_keys=True, indent=2))

    async def start(self) -> None:
        """Start the scheduled saving of data."""

    async def stop(self) -> None:
        """Stop the scheduled saving of data."""
