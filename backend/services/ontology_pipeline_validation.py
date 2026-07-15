"""Schema validation of ontology instances (structural + human-required fields)."""

from __future__ import annotations

import logging

from backend.models import (
    HumanRequiredField,
    OntologyInstance,
    OntologyRelationDefinition,
    OntologySchemaDefinition,
    PipelineIssue,
)
from backend.services.ontology_pipeline_coercion import (
    _collect_node_index,
    _human_prompt_for_property,
    _is_general_material_context,
    _make_human_field,
    _node_id_property,
    _schema_node_map,
    _substantive_node_count,
)
from backend.services.ontology_semantics import (
    has_actionable_instruction,
    is_escalation_instruction,
    is_operational_state_failure_mode,
)

logger = logging.getLogger(__name__)

_WILDCARD_HUMAN_FIELD_THRESHOLD = 4

def _validate_schema(ontology: OntologyInstance, schema: OntologySchemaDefinition) -> tuple[list[PipelineIssue], list[HumanRequiredField]]:
    issues: list[PipelineIssue] = []
    human_required_fields: list[HumanRequiredField] = []
    node_map = _schema_node_map(schema)
    node_index = _collect_node_index(ontology, schema)
    substantive_node_count = _substantive_node_count(ontology)

    if substantive_node_count == 0:
        issues.append(PipelineIssue(
            severity="error",
            code="empty_draft_content",
            message="Ontology draft contains only the Asset node and no extracted diagnostic content.",
            target_type="ontology",
            fix_hint="Rerun the draft with broader page coverage or review the extraction prompt/output.",
        ))

    asset_count = len(ontology.nodes.get("Asset", []) or [])
    if asset_count > 1:
        issues.append(PipelineIssue(
            severity="error",
            code="multiple_assets_detected",
            message=f"Ontology draft contains {asset_count} Asset nodes; exactly one canonical Asset is allowed.",
            target_type="Asset",
            fix_hint="Collapse duplicate Asset variants to the single scoping-selected asset identity and remap relations.",
        ))

    for node_type, items in ontology.nodes.items():
        node_def = node_map.get(node_type)
        if not node_def:
            issues.append(PipelineIssue(
                severity="error",
                code="unknown_node_type",
                message=f"Unknown node type {node_type}.",
                target_type=node_type,
            ))
            continue

        id_prop = _node_id_property(node_def)
        seen_ids: set[str] = set()
        for item in items:
            node_id = str(item.get(id_prop, "")).strip()
            if not node_id:
                issues.append(PipelineIssue(
                    severity="error",
                    code="missing_id",
                    message=f"{node_type} is missing unique identifier {id_prop}.",
                    target_type=node_type,
                    property_name=id_prop,
                ))
                continue
            if node_id in seen_ids:
                issues.append(PipelineIssue(
                    severity="error",
                    code="duplicate_id",
                    message=f"Duplicate {node_type} identifier {node_id}.",
                    target_type=node_type,
                    target_id=node_id,
                    property_name=id_prop,
                ))
                continue
            seen_ids.add(node_id)

            for prop in node_def.properties:
                val = item.get(prop.name)
                if prop.required and (val is None or (isinstance(val, str) and not val.strip())):
                    if prop.name == id_prop:
                        issues.append(PipelineIssue(
                            severity="error",
                            code="missing_id",
                            message=f"{node_type} is missing unique identifier {id_prop}.",
                            target_type=node_type,
                            target_id=node_id,
                            property_name=id_prop,
                            fix_hint="Regenerate the draft or repair the node identity before exporting.",
                        ))
                        continue

                    entity_label = str(item.get("name") or node_id or node_type).strip()
                    prompt, reason = _human_prompt_for_property(node_type, prop.name, entity_label)
                    suggested_value = ""
                    if prop.name == "source_type":
                        suggested_value = str(ontology.source_type or "").strip()
                    elif prop.name == "source_title":
                        suggested_value = str(ontology.source_title or "").strip()
                    elif prop.name == "source_reference" and item.get("source_page"):
                        suggested_value = f"PAGE {item['source_page']}"

                    human_required_fields.append(_make_human_field(
                        node_type=node_type,
                        node_id=node_id,
                        property_name=prop.name,
                        reason=reason,
                        prompt=prompt,
                        suggested_value=suggested_value,
                    ))

    for action in ontology.nodes.get("CorrectiveAction", []):
        if not isinstance(action, dict):
            continue
        instruction_text = str(action.get("instruction_text", "") or "").strip()
        # A documented escalation ("contact your factory outlet") is a valid
        # corrective action with no on-site repair verb — never flag it as
        # non-actionable.
        is_escalation = (
            str(action.get("action_kind", "") or "").strip().lower() == "escalation"
            or is_escalation_instruction(instruction_text)
        )
        if instruction_text and not is_escalation and not has_actionable_instruction(instruction_text):
            issues.append(PipelineIssue(
                severity="warning",
                code="instruction_not_actionable",
                message=(
                    f"CorrectiveAction '{action.get('name', action.get('action_id', ''))}' has "
                    "instruction_text without any restorative action step (it reads like a cause, "
                    "observation, or inspection note)."
                ),
                target_type="CorrectiveAction",
                target_id=str(action.get("action_id", "")).strip(),
                property_name="instruction_text",
                fix_hint=(
                    "Rewrite instruction_text as numbered restorative steps (replace, reconnect, "
                    "tighten, clean, adjust, calibrate, reset, ...) supported by the source page, "
                    "or remove the action if the manual provides no repair procedure."
                ),
            ))

    for fm in ontology.nodes.get("FailureMode", []):
        if not isinstance(fm, dict):
            continue
        if is_operational_state_failure_mode(
            str(fm.get("name", "") or ""),
            str(fm.get("description", "") or ""),
            str(fm.get("material_context", "") or ""),
        ):
            issues.append(PipelineIssue(
                severity="warning",
                code="operational_state_failure_mode",
                message=(
                    f"FailureMode '{fm.get('name', fm.get('failure_mode_id', ''))}' reads like a "
                    "reversible operational or safety-interlock state (e.g. door open, e-stop "
                    "pressed, cycle interrupted), not a degraded component condition."
                ),
                target_type="FailureMode",
                target_id=str(fm.get("failure_mode_id", "")).strip(),
                property_name="name",
                fix_hint=(
                    "Confirm this is a genuine failure mode. If it is an operational state or a "
                    "safety-interlock precondition, remove it, or rewrite the cause as a component "
                    "in a degraded condition that the manual supports."
                ),
            ))

    component_ids = {
        str(item.get("component_id", "")).strip()
        for item in ontology.nodes.get("Component", [])
        if isinstance(item, dict) and str(item.get("component_id", "")).strip()
    }
    for fm in ontology.nodes.get("FailureMode", []):
        if not isinstance(fm, dict):
            continue
        material_context = str(fm.get("material_context", "") or "").strip()
        if not material_context:
            continue
        if _is_general_material_context(material_context):
            continue
        if material_context not in component_ids:
            issues.append(PipelineIssue(
                severity="warning",
                code="material_context_not_linked",
                message=(
                    f"FailureMode '{fm.get('name', fm.get('failure_mode_id', ''))}' has "
                    f"material_context='{material_context}' which is not a Component.component_id."
                ),
                target_type="FailureMode",
                target_id=str(fm.get("failure_mode_id", "")).strip(),
                property_name="material_context",
                fix_hint=(
                    "Either set material_context to an existing Component.component_id, "
                    "add the missing Component node and link it here, or set it to "
                    "\"asset_level\" when the failure is genuinely general to the whole "
                    "asset. Do not leave it empty: the field is required by the export "
                    "contract."
                ),
            ))

    relation_defs = {rel.name: rel for rel in schema.relations}
    for rel in ontology.relations:
        rel_def: OntologyRelationDefinition | None = relation_defs.get(rel.name)
        if rel_def is None:
            issues.append(PipelineIssue(
                severity="error",
                code="unknown_relation",
                message=f"Unknown relation {rel.name}.",
                target_type="relation",
                target_id=rel.name,
            ))
            continue
        if rel.from_type != rel_def.domain or rel.to_type != rel_def.range:
            issues.append(PipelineIssue(
                severity="error",
                code="relation_domain_range_mismatch",
                message=f"{rel.name} must connect {rel_def.domain} -> {rel_def.range}.",
                target_type="relation",
                target_id=rel.name,
            ))
        if rel.from_id not in node_index.get(rel.from_type, set()):
            issues.append(PipelineIssue(
                severity="error",
                code="relation_missing_source",
                message=f"Relation {rel.name} references missing source node {rel.from_id}.",
                target_type="relation",
                target_id=rel.name,
            ))
        if rel.to_id not in node_index.get(rel.to_type, set()):
            issues.append(PipelineIssue(
                severity="error",
                code="relation_missing_target",
                message=f"Relation {rel.name} references missing target node {rel.to_id}.",
                target_type="relation",
                target_id=rel.name,
            ))

    # Group by (node_type, property_name). Small groups keep one field per node
    # so the operator can give node-specific values; only large groups collapse
    # into a single wildcard field (broadcast), trading per-node precision for
    # a manageable review queue.
    grouped_fields: dict[str, list[HumanRequiredField]] = {}
    for field in human_required_fields:
        group_key = f"{field.target_type}::*::{field.property_name}"
        grouped_fields.setdefault(group_key, []).append(field)

    deduped_human_fields: list[HumanRequiredField] = []
    for group_key, fields in grouped_fields.items():
        if len(fields) >= _WILDCARD_HUMAN_FIELD_THRESHOLD:
            # Represent the group with a wildcard key so _apply_human_answers
            # broadcasts the value to every node of this type missing the property.
            first = fields[0]
            prompt = (
                f"{first.prompt} The same value will be applied to all "
                f"{len(fields)} {first.target_type} nodes missing {first.property_name}."
            )
            deduped_human_fields.append(first.model_copy(update={
                "field_key": group_key,
                "target_id": "*",
                "prompt": prompt,
            }))
        else:
            deduped_human_fields.extend(fields)
    return issues, deduped_human_fields


