from __future__ import annotations

"""Track C: vary skill_set combinations (#9)."""

from typing import Any

from harness_research.tracks.base import TrackBase


class SkillTrack(TrackBase):
    track_id = "C"

    SKILL_SETS = [
        ["search", "code"],
        ["search", "code", "memory"],
        ["search", "code", "memory", "browser"],
        ["code"],
    ]

    def generate_candidates(self, n: int) -> list[dict[str, Any]]:
        return [
            {
                "candidate_id": f"track_c_{'_'.join(skills)}",
                "track": "C",
                "skill_set": skills,
            }
            for skills in self.SKILL_SETS[:n]
        ]
