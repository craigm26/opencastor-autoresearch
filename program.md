# OpenCastor AutoResearcher

This agent autonomously improves the OpenCastor codebase overnight.

## Context

OpenCastor is a universal robot runtime (~Python 3.10+, 106 harness tests, ruff 100-char line limit).
Repo path: set in env var OPENCASTOR_REPO_PATH.
Conventions: PEP8, snake_case, type hints on public signatures, Google-style docstrings.
Test runner: `python -m pytest tests/ -x -q`
Linter: `ruff check castor/`

## KEY RULE: ONE TARGET PER EXPERIMENT

Every experiment targets EXACTLY ONE function, class, or file.
Never rewrite a whole module. Never add more than one test function per experiment.
Small, focused changes = higher approval rate.

## Active Track

Determined at runtime by TODAY_TRACK env var:

- **A** = Tests: write ONE new pytest test for ONE specific untested function in castor/
- **B** = Docs: add a Google-style docstring to ONE function/class missing it
- **C** = Presets: generate ONE new RCAN config preset YAML for a specific hardware combo
- **D** = Skills: improve ONE SKILL.md body with better step-by-step instructions
- **E** = Harness tests: write ONE pytest test for harness/P66 code (must include P66 assertion)
- **F** = Trajectory mining: read-only, extract patterns from trajectory DB

## Metrics (direction = improvement)

- A: test count ↑ (more tests = better)
- B: missing docstring count ↓ (fewer missing = better)
- C: preset count ↑ (more presets = better)
- D: skill eval checks count ↑
- E: harness test count ↑
- F: no metric (read-only, always exits after one pass)

## Output Format Rules

Track A & E — return ONLY a single Python test function:
```python
def test_<name>(...):
    ...
```

Track B — return ONLY the function/class definition with docstring added:
```python
def function_name(...):
    """One-line summary.

    Args:
        param: description

    Returns:
        description
    """
    ...existing code...
```

Track C — return ONLY valid YAML:
```yaml
rcan_version: "1.6"
metadata:
  robot_name: ...
...
```

Track D — return the COMPLETE SKILL.md including frontmatter (between --- markers).

## Forbidden Files

NEVER modify: castor/api.py, castor/safety.py, castor/auth.py, .env, results.tsv

## Quality Standards

Track A/E tests must:
- Import from real castor modules
- Test real behavior (not trivial `assert True`)
- Use pytest.mark.asyncio for async functions
- Mock external deps (ollama, google.auth, filesystem) with unittest.mock

Track B docstrings must:
- Follow Google style exactly
- Be accurate to what the function actually does
- Not hallucinate parameters that don't exist

Track E tests must additionally:
- Assert P66 invariant: ESTOP bypasses all harness steps
- Assert physical tools blocked in chat scope
- Assert consent required before physical tool execution
