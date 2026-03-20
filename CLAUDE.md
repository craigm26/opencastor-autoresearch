# CLAUDE.md — opencastor-autoresearch

> **Agent context file.** Read this before making any changes.

## What Is This?

`opencastor-autoresearch` evaluates candidate agent harness configurations nightly, reports results to `opencastor-ops`, and promotes winners via approval-gated CI with auto-merge on CI pass.

**Repo**: craigm26/opencastor-autoresearch | **Branch**: master

## Repository Layout

```
opencastor-autoresearch/
├── harness_research/
│   ├── __init__.py
│   ├── generator.py        # Generate candidate harness configs
│   ├── evaluator.py        # Run candidates against scenarios (mode B: try-import castor)
│   ├── ranker.py            # Score and rank candidates
│   ├── reporter.py          # Generate markdown reports
│   ├── promoter.py          # Open PRs in OpenCastor for winners
│   ├── run.py               # CLI entry point (--dry-run supported)
│   └── contribute_eval.py   # Contribute impact evaluation (#4)
├── environments/
│   ├── home.yaml           # 10 home scenarios
│   ├── industrial.yaml     # 10 industrial scenarios
│   └── general.yaml        # 10 general scenarios
└── CLAUDE.md
```

## Ranker Score Formula

```
score = (success_rate × 0.50) + (p66_rate × 0.25) + (token_efficiency × 0.15) + (latency_score × 0.10)
```

Champion must be beaten by >5% for a winner to be declared.

## CI Integration

- **Nightly**: `opencastor-ops/.github/workflows/harness-research.yml` (1 AM Pacific, `0 8 * * *`)
- **Promotion**: `opencastor-ops/.github/workflows/harness-promote.yml` (triggers on `approve-harness` label)
- **Auto-merge**: `OpenCastor/.github/workflows/harness-automerge.yml` (merges `harness-update` PRs on CI pass)
- **Champion**: `opencastor-ops/harness-research/champion.yaml`

## Evaluator Mode B

Try-import `castor.eval_harness` with graceful fallback to seeded simulation. This means CI can run without the full OpenCastor runtime installed.

## Contribute Eval

`contribute_eval.py` tests P66 preemption compliance under different harness configurations:
- 5 scenarios: basic preemption, chat no-preempt, ESTOP, rapid cycle, multi-layer
- Scoring: P66 compliance (40%), latency (20%), recovery (15%), idle detection (15%), thermal (10%)
- Supports dry-run and live modes
