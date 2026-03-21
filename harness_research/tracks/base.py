from __future__ import annotations

"""Base class for auto-research tracks (#9)."""

import abc
from typing import Any


class TrackBase(abc.ABC):
    @property
    @abc.abstractmethod
    def track_id(self) -> str: ...

    @abc.abstractmethod
    def generate_candidates(self, n: int) -> list[dict[str, Any]]: ...
