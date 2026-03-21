"""Tests for harness_research/dashboard.py."""

import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Ensure the repo root is importable
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data))


# ---------------------------------------------------------------------------
# test_load_champion
# ---------------------------------------------------------------------------

def test_load_champion(tmp_path, monkeypatch):
    """_load_yaml reads champion.yaml correctly."""
    # Set up a fake ops repo
    harness_dir = tmp_path / "harness-research"
    champion_path = harness_dir / "champion.yaml"
    champion_data = {
        "candidate_id": "test_champ",
        "score": 0.9500,
        "date": "2026-03-21",
        "config": {"cost_gate_usd": 0.01, "thinking_budget": 1024},
    }
    _write_yaml(champion_path, champion_data)

    monkeypatch.setenv("OPENCASTOR_OPS_DIR", str(tmp_path))

    # Re-import module with patched env so OPS_REPO is resolved
    import importlib
    import harness_research.dashboard as dash
    importlib.reload(dash)

    result = dash._load_yaml(champion_path)
    assert result["candidate_id"] == "test_champ"
    assert result["score"] == pytest.approx(0.9500)
    assert result["config"]["cost_gate_usd"] == 0.01


# ---------------------------------------------------------------------------
# test_recent_winners
# ---------------------------------------------------------------------------

def test_recent_winners(tmp_path, monkeypatch):
    """_recent_winners returns files sorted newest-first."""
    candidates_dir = tmp_path / "harness-research" / "candidates"
    candidates_dir.mkdir(parents=True)

    dates = ["2026-03-18", "2026-03-20", "2026-03-19"]
    for d in dates:
        _write_yaml(
            candidates_dir / f"{d}-winner.yaml",
            {"score": float(d.replace("-", ".")[5:])},  # deterministic score
        )

    monkeypatch.setenv("OPENCASTOR_OPS_DIR", str(tmp_path))

    import importlib
    import harness_research.dashboard as dash
    importlib.reload(dash)

    winners = dash._recent_winners(5)
    # Should be sorted newest-first by filename
    names = [w[0] for w in winners]
    assert names == sorted(names, reverse=True)
    assert len(winners) == 3


# ---------------------------------------------------------------------------
# test_dashboard_no_ops_dir
# ---------------------------------------------------------------------------

def test_dashboard_no_ops_dir(monkeypatch):
    """main() does not raise when OPS_REPO does not exist."""
    monkeypatch.setenv("OPENCASTOR_OPS_DIR", "/nonexistent/path/that/does/not/exist")

    import importlib
    import harness_research.dashboard as dash
    importlib.reload(dash)

    # Should not raise
    rc = dash.main()
    assert rc == 0
