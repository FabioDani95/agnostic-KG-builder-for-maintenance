"""Campaign tools are offline and refuse implicit budget authorization."""

from __future__ import annotations

import json

import pytest

from backend.kg_v3.replay import ReplayProvider
from backend.kg_v3.run_state import digest
from scripts import kg_v3_quality_campaign as campaign
from scripts.kg_v3_quality_evaluate import legacy_predictions, structural_metrics
from tests.test_kg_v3_reader import troubleshooting_pdf


def corpus(tmp_path, monkeypatch):
    manual = tmp_path / "campaign" / "fixture"
    manual.mkdir(parents=True)
    troubleshooting_pdf(manual / "manual.pdf")
    (manual / "info.yaml").write_text("name: fixture\n")
    (manual / "gold").mkdir()
    (manual / "gold" / "gold.json").write_text(
        json.dumps(
            {
                "claims": [
                    {
                        "claim_id": "G.1",
                        "branch_id": "G",
                        "indicator": "No power",
                        "failure": "Blown fuse",
                        "failure_stated": True,
                        "action": "Replace fuse",
                        "action_kind": "repair",
                        "conditions": "",
                        "indicator_segments": ["p1.t1.r2"],
                        "failure_segments": ["p1.t1.r2"],
                        "action_segments": ["p1.t1.r2"],
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(campaign, "ROOT", tmp_path)
    return manual


def test_campaign_plan_has_replicas_and_never_authorizes_estimated_cost(tmp_path, monkeypatch):
    corpus(tmp_path, monkeypatch)
    manifest = campaign.plan(tmp_path / "new-campaign", ["fixture"], ["Bsafe", "S", "ALL"])
    assert len(manifest["matrix"]) == 9 and manifest["provider_calls"] == 0
    assert not manifest["estimate_is_authorization"] and not manifest["paid_calls_authorized"]
    campaign.verify_inputs(manifest)
    with pytest.raises(ValueError, match="explicit budget"):
        campaign.execute(tmp_path / "new-campaign", manifest)
    with pytest.raises(ValueError, match="at least three"):
        campaign.plan(tmp_path / "bad-replicas", ["fixture"], ["S"], replicas=1)
    with pytest.raises(ValueError, match="baseline-source"):
        campaign.plan(tmp_path / "bad-baseline", ["fixture"], ["B0"])


def test_campaign_detects_changed_condition_and_counts_failed_runs(tmp_path, monkeypatch):
    corpus(tmp_path, monkeypatch)
    out = tmp_path / "campaign-new"
    manifest = campaign.plan(out, ["fixture"], ["S"])
    rows = campaign.score_campaign(out, manifest)
    assert all(
        row["status"] == "MISSING_RUN" and row["metrics"]["recall"] == 0 and row["metrics"]["fn"] == 2 for row in rows
    )
    report = campaign.report(out)
    assert report["conditions"]["S"]["micro_recall"] == 0
    config = out / "configs" / "S.json"
    changed = json.loads(config.read_text())
    changed["graph_review"] = True
    config.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="condition changed"):
        campaign.verify_inputs(manifest)


def test_exact_replay_cannot_call_network_on_miss(tmp_path):
    import asyncio

    request = {"model": "fixture", "messages": []}
    (tmp_path / "one.json").write_text(
        json.dumps({"request": request, "response": {"model": "snapshot", "choices": []}})
    )
    provider = ReplayProvider(tmp_path)
    response = asyncio.run(provider.create(**request))
    assert response.model == "snapshot"
    with pytest.raises(ValueError, match="EXACT_REPLAY_MISS"):
        asyncio.run(provider.create(**request))


def test_campaign_freezes_runners_and_baseline_sources(tmp_path, monkeypatch):
    corpus(tmp_path, monkeypatch)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    script = baseline / "baseline.py"
    script.write_text("original baseline\n")
    (baseline / "baseline_checkout_manifest.json").write_text(
        json.dumps({"files": {"baseline.py": campaign.file_hash(script)}})
    )
    manifest = campaign.plan(tmp_path / "plan", ["fixture"], ["B0", "Bsafe"], baseline=baseline)
    campaign.verify_inputs(manifest)
    for field in ("campaign_runner_sha256", "baseline_runner_sha256"):
        with pytest.raises(ValueError, match="runner changed"):
            campaign.verify_inputs({**manifest, field: "different runner"})
    script.write_text("modified baseline\n")
    with pytest.raises(ValueError, match="baseline source changed"):
        campaign.verify_inputs(manifest)


def test_b0_and_new_conditions_share_the_same_absolute_budget_ledger(tmp_path, monkeypatch):
    from types import SimpleNamespace

    corpus(tmp_path, monkeypatch)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    (baseline / "baseline_checkout_manifest.json").write_text(json.dumps({"files": {}}))
    out = tmp_path / "plan"
    manifest = campaign.plan(out, ["fixture"], ["B0", "Bsafe"], baseline=baseline)
    invocations = []

    def stub_run(command, **kwargs):
        invocations.append((command, kwargs["cwd"]))
        return SimpleNamespace(returncode=0, stdout="fixture", stderr="")

    monkeypatch.setattr(campaign.subprocess, "run", stub_run)
    campaign.execute(out, manifest, authorization={
        "authorized": True, "authorization_reference": "TEST_ONLY_NO_PROVIDER",
        "budget_usd": 1, "ledger": "new_budget.jsonl",
    })
    assert len(invocations) == 6
    assert {cwd for _, cwd in invocations} == {tmp_path, baseline}
    assert {cmd[cmd.index("--ledger") + 1] for cmd, _ in invocations} == {str(tmp_path / "new_budget.jsonl")}
    initial_ids = {cmd[cmd.index("--run-id") + 1] for cmd, _ in invocations}
    other_out = tmp_path / "next-version"
    other = campaign.plan(other_out, ["fixture"], ["B0", "Bsafe"], baseline=baseline)
    campaign.execute(other_out, other, authorization={
        "authorized": True, "authorization_reference": "TEST_ONLY_NO_PROVIDER",
        "budget_usd": 1, "ledger": "new_budget.jsonl",
    })
    new_ids = {cmd[cmd.index("--run-id") + 1] for cmd, _ in invocations[6:]}
    assert initial_ids.isdisjoint(new_ids)


def test_legacy_adjudication_never_invents_certificates():
    graph = {
        "nodes": [
            {"id": "a", "type": "FailureMode", "name": "Blown fuse", "properties": {}},
            {"id": "b", "type": "CorrectiveAction", "name": "Replace fuse", "properties": {"action_kind": "repair"}},
        ],
        "edges": [
            {
                "id": "e",
                "type": "RESOLVED_BY",
                "from": "a",
                "to": "b",
                "tier": "green",
                "occurrences": [{"evidence": [{"segment_id": "p1.t1.r2", "page": 1}]}],
            }
        ],
    }
    before = digest(graph)
    facts, _ = legacy_predictions(graph, graph_sha256="source-hash")
    assert facts[0]["occurrences"][0]["scope_status"] == "LEGACY_UNKNOWN"
    oid = facts[0]["occurrences"][0]["assertion_id"]
    decision = {
        "graph_sha256": "source-hash",
        "legacy_fact_reviews": {
            oid: {
                "verdict": "SUPPORTED",
                "reviewer": "human",
                "scope_evidence": ["p1.t1.r2"],
                "branch_ids": ["branch"],
                "subject_denotation_status": "STATED",
                "object_denotation_status": "STATED",
                "epistemic_status": "EXPLICIT",
            }
        },
    }
    verified, branches = legacy_predictions(graph, decision, graph_sha256="source-hash")
    assert verified[0]["occurrences"][0]["scope_status"] == "VERIFIED_REVIEW" and branches["branch"]
    assert digest(graph) == before
    with pytest.raises(ValueError, match="different graph"):
        legacy_predictions(graph, decision, graph_sha256="edited")


def test_topology_declares_graph_universe_and_excludes_derived_edges():
    graph = {
        "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "asset"}],
        "edges": [
            {"from": "a", "to": "b", "tier": "green"},
            {"from": "b", "to": "c", "tier": "yellow"},
            {"from": "asset", "to": "a", "tier": "green", "derived": True},
        ],
    }
    metrics = structural_metrics(graph)
    assert metrics["views"]["green-derived"]["nodes"] == 2
    assert metrics["views"]["green+yellow+derived"]["nodes"] == 4
    assert metrics["false_merges_adjudicated"] is None
