"""Provide a MySensors node and child abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field

from mashumaro import DataClassDictMixin, field_options
from mashumaro.config import BaseConfig

from aiomysensors.exceptions import MissingChildError


@dataclass(kw_only=True)
class Node(DataClassDictMixin):
    """Represent a MySensors node."""

    node_id: int = field(metadata=field_options(alias="sensor_id"))
    node_type: int = field(
        metadata=field_options(
            alias="type",
            deserialize=lambda x: 18 if x is None else x,
        )
    )
    protocol_version: str
    children: dict[int, Child] = field(default_factory=dict)
    sketch_name: str = field(
        default="",
        metadata=field_options(deserialize=lambda x: "" if x is None else x),
    )
    sketch_version: str = field(
        default="",
        metadata=field_options(deserialize=lambda x: "" if x is None else x),
    )
    battery_level: int | None = field(
        default=None,
        metadata=field_options(
            deserialize=lambda x: None if x is None else min(max(x, 0), 100)
        ),
    )
    sleeping: bool = False
    reboot: bool = field(
        default=False,
        init=False,
        metadata=field_options(serialize="omit"),
    )

    class Config(BaseConfig):
        """Config for mashumaro."""

        allow_deserialization_not_by_alias = True
        code_generation_options = ["TO_DICT_ADD_BY_ALIAS_FLAG"]  # noqa: RUF012

    def add_child(
        self,
        child_id: int,
        child_type: int,
        description: str = "",
        values: dict[int, str] | None = None,
    ) -> None:
        """Create and add a child."""
        self.children[child_id] = Child(
            child_id=child_id,
            child_type=child_type,
            description=description,
            values=values or {},
        )

    def remove_child(self, child_id: int) -> None:
        """Remove a child."""
        if child_id not in self.children:
            raise MissingChildError(child_id)
        self.children.pop(child_id)


@dataclass(kw_only=True)
class Child(DataClassDictMixin):
    """Represent a MySensors child."""

    child_id: int = field(metadata=field_options(alias="id"))
    child_type: int = field(metadata=field_options(alias="type"))
    description: str = ""
    values: dict[int, str] = field(default_factory=dict)

    class Config(BaseConfig):
        """Config for mashumaro."""

        allow_deserialization_not_by_alias = True
        code_generation_options = ["TO_DICT_ADD_BY_ALIAS_FLAG"]  # noqa: RUF012

    def set_value(self, value_type: int, value: str) -> None:
        """Set a child's value."""
        self.values[value_type] = value
