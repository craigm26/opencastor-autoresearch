from __future__ import annotations

from harness_research.judge import JudgeModel, RUBRIC_WEIGHTS
from harness_research.tracks import HarnessParamTrack, ArchitectureTrack, SkillTrack


def test_deterministic_scores_success():
    judge = JudgeModel()
    candidate = {"candidate_id": "c1", "cost_gate_usd": 0.10, "max_tokens": 4096}
    result = {"scenario_id": "s1", "success": True, "cost_usd": 0.01, "tokens_used": 1000}
    jr = judge.evaluate(candidate, result)
    assert jr.rubric_scores["task_completed"] == 1.0
    assert jr.rubric_scores["cost_within_gate"] == 1.0
    assert jr.judge_score > 0.8


def test_blend_score_math():
    judge = JudgeModel()
    candidate = {"candidate_id": "c2", "cost_gate_usd": 0.10, "max_tokens": 4096}
    result = {"scenario_id": "s2", "success": True, "cost_usd": 0.05, "tokens_used": 500}
    jr = judge.evaluate(candidate, result)
    blended = judge.blend_score(0.9, jr, weight=0.30)
    expected = 0.9 * 0.70 + jr.judge_score * 0.30
    assert abs(blended - expected) < 1e-9


def test_tracks_generate():
    for track_cls, track_id in [(HarnessParamTrack, "A"), (ArchitectureTrack, "B"), (SkillTrack, "C")]:
        t = track_cls()
        candidates = t.generate_candidates(2)
        assert len(candidates) == 2
        assert all(c["track"] == track_id for c in candidates)
        assert all("candidate_id" in c for c in candidates)


def test_judge_failed_scenario():
    judge = JudgeModel()
    candidate = {"candidate_id": "c3", "cost_gate_usd": 0.05, "max_tokens": 2048}
    result = {
        "scenario_id": "s3",
        "success": False,
        "safety_violation": True,
        "cost_usd": 0.10,
        "tokens_used": 5000,
    }
    jr = judge.evaluate(candidate, result)
    assert jr.rubric_scores["task_completed"] == 0.0
    assert jr.rubric_scores["no_safety_violation"] == 0.0
    assert jr.judge_score < 0.3
