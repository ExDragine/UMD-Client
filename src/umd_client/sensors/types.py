from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Reading:
    timestamp: int
    data: dict[str, Any]

    @property
    def value_names(self) -> list[str]:
        return list(self.data.keys())

    @property
    def values(self) -> list[Any]:
        return list(self.data.values())

    @property
    def display_values(self) -> list[Any]:
        return [
            self.data["temperature"],
            self.data["humidity"],
            self.data["pressure"],
            self.data["lux"],
            self.data["uv"],
        ]
