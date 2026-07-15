"""Triplet-review tools: approve, skip, edit and fetch the next triplet.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from backend.services.conversation.tools.common import (
    _apply_triplet_patch,
    _build_review_graph_payload,
    _contains_triplet,
    _triplet_logic_assessment,
)


async def _approve_triplet(args, store, on_event):
    idx = args["index"]
    patch = args.get("patch") or {}
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    triplet = triplets[idx]
    if patch:
        import copy
        triplet = _apply_triplet_patch(copy.deepcopy(triplet), patch)
        triplets[idx] = triplet
        gs["cleaned_triplets"] = triplets
        store["graph_state"] = gs
    validated = store.setdefault("validated_triplets", [])
    if not _contains_triplet(validated, triplet):
        validated.append(triplet)
    store["review_index"] = idx + 1
    return {
        "status": "ok",
        "action": "validated",
        "index": idx,
        "graph": _build_review_graph_payload(store),
        "widget": "extraction_graph",
    }


async def _skip_triplet(args, store, on_event):
    idx = args["index"]
    store["review_index"] = idx + 1
    return {
        "status": "ok",
        "action": "skipped",
        "index": idx,
        "graph": _build_review_graph_payload(store),
        "widget": "extraction_graph",
    }


async def _edit_triplet(args, store, on_event):
    idx = args["index"]
    patch = args.get("patch") or {}
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    if not triplets or idx >= len(triplets):
        return {"status": "error", "message": f"No triplet at index {idx}."}

    import copy
    triplet = _apply_triplet_patch(copy.deepcopy(triplets[idx]), patch)

    triplets[idx] = triplet
    gs["cleaned_triplets"] = triplets
    store["graph_state"] = gs
    return {
        "status": "ok",
        "action": "edited",
        "index": idx,
        "total": len(triplets),
        "triplet": triplet,
        "graph": _build_review_graph_payload(store, focus_index=idx),
        "widget": "triplet",
        "logic_assessment": _triplet_logic_assessment(triplet),
        "message": "Triplet edits saved. Review the updated card before approving or skipping.",
    }


async def _get_next_triplet(args, store, on_event):
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    review_index = store.get("review_index", 0)

    if review_index >= len(triplets):
        # All done — update phase to EXPORT
        from backend.graph.state import GraphPhase
        from backend.graph.store import _record_phase
        _record_phase(
            store, phase=GraphPhase.EXPORT,
            agent="TripletReviewAgent", decision="all_reviewed",
        )
        validated = store.get("validated_triplets") or []
        return {
            "status": "done",
            "total": len(triplets),
            "validated": len(validated),
            "exported": False,
            "message": (
                f"All {len(triplets)} triplet(s) reviewed — "
                f"{len(validated)} validated, {len(triplets) - len(validated)} skipped. "
                "Ready to export!"
            ),
            "widget": "export",
        }

    triplet = triplets[review_index]

    # Proactive critic
    if on_event:
        try:
            from backend.services.conversation.critic import critique_triplet
            for critique in critique_triplet(triplet, store):
                on_event(critique)
        except Exception:
            pass

    return {
        "status": "ok",
        "index": review_index,
        "total": len(triplets),
        "triplet": triplet,
        "logic_assessment": _triplet_logic_assessment(triplet),
        "graph": _build_review_graph_payload(store, focus_index=review_index),
        "widget": "triplet",
    }
