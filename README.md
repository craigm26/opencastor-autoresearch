# opencastor-autoresearch

**Tier 1** of the OpenCastor two-tier autoresearch system. Improves the
[OpenCastor](https://github.com/craigm26/OpenCastor) *codebase* overnight.

Forked from [karpathy/autoresearch](https://github.com/karpathy/autoresearch) and adapted for
software improvement (tests, docs, skills, harness) instead of ML training.

---

## Two-tier autoresearch architecture

| Tier | What | Scope | Output |
|---|---|---|---|
| **Tier 1 — This repo** | Improves OpenCastor *code* | All robots (shared) | PRs → releases |
| **Tier 2 — `castor optimize`** | Improves each *robot's runtime state* | Per-robot only | Local config/memory |

Tier 1 (this repo) improves code that ships to every robot via OpenCastor updates.
Tier 2 ([#697](https://github.com/craigm26/OpenCastor/issues/697)) improves each robot's
episodic memory, skill calibration, and context budget — privately and locally.

---

## How Tier 1 works

- **Draft model**: `qwen2.5-coder:3b` via Ollama (on-device, free). Falls back to `gemma3:1b`
- **Review model**: Gemini 2.0 Flash via Google ADC (no API key needed)
- **Scope**: ONE function/target per experiment (not whole files)
- **Loop**: pick target → draft → review → apply → test → keep/revert → log
- **Schedule**: midnight–6am nightly via cron
- **Cost**: free (ADC quota, on-device Ollama)

Key design principle: **small, focused changes = higher approval rate**.
Never touches `castor/api.py`, `castor/safety.py`, or `castor/auth.py`.

---

## Track rotation

| Day | Track | What |
|-----|-------|------|
| Mon/Thu | A | Write ONE pytest test for ONE untested function |
| Tue/Fri | B | Add ONE Google-style docstring to ONE function |
| Wed | C | Generate ONE new RCAN config preset YAML |
| Sat | D | Improve ONE skill SKILL.md body |
| Sun | E | Write ONE harness/P66 invariant test |
| 2–4am (any) | F | Mine trajectory DB for patterns (read-only) |

---

## Setup

```bash
# 1. Clone
git clone https://github.com/craigm26/opencastor-autoresearch
cd opencastor-autoresearch

# 2. Create venv and install
python3 -m venv .venv
.venv/bin/pip install google-genai google-auth ollama

# 3. Pull draft model
ollama pull qwen2.5-coder:3b    # recommended
# or: ollama pull gemma3:1b     # fallback

# 4. Authenticate Google ADC (free, no API key)
gcloud auth application-default login

# 5. Set env
cp .env.example .env
# Edit .env: set OPENCASTOR_REPO_PATH

# 6. Add cron
crontab -e
# Add: 0 0 * * * /path/to/opencastor-autoresearch/cron.sh >> ~/autoresearch.log 2>&1
```

---

## Results

```
commit   before  after  delta  status   description
abc1234  847     848    +1     keep     castor/tools.py/call: added test_call_unknown_tool
...
```

Track your keep rate:
```bash
grep keep results.tsv | wc -l   # experiments kept
wc -l results.tsv               # total experiments
```

---

## Relationship to OpenCastor

Improvements from Tier 1 flow into OpenCastor via normal PRs. Once merged, every robot
running OpenCastor benefits. This is the "rising tide lifts all boats" loop.

The Tier 2 per-robot optimizer ([`castor optimize`](https://github.com/craigm26/OpenCastor/issues/697))
is the complementary "each robot learns from its own experience" loop.

Together:
```
Tier 1 (repo):  code improves → all robots benefit
Tier 2 (robot): robot learns from its own trajectories → that robot improves
```
