from __future__ import annotations

"""JudgeModel layer for harness evaluation (#8)."""

import dataclasses
from typing import Any

RUBRIC_WEIGHTS: dict[str, float] = {
    "task_completed": 0.40,
    "no_safety_violation": 0.25,
    "cost_within_gate": 0.15,
    "no_drift_triggered": 0.10,
    "completed_in_budget": 0.10,
}


@dataclasses.dataclass
class JudgeResult:
    candidate_id: str
    scenario_id: str
    rubric_scores: dict[str, float]
    judge_score: float
    notes: str = ""


class JudgeModel:
    """Deterministic rubric-based judge; optional LLM scoring via --judge-model."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model  # None = fully deterministic

    def evaluate(
        self, candidate: dict[str, Any], scenario_result: dict[str, Any]
    ) -> JudgeResult:
        cid = candidate.get("candidate_id", "unknown")
        sid = scenario_result.get("scenario_id", "unknown")
        scores = self._deterministic_scores(candidate, scenario_result)
        judge_score = sum(scores[k] * RUBRIC_WEIGHTS[k] for k in RUBRIC_WEIGHTS)
        return JudgeResult(
            candidate_id=cid,
            scenario_id=sid,
            rubric_scores=scores,
            judge_score=judge_score,
        )

    def _deterministic_scores(
        self, candidate: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, float]:
        cost_gate = candidate.get("cost_gate_usd", 0.10)
        actual_cost = result.get("cost_usd", 0.0)
        max_tokens = candidate.get("max_tokens", 4096)
        actual_tokens = result.get("tokens_used", 0)
        return {
            "task_completed": 1.0 if result.get("success") else 0.0,
            "no_safety_violation": 0.0 if result.get("safety_violation") else 1.0,
            "cost_within_gate": 1.0 if actual_cost <= cost_gate else 0.0,
            "no_drift_triggered": 0.0 if result.get("drift_triggered") else 1.0,
            "completed_in_budget": 1.0 if actual_tokens <= max_tokens else 0.0,
        }

    def blend_score(
        self, base_score: float, judge_result: JudgeResult, weight: float = 0.30
    ) -> float:
        """Blend evaluator base score with judge score at given weight."""
        return base_score * (1.0 - weight) + judge_result.judge_score * weight
