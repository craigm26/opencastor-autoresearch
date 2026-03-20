"""Aggregate harness evaluation results submitted by castor contribute fleet.

Each robot running `castor contribute` with harness_eval work units submits
an EvalResult document to Firestore under:
  contribute_results/{robot_id}/harness_eval/{session_id}

This module reads those results, groups by hardware_tier, runs the ranker
per group, and triggers reporter.write_report() for each tier that has
enough data to be meaningful.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Minimum number of eval submissions per tier before we consider it meaningful
MIN_SUBMISSIONS_PER_TIER = 3

# Only use submissions from the last N days
LOOKBACK_DAYS = 7

# Known hardware tiers (from generator.py)
from .generator import HARDWARE_TIERS


@dataclass
class FleetEvalSubmission:
    """A single harness eval result submitted by a fleet robot."""
    robot_id: str
    hardware_tier: str
    candidate_id: str
    config: dict
    description: str
    success_rate: float
    p66_rate: float
    token_efficiency: float
    latency_score: float
    submitted_at: datetime
    env_results: list[dict] = field(default_factory=list)


def _load_firestore_client():
    """Create Firestore client using service account or ADC."""
    from google.cloud import firestore as _firestore

    creds_path = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(Path.home() / ".config/opencastor/firebase-sa-key.json"),
    )
    try:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=[
                "https://www.googleapis.com/auth/datastore",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )
        return _firestore.Client(project="opencastor", credentials=creds)
    except Exception:
        import google.auth
        creds, project = google.auth.default()
        return _firestore.Client(project=project or "opencastor", credentials=creds)


def _parse_submission(doc_data: dict[str, Any], robot_id: str) -> FleetEvalSubmission | None:
    """Parse a Firestore document into a FleetEvalSubmission."""
    try:
        submitted_at = doc_data.get("submitted_at")
        if hasattr(submitted_at, "timestamp"):
            submitted_at = datetime.fromtimestamp(submitted_at.timestamp(), tz=timezone.utc)
        elif isinstance(submitted_at, str):
            submitted_at = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
        else:
            submitted_at = datetime.now(tz=timezone.utc)

        return FleetEvalSubmission(
            robot_id=robot_id,
            hardware_tier=doc_data.get("hardware_tier", "unknown"),
            candidate_id=doc_data.get("candidate_id", "unknown"),
            config=doc_data.get("config", {}),
            description=doc_data.get("description", ""),
            success_rate=float(doc_data.get("success_rate", 0.0)),
            p66_rate=float(doc_data.get("p66_rate", 1.0)),
            token_efficiency=float(doc_data.get("token_efficiency", 0.5)),
            latency_score=float(doc_data.get("latency_score", 0.5)),
            submitted_at=submitted_at,
            env_results=doc_data.get("env_results", []),
        )
    except Exception as e:
        log.warning("Failed to parse submission from robot %s: %s", robot_id, e)
        return None


def fetch_fleet_submissions(
    hardware_tier: str | None = None,
    lookback_days: int = LOOKBACK_DAYS,
    dry_run: bool = False,
) -> dict[str, list[FleetEvalSubmission]]:
    """Fetch harness eval submissions from Firestore, grouped by hardware_tier.

    Args:
        hardware_tier: If set, only fetch submissions for this tier.
        lookback_days: Only include submissions from the last N days.
        dry_run: Return synthetic data instead of querying Firestore.

    Returns:
        Dict mapping hardware_tier → list of FleetEvalSubmission.
    """
    if dry_run:
        return _generate_synthetic_submissions(hardware_tier)

    try:
        db = _load_firestore_client()
    except Exception as e:
        log.warning("Firestore unavailable: %s — using synthetic submissions", e)
        return _generate_synthetic_submissions(hardware_tier)

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    results: dict[str, list[FleetEvalSubmission]] = {}

    try:
        robots_ref = db.collection("robots")
        if hardware_tier:
            robots_query = robots_ref.where("hardware_tier", "==", hardware_tier)
        else:
            robots_query = robots_ref

        robots = list(robots_query.stream())
        log.info("Found %d robot(s) to check for fleet submissions", len(robots))

        for robot_doc in robots:
            robot_id = robot_doc.id
            evals_ref = db.collection("contribute_results").document(robot_id).collection("harness_eval")
            evals = list(evals_ref.stream())

            for eval_doc in evals:
                data = eval_doc.to_dict()
                if not data:
                    continue
                sub = _parse_submission(data, robot_id)
                if sub is None:
                    continue
                if sub.submitted_at < cutoff:
                    continue
                tier = sub.hardware_tier
                if tier not in results:
                    results[tier] = []
                results[tier].append(sub)
                log.debug("  Loaded submission from %s (tier=%s, score=%.2f)", robot_id, tier, sub.success_rate)

    except Exception as e:
        log.warning("Error reading fleet submissions from Firestore: %s", e)
        return _generate_synthetic_submissions(hardware_tier)

    for tier, subs in results.items():
        log.info("Tier %s: %d fleet submission(s)", tier, len(subs))

    return results


def _generate_synthetic_submissions(
    hardware_tier: str | None = None,
) -> dict[str, list[FleetEvalSubmission]]:
    """Generate synthetic fleet submissions for dry-run / CI testing."""
    import random
    from datetime import timezone

    tiers = [hardware_tier] if hardware_tier else HARDWARE_TIERS
    results: dict[str, list[FleetEvalSubmission]] = {}

    for tier in tiers:
        subs = []
        for i in range(random.randint(3, 6)):
            robot_id = f"synthetic-robot-{tier}-{i}"
            config = {
                "enabled": True,
                "max_iterations": random.choice([4, 5, 6, 8]),
                "thinking_budget": random.choice([512, 768, 1024, 2048]),
                "context_budget": random.choice([4096, 8192, 12288]),
                "p66_consent_threshold": random.choice(["physical", "verbal"]),
                "retry_on_error": random.choice([True, False]),
                "drift_detection": random.choice([True, False]),
                "cost_gate_usd": random.choice([0.005, 0.01, 0.015, 0.02, 0.05]),
            }
            candidate_id = f"fleet_{tier}_v{i}"
            subs.append(FleetEvalSubmission(
                robot_id=robot_id,
                hardware_tier=tier,
                candidate_id=candidate_id,
                config=config,
                description=f"Fleet eval from {robot_id}",
                success_rate=random.uniform(0.7, 0.99),
                p66_rate=random.uniform(0.85, 1.0),
                token_efficiency=random.uniform(0.2, 0.8),
                latency_score=random.uniform(0.0, 0.5),
                submitted_at=datetime.now(tz=timezone.utc),
            ))
        results[tier] = subs
        log.info("[synthetic] Tier %s: %d fleet submission(s)", tier, len(subs))

    return results


def submissions_to_eval_results(submissions: list[FleetEvalSubmission]):
    """Convert fleet submissions into EvalResults for the ranker.

    Multiple submissions with the same candidate_id are averaged together.
    Builds synthetic ScenarioResult objects that reproduce the fleet-averaged metrics.
    """
    from .evaluator import EvalResults, ScenarioResult

    # Group by candidate_id
    grouped: dict[str, list[FleetEvalSubmission]] = {}
    for sub in submissions:
        if sub.candidate_id not in grouped:
            grouped[sub.candidate_id] = []
        grouped[sub.candidate_id].append(sub)

    eval_results_list = []
    for candidate_id, subs in grouped.items():
        # Average metrics across submissions
        avg_success = sum(s.success_rate for s in subs) / len(subs)
        avg_p66 = sum(s.p66_rate for s in subs) / len(subs)
        avg_efficiency = sum(s.token_efficiency for s in subs) / len(subs)
        avg_latency = sum(s.latency_score for s in subs) / len(subs)

        # Use config and description from the first submission
        config = subs[0].config
        description = subs[0].description or f"Fleet eval: {candidate_id}"

        # Build 10 synthetic ScenarioResults that reproduce the averaged metrics.
        # success_rate and p66_rate → N out of 10 scenarios pass.
        # token_efficiency → avg_tokens = (1 - avg_efficiency) * 8000
        # latency_score    → avg_latency_ms = (1 - avg_latency) * 5000
        n_success = max(0, min(10, round(avg_success * 10)))
        n_p66 = max(0, min(10, round(avg_p66 * 10)))
        avg_tokens = int((1.0 - avg_efficiency) * 8000)
        avg_latency_ms = (1.0 - avg_latency) * 5000

        scenario_results = []
        for i in range(10):
            scenario_results.append(ScenarioResult(
                scenario_id=f"fleet_{candidate_id}_{i}",
                environment="general",
                success=(i < n_success),
                p66_compliant=(i < n_p66),
                tokens_used=avg_tokens,
                latency_ms=avg_latency_ms,
            ))

        eval_results_list.append(EvalResults(
            candidate_id=candidate_id,
            config=config,
            description=description,
            scenario_results=scenario_results,
        ))
        log.debug(
            "Aggregated %d submission(s) for %s: success=%.2f p66=%.2f",
            len(subs), candidate_id, avg_success, avg_p66,
        )

    return eval_results_list


def run_fleet_research(
    hardware_tier: str | None = None,
    dry_run: bool = False,
    lookback_days: int = LOOKBACK_DAYS,
) -> dict[str, bool]:
    """Run fleet-contributed harness research for one or all hardware tiers.

    Fetches Firestore submissions, aggregates by tier, ranks, and writes reports.

    Returns dict of hardware_tier → had_winner.
    """
    from .ranker import find_winner
    from .reporter import write_report

    all_submissions = fetch_fleet_submissions(
        hardware_tier=hardware_tier,
        lookback_days=lookback_days,
        dry_run=dry_run,
    )

    if not all_submissions:
        log.info("No fleet submissions found")
        return {}

    results = {}
    for tier, subs in all_submissions.items():
        log.info("=== Fleet research for tier: %s (%d submissions) ===", tier, len(subs))

        if len(subs) < MIN_SUBMISSIONS_PER_TIER:
            log.info(
                "Skipping tier %s — only %d submission(s), need %d",
                tier, len(subs), MIN_SUBMISSIONS_PER_TIER,
            )
            results[tier] = False
            continue

        # Convert to EvalResults and rank
        eval_results_list = submissions_to_eval_results(subs)
        if not eval_results_list:
            log.warning("No valid eval results for tier %s", tier)
            results[tier] = False
            continue

        ranked, winner, champion_score, best_score = find_winner(
            eval_results_list,
            hardware_tier=tier,
        )

        for i, (r, score) in enumerate(ranked, 1):
            log.info("  #%d %s: %.4f — %s", i, r.candidate_id, score, r.description)

        had_winner = write_report(
            ranked, winner, champion_score,
            dry_run=dry_run,
            hardware_tier=tier,
        )
        results[tier] = had_winner

        if had_winner:
            log.info(
                "Fleet winner for %s: %s (%.4f > %.4f)",
                tier, winner.candidate_id, best_score, champion_score,
            )
        else:
            log.info("No improvement for %s (best=%.4f, champion=%.4f)", tier, best_score, champion_score)

    return results
