"""Provide persistence."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .model.node import Node, NodeSchema


@dataclass
class Persistence:
    """Represent the persistence feature."""

    nodes: Dict[int, Node]
    path: str

    def _load(self, path: str = None) -> None:
        """Load stored data."""
        path = path or self.path
        data: dict = json.loads(Path(path).read_text())
        node_schema = NodeSchema()
        for node_data in data.values():
            node: Node = node_schema.load(node_data)
            self.nodes[node.node_id] = node

    def _save(self) -> None:
        """Save data."""
        data = {}
        node_schema = NodeSchema()
        for node in self.nodes.values():
            data[node.node_id] = node_schema.dump(node)

        Path(self.path).write_text(json.dumps(data, sort_keys=True, indent=2))

    async def start(self) -> None:
        """Start the scheduled saving of data."""

    async def stop(self) -> None:
        """Stop the scheduled saving of data."""
