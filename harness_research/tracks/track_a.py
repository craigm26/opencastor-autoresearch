from __future__ import annotations

"""Track A: vary cost_gate_usd, max_tokens, timeout_s (#9)."""

import hashlib
import itertools
from typing import Any

from harness_research.tracks.base import TrackBase


class HarnessParamTrack(TrackBase):
    track_id = "A"

    COST_GATES = [0.005, 0.01, 0.02, 0.05]
    MAX_TOKENS = [1024, 2048, 4096, 8192]
    TIMEOUTS = [30, 60, 120, 300]

    def generate_candidates(self, n: int) -> list[dict[str, Any]]:
        combos = list(itertools.product(self.COST_GATES, self.MAX_TOKENS, self.TIMEOUTS))
        results: list[dict[str, Any]] = []
        for cost, tokens, timeout in combos[:n]:
            h = hashlib.md5(f"{cost}-{tokens}-{timeout}".encode()).hexdigest()[:6]
            results.append(
                {
                    "candidate_id": f"track_a_{h}",
                    "track": "A",
                    "cost_gate_usd": cost,
                    "max_tokens": tokens,
                    "timeout_s": timeout,
                }
            )
        return results
