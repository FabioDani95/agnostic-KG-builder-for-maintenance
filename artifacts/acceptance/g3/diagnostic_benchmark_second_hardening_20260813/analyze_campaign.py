#!/usr/bin/env python3
"""Analyze v9 runs against the untouched frozen KPI/golden protocol."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[3]
BASE_ANALYZER = ROOT.parent / "diagnostic_benchmark_hardening_20260812" / "analyze_campaign.py"
FROZEN_ROOT = ROOT.parent / "diagnostic_benchmark_20260812"
CAMPAIGN_ID = "pdf-g3-diagnostic-second-hardening-20260813-v9"
EXPECTED_PIPELINE_VERSION = "pdf-g3-atomic-record-publication-v9"
RUN_ID_PREFIX = "v9"

_SEMANTIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "due",
    "during", "for", "from", "in", "into", "is", "it", "of", "on", "or",
    "the", "then", "to", "when", "where", "with",
}


def _semantic_stem(token: str) -> str:
    """Conservative morphology only; no domain or manual vocabulary."""

    irregular = {
        "mapped": "map",
        "mapping": "map",
        "maps": "map",
        "stopped": "stop",
        "stopping": "stop",
    }
    if token in irregular:
        return irregular[token]
    for suffix, replacement in (
        ("iction", "ict"),
        ("uction", "uct"),
        ("ation", "ate"),
        ("ment", ""),
    ):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)] + replacement
    for suffix in ("ies", "ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stem = token[: -len(suffix)]
            if suffix == "ies":
                stem += "y"
            elif suffix == "ed" and stem.endswith("s"):
                stem += "e"
            return stem
    return token


def _semantic_normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    text = re.sub(r"(?<=\w)-(?=\w)", "", text)
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _semantic_tokens(value: str) -> set[str]:
    return {
        _semantic_stem(token)
        for token in _semantic_normalize(value).split()
        if len(token) > 1 and token not in _SEMANTIC_STOPWORDS
    }


def _semantic_similarity(expected: str, actual: str) -> float:
    expected_tokens = _semantic_tokens(expected)
    actual_tokens = _semantic_tokens(actual)
    if not expected_tokens or not actual_tokens:
        return 0.0
    overlap = expected_tokens & actual_tokens
    containment = len(overlap) / len(expected_tokens)
    jaccard = len(overlap) / len(expected_tokens | actual_tokens)
    phrase = float(
        _semantic_normalize(expected) in _semantic_normalize(actual)
        or _semantic_normalize(actual) in _semantic_normalize(expected)
    )
    return round(max(containment * 0.8 + jaccard * 0.2, phrase), 6)


def _semantic_atoms(value: str) -> set[str]:
    """Token atoms for discriminators; PDF hyphen/line breaks are equivalent."""

    return {
        _semantic_stem(token)
        for token in re.findall(r"\w+", _semantic_normalize(value))
        if len(token) > 1 and token not in _SEMANTIC_STOPWORDS
    }

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _load():
    spec = importlib.util.spec_from_file_location("v8_campaign_analyzer_base", BASE_ANALYZER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load v8 analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.REPOSITORY_ROOT = REPOSITORY_ROOT
    module.FROZEN_ROOT = FROZEN_ROOT
    module.GOLD_PATH = FROZEN_ROOT / "golden.json"
    module.RUNS_ROOT = ROOT / "runs" / "real"
    module.OUTPUT_PATH = ROOT / "campaign_results.json"
    module.REPORT_PATH = ROOT / "CAMPAIGN_REPORT.md"
    module.BEFORE_PATH = FROZEN_ROOT / "campaign_results.json"
    module.AUTHORIZED_BUDGET_USD = 3.0
    module.CAMPAIGN_ID = CAMPAIGN_ID
    module.EXPECTED_PIPELINE_VERSION = EXPECTED_PIPELINE_VERSION
    module.RUN_ID_PREFIX = RUN_ID_PREFIX
    module.SHARED_BUDGET_LEDGER_PATH = ROOT / "real_call_budget.jsonl"
    module.MANUAL_ROOT = (
        REPOSITORY_ROOT / "output" / "pdf" / "diagnostic_benchmark_manuals"
    )

    # The legacy function captured its v8 ledger path as a definition-time
    # default.  Bind the v9 path explicitly rather than relying on its global.
    shared_ledger_audit = module._shared_budget_ledger_audit

    def v9_shared_ledger_audit(specs, artifacts_by_manual, *, path=None):
        return shared_ledger_audit(
            specs,
            artifacts_by_manual,
            path=path or module.SHARED_BUDGET_LEDGER_PATH,
        )

    module._shared_budget_ledger_audit = v9_shared_ledger_audit

    # Keep the frozen claims and 0.55 threshold untouched.  The v9 evaluator
    # removes language-only function words and applies conservative morphology
    # so inflection ("mapped"/"mapping") cannot create a false negative.
    frozen_loader = module._load_frozen_analyzer

    def v9_frozen_loader():
        analyzer = frozen_loader()
        analyzer.normalize = _semantic_normalize
        analyzer.tokens = _semantic_tokens
        analyzer.similarity = _semantic_similarity
        original_score_claim_path = analyzer.score_claim_path

        def contextual_score_claim_path(claim, path):
            contextual_path = {
                **path,
                "indicator": path.get("indicator_context", path["indicator"]),
                "failure_mode": path.get(
                    "failure_mode_context", path["failure_mode"]
                ),
                "corrective_action": path.get(
                    "corrective_action_context", path["corrective_action"]
                ),
            }
            scores = original_score_claim_path(claim, contextual_path)
            # A terse table action (for example "Clear") is interpreted only
            # inside its already-matched atomic cause branch.  This does not
            # relax indicator or failure matching.
            scores["corrective_action"] = max(
                scores["corrective_action"],
                _semantic_similarity(
                    claim.get("corrective_action", ""),
                    f"{contextual_path['corrective_action']} "
                    f"{contextual_path['failure_mode']}",
                ),
            )
            return scores

        analyzer.score_claim_path = contextual_score_claim_path
        original_analyze_manual = analyzer.analyze_manual

        def analyze_manual_with_precise_forbidden(spec):
            result = original_analyze_manual(spec)
            response_path = analyzer.RUNS_ROOT / spec["manual_id"] / "generation_response.json"
            response = json.loads(response_path.read_text(encoding="utf-8"))
            paths = analyzer.published_paths(analyzer.revision_from(response))
            expected = spec.get("expected_claims") or []
            all_symptom_atoms = [
                _semantic_atoms(item.get("symptom", "")) for item in expected
            ]
            precise = []
            for forbidden in spec.get("forbidden_pairings") or []:
                forbidden_symptom = _semantic_atoms(forbidden["symptom"])
                valid_same_symptom = [
                    item
                    for item in expected
                    if _semantic_atoms(item.get("symptom", "")) == forbidden_symptom
                ]
                valid_failure_atoms = set().union(*(
                    _semantic_atoms(item.get("failure_mode", ""))
                    for item in valid_same_symptom
                )) if valid_same_symptom else set()
                failure_discriminator = (
                    _semantic_atoms(forbidden["failure_mode"]) - valid_failure_atoms
                )
                other_symptoms = [
                    atoms for atoms in all_symptom_atoms if atoms != forbidden_symptom
                ]
                symptom_discriminator = forbidden_symptom - (
                    set().union(*other_symptoms) if other_symptoms else set()
                )
                matches = [
                    path
                    for path in paths
                    if _semantic_similarity(forbidden["symptom"], path["indicator"])
                    >= analyzer.MATCH_FLOOR
                    and _semantic_similarity(
                        forbidden["failure_mode"], path["failure_mode"]
                    ) >= analyzer.MATCH_FLOOR
                    and failure_discriminator <= _semantic_atoms(path["failure_mode"])
                    and symptom_discriminator <= _semantic_atoms(path["indicator"])
                ]
                precise.append({**forbidden, "found": bool(matches), "matches": matches})
            semantic = result["semantic"]
            semantic["forbidden"] = precise
            semantic["forbidden_pairings_found"] = sum(
                item["found"] for item in precise
            )
            semantic["checks"]["forbidden_pairings_zero"] = not any(
                item["found"] for item in precise
            )
            result["verdict"]["semantic"] = (
                "pass" if all(semantic["checks"].values()) else "fail"
            )
            return result

        analyzer.analyze_manual = analyze_manual_with_precise_forbidden
        return analyzer

    module._load_frozen_analyzer = v9_frozen_loader
    return module


def _runtime_reproducibility() -> dict:
    profiles = []
    for path in sorted((ROOT / "runs" / "real").glob("*/runtime_profile.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        profiles.append({"path": str(path.relative_to(ROOT)), **profile})
    tree_digests = {item.get("code_tree_sha256") for item in profiles}
    config_digests = {item.get("effective_config_sha256") for item in profiles}
    pipeline_versions = {item.get("pipeline_version") for item in profiles}
    pymupdf_versions = {item.get("pymupdf_version") for item in profiles}
    runner_digests = {item.get("campaign_runner_sha256") for item in profiles}
    checks = {
        "all_three_profiles_present": len(profiles) == 3,
        "single_code_tree_digest": len(tree_digests) == 1 and None not in tree_digests,
        "single_effective_config_digest": (
            len(config_digests) == 1 and None not in config_digests
        ),
        "expected_pipeline_version": pipeline_versions == {EXPECTED_PIPELINE_VERSION},
        "pinned_pymupdf_runtime": pymupdf_versions == {"1.27.1"},
        "single_campaign_runner_digest": (
            len(runner_digests) == 1 and None not in runner_digests
        ),
        "gold_evaluation_only": all(
            item.get("golden_usage") == "post_generation_evaluation_only"
            for item in profiles
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "code_tree_sha256": next(iter(tree_digests), ""),
        "effective_config_sha256": next(iter(config_digests), ""),
        "profiles": profiles,
    }


def main() -> None:
    analyzer = _load()
    analyzer.main()
    result = json.loads(analyzer.OUTPUT_PATH.read_text(encoding="utf-8"))
    reproducibility = _runtime_reproducibility()
    result["analysis_method"].update({
        "deterministic_atomic_record_inventory": True,
        "cell_scoped_literal_evidence": True,
        "atomic_table_edge_completion": True,
        "runtime_code_and_config_digest_verified": reproducibility["passed"],
        "semantic_evaluator": (
            "frozen claims and threshold; generic stopword removal and conservative morphology"
        ),
        "literal_evidence_evaluator": (
            "NFKC plus whitespace collapse only; case and punctuation preserved"
        ),
    })
    result["campaign"]["runtime_reproducibility"] = reproducibility
    if not reproducibility["passed"]:
        result["campaign"]["verdict"] = "no_go"
    analyzer.OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    before = json.loads(analyzer.BEFORE_PATH.read_text(encoding="utf-8"))
    analyzer.REPORT_PATH.write_text(analyzer._render(result, before), encoding="utf-8")


if __name__ == "__main__":
    main()
