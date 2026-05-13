from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "evals" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("replay_chain_eval", SCRIPTS / "replay_chain_eval.py")
assert SPEC is not None and SPEC.loader is not None
replay_chain_eval = importlib.util.module_from_spec(SPEC)
sys.modules["replay_chain_eval"] = replay_chain_eval
SPEC.loader.exec_module(replay_chain_eval)


def minimal_raw_context() -> dict:
    return {
        "positioning": "semantic replay fidelity under constrained context budgets",
        "constraints": ["cloud-first workflow", "preserve CI stability"],
        "truths": [
            {
                "id": "cloud_first_workflow_required",
                "category": "workflow_constraint",
                "must_retain_terms": ["cloud", "Render", "Vercel", "Docker", "CI"],
            },
            {
                "id": "architectural_continuity_matters",
                "category": "architectural_continuity",
                "must_retain_terms": ["architecture", "API", "KVTC", "showcase", "telemetry", "validation"],
            },
        ],
        "questions": [
            {"id": "q_cloud_first", "question": "", "expected_terms": ["cloud-first", "CI", "deployability"]},
            {"id": "q_architecture", "question": "", "expected_terms": ["API", "KVTC", "showcase", "telemetry", "validation"]},
        ],
    }


def test_negated_mutation_markers_are_not_contradictions() -> None:
    text = "This is not production certified and has no synthetic token spam."

    assert replay_chain_eval.detect_contradictions(text) == []


def test_replay_chain_metrics_decay_without_question_leakage() -> None:
    raw_context = minimal_raw_context()
    state = replay_chain_eval.initial_state(raw_context)
    replay = replay_chain_eval.replay_answers(state, raw_context["questions"])
    first = replay_chain_eval.evaluate_step(raw_context, state, replay, 1.0, 0)

    for iteration in range(2, 8):
        state = replay_chain_eval.recompress(state, replay, raw_context, iteration)
        replay = replay_chain_eval.replay_answers(state, raw_context["questions"])
    later = replay_chain_eval.evaluate_step(raw_context, state, replay, first["metrics"]["truth_retention_score"], 0)

    assert later["metrics"]["truth_retention_score"] < first["metrics"]["truth_retention_score"]
    assert later["metrics"]["semantic_drift_growth"] > first["metrics"]["semantic_drift_growth"]


def test_adaptive_replay_stabilizes_late_chain_drift() -> None:
    raw_context = minimal_raw_context()

    baseline_state = replay_chain_eval.initial_state(raw_context)
    baseline_replay = replay_chain_eval.replay_answers(baseline_state, raw_context["questions"])
    baseline_first = replay_chain_eval.evaluate_step(raw_context, baseline_state, baseline_replay, 1.0, 0)
    for iteration in range(2, 8):
        baseline_state = replay_chain_eval.recompress(baseline_state, baseline_replay, raw_context, iteration)
        baseline_replay = replay_chain_eval.replay_answers(baseline_state, raw_context["questions"])
    baseline_late = replay_chain_eval.evaluate_step(
        raw_context,
        baseline_state,
        baseline_replay,
        baseline_first["metrics"]["truth_retention_score"],
        0,
    )

    adaptive_state = replay_chain_eval.adaptive_initial_state(raw_context)
    adaptive_replay = replay_chain_eval.replay_answers(adaptive_state, raw_context["questions"])
    adaptive_first = replay_chain_eval.evaluate_step(
        raw_context,
        adaptive_state,
        adaptive_replay,
        1.0,
        0,
        baseline_first["metrics"],
    )
    for iteration in range(2, 8):
        adaptive_state = replay_chain_eval.adaptive_recompress(adaptive_state, adaptive_replay, raw_context, iteration)
        adaptive_replay = replay_chain_eval.replay_answers(adaptive_state, raw_context["questions"])
    adaptive_late = replay_chain_eval.evaluate_step(
        raw_context,
        adaptive_state,
        adaptive_replay,
        adaptive_first["metrics"]["truth_retention_score"],
        0,
        baseline_late["metrics"],
    )

    assert adaptive_late["metrics"]["semantic_drift_growth"] < baseline_late["metrics"]["semantic_drift_growth"]
    assert adaptive_late["metrics"]["pinned_truth_retention"] >= baseline_late["metrics"]["pinned_truth_retention"]
    assert adaptive_late["metrics"]["drift_stabilization_delta"] > 0
    assert adaptive_late["metrics"]["adaptive_continuity_score"] > baseline_late["metrics"]["adaptive_continuity_score"]
