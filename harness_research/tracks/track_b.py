from __future__ import annotations

"""Track B: vary orchestration pattern (#9)."""

from typing import Any

from harness_research.tracks.base import TrackBase


class ArchitectureTrack(TrackBase):
    track_id = "B"

    PATTERNS = ["single_agent_supervisor", "initializer_executor", "multi_agent"]

    def generate_candidates(self, n: int) -> list[dict[str, Any]]:
        return [
            {"candidate_id": f"track_b_{p}", "track": "B", "pattern": {"name": p}}
            for p in self.PATTERNS[:n]
        ]
