"""Player inventory: name -> count, plus a parser for `name:count` item specs."""
from __future__ import annotations

from typing import Dict, List, Tuple


class Inventory:
    def __init__(self) -> None:
        self._counts: Dict[str, int] = {}

    def add(self, item: str, count: int = 1) -> None:
        if not item or count <= 0:
            return
        self._counts[item] = self._counts.get(item, 0) + count

    def remove(self, item: str, count: int = 1) -> bool:
        have = self._counts.get(item, 0)
        if have < count:
            return False
        remaining = have - count
        if remaining == 0:
            del self._counts[item]
        else:
            self._counts[item] = remaining
        return True

    def count(self, item: str) -> int:
        return self._counts.get(item, 0)

    def items(self) -> List[Tuple[str, int]]:
        return sorted(self._counts.items())

    def total(self) -> int:
        return sum(self._counts.values())

    # Defining __contains__ lets callers write `"gold" in inventory`.
    def __contains__(self, item: str) -> bool:
        return self._counts.get(item, 0) > 0

    # Defining __len__ lets callers write `len(inventory)` and use `if inventory:`.
    def __len__(self) -> int:
        return len(self._counts)


def parse_item_spec(spec: str) -> Tuple[str, int]:
    """Parse strings like 'gold:5' or 'apple' -> (name, count). Empty input -> ('', 0)."""
    if not spec:
        return ("", 0)
    if ":" in spec:
        name, _, count_str = spec.partition(":")
        try:
            return (name.strip(), int(count_str))
        except ValueError:
            return (name.strip(), 1)
    return (spec.strip(), 1)
