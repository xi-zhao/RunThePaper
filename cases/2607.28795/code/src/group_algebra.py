"""Finite-group regular representations used by the mitten-code constructor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np


@dataclass(frozen=True)
class FiniteGroupTable:
    """A finite group in the exact zero-based ordering returned by GAP."""

    small_group_id: tuple[int, int]
    multiplication: np.ndarray
    inverses: np.ndarray
    identity: int

    @property
    def order(self) -> int:
        return int(self.multiplication.shape[0])

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "FiniteGroupTable":
        group_id = tuple(int(value) for value in record["small_group_id"])
        multiplication = np.asarray(record["multiplication"], dtype=np.int64)
        inverses = np.asarray(record["inverse"], dtype=np.int64)
        order = int(record["order"])
        identity = int(record["identity"])
        if len(group_id) != 2 or group_id[0] != order:
            raise ValueError(f"invalid SmallGroup identifier: {group_id}")
        if multiplication.shape != (order, order) or inverses.shape != (order,):
            raise ValueError(f"invalid group table shape for {group_id}")
        if np.any(multiplication < 0) or np.any(multiplication >= order):
            raise ValueError(f"group products outside range for {group_id}")
        if np.any(inverses < 0) or np.any(inverses >= order):
            raise ValueError(f"group inverses outside range for {group_id}")
        labels = np.arange(order)
        if not np.array_equal(multiplication[identity], labels):
            raise ValueError(f"invalid left identity for {group_id}")
        if not np.array_equal(multiplication[:, identity], labels):
            raise ValueError(f"invalid right identity for {group_id}")
        if not np.all(multiplication[labels, inverses] == identity):
            raise ValueError(f"invalid inverse table for {group_id}")
        return cls(group_id, multiplication, inverses, identity)

    def validate_support(self, support: Iterable[int]) -> tuple[int, ...]:
        values = tuple(int(value) for value in support)
        if len(set(values)) != len(values):
            raise ValueError(f"duplicate elements in support {values}")
        if any(value < 0 or value >= self.order for value in values):
            raise ValueError(f"support outside group range: {values}")
        return values

    def star_support(self, support: Iterable[int]) -> tuple[int, ...]:
        values = self.validate_support(support)
        return tuple(int(self.inverses[value]) for value in values)

    def left_regular(self, support: Iterable[int]) -> np.ndarray:
        """XOR of L(g)|h> = |gh> for all g in the support."""

        values = self.validate_support(support)
        result = np.zeros((self.order, self.order), dtype=np.uint8)
        columns = np.arange(self.order)
        for element in values:
            result[self.multiplication[element, columns], columns] ^= 1
        return result
    def right_regular(self, support: Iterable[int]) -> np.ndarray:
        """XOR of R(g)|h> = |h g^{-1}> for all g in the support."""

        values = self.validate_support(support)
        result = np.zeros((self.order, self.order), dtype=np.uint8)
        columns = np.arange(self.order)
        for element in values:
            inverse = int(self.inverses[element])
            result[self.multiplication[columns, inverse], columns] ^= 1
        return result
