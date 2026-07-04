EXTRACTION_PROMPT_TEMPLATE = """\
You are an ontology extraction agent.
Your task is to extract a troubleshooting ontology instance from the provided manual text.

You must follow the ontology definition exactly.

## Ontology Schema
{schema_json}

## Source Metadata
- source_type: {source_type}
- source_title: {source_title}

{candidate_candidates_block}

## Instructions
1. Extract only facts explicitly supported by the text.
2. Build an ontology instance with these top-level keys only:
   - ontology_name
   - version
   - language
   - source_type
   - source_title
   - nodes
   - relations
3. The "nodes" object must contain arrays keyed by ontology node name.
4. Include only nodes and relations supported by the text.
5. If a required property is missing from the document, leave it as an empty string rather than inventing it.
6. For CorrectiveAction, set source_reference from page markers using the form "PAGE N".
7. Every relation MUST include an "evidence" array with at least one entry.
   Each evidence entry must use this exact shape (all three fields required):
     {{"source_page": 14, "source_reference": "PAGE 14", "quote": "short verbatim text from that page"}}
   Use the integer page number from the "--- PAGE N ---" markers in the text as source_page.
   The quote should be a short verbatim excerpt (10-20 words) from that page that supports the relation.
8. If the primary asset is clearly identifiable, include one Asset node.
   Fill brand, model, asset_type from the manual title page or product description.
9. You MUST attempt to extract ALL 6 node types defined in the schema, not only diagnostic triplets.
   For each node type, use its schema description as your extraction guide:
   - **Asset**: "The product, machine, robot, cobot, controller, or other technical asset that is the subject of troubleshooting knowledge."
     Extract exactly one Asset node per document.
   - **Component**: "A physical or software component or subsystem of the asset involved in troubleshooting."
     Look for: parts lists, exploded diagrams, subsystem descriptions, installation instructions naming hardware,
     maintenance sections referencing serviceable parts. Extract a Component node for each distinct physical part
     or subsystem named in the text. Software and control subsystems (cutting/control software, operator UI,
     PLC, parameter sets) are Components too — set category to "software" or "control" for them.
     Fill category from the component's functional group.
   - **Symptom**: "An observed issue, anomaly, or visible manifestation detected by the user or system."
     Extract observable problems the user would report. Fill severity based on impact described in the text.
     severity MUST be exactly one of: "Low", "Medium", "High", "Critical".
   - **FailureMode**: "The underlying technical cause or failure mechanism that may explain one or more symptoms."
     Extract root causes, NOT tests or inspection steps. Fill material_context with the physical component, subsystem,
     or the literal value "asset_level" when the failure is genuinely general to the whole asset.
   - **CorrectiveAction**: "An action, procedure, or remediation step intended to resolve a failure mode."
     Extract repair or remediation procedures, NOT inspection-only steps. Fill instruction_text with the actual steps,
     source_reference as "PAGE N".
   - **ErrorCode**: "A machine-generated error code or alert code produced by the asset."
     Look for: alarm code tables, fault code lists, diagnostic display codes, PID alarm values.
     Extract each distinct code. Fill the "code" property with the exact alphanumeric code from the text.
10. You MUST also create ALL 6 relation types defined in the schema when supported by the text:
    - HAS_COMPONENT: Asset → Component (for every Component extracted)
    - MAY_INDICATE: Symptom → FailureMode
    - AFFECTS: FailureMode → Component (link failure modes to the MOST SPECIFIC Component
      named in the failure context — never fall back to the root asset or the highest-level
      assembly unless the text explicitly names only that level. If the specific component
      is not yet in the Component list, ADD it as a new Component BEFORE emitting the
      AFFECTS relation.)
    - RESOLVED_BY: FailureMode → CorrectiveAction
    - GENERATES_ERROR: Asset → ErrorCode (for every ErrorCode extracted)
    - INDICATES: ErrorCode → FailureMode (link error codes to the failure they signal)
11. Component and ErrorCode nodes are valuable STANDALONE — extract them even when they are
    not part of a complete Symptom → FailureMode → CorrectiveAction chain.
    A parts list should produce Component nodes. An alarm table should produce ErrorCode nodes.
12. Deduplicate repeated entities.
13. Set the top-level "language" field to the detected language of the source document (e.g. "en", "it", "de").
14. Write all human-readable field values in the same language as the source document.
15. Keep JSON keys, node type names, relation names, IDs, and the source_reference format "PAGE N" unchanged.
16. Return JSON only. No markdown. No commentary.
17. Keep the Asset scope aligned with source_title. Do NOT broaden a "control box" or "controller" manual into a whole "robot system" unless the manual text explicitly requires that broader scope.
18. A FailureMode must be a technical cause, not a failed test, verification result, inspection result, or procedural step.
    A valid FailureMode MUST name (a) a component or subsystem — physical OR software/control
    (a software application, a configuration set, a parameter, a calibration, a mapping) —
    AND (b) a stative condition. Stative conditions include physical states (worn, loose,
    misaligned, dead, disconnected, out of adjustment, phased incorrectly, seized,
    contaminated, cracked, obstructed, ...) AND configuration states (not mapped,
    not assigned, misconfigured, disabled, out of calibration, wrong parameter value, ...).
    Contrast examples:
    - Symptom "The tool changer gets hung up." → FailureMode "Pneumatic solenoid valve
      stuck open on ATC circuit." (NOT "Tool changer hung up")
    - Symptom "An alarm is displayed." → FailureMode "Spindle orient parameter P4031
      misconfigured after control reload." (NOT "A fault occurs")
    - Symptom "Window damaged or severely scratched." → FailureMode "Impact from flying chip
      cracked the polycarbonate window pane." (NOT "Damaged or scratched window panel")
    - Symptom "The cutting tool does not move down." → FailureMode "Cutting layer not mapped
      to a tool in the cutting software." (NOT "Tool mapping problem", NOT "Tool does not
      come down")
    Still NOT valid FailureModes: outcomes of checks ("Verification of tool mapping failed"),
    and operator or context faults that name no system state ("operator error", "wrong usage").
    If the only FailureMode you can find is a lexical restatement of the Symptom, OMIT it —
    do not invent one.
19. A CorrectiveAction must be a restorative action, not an inspection-only or verification-only step unless that step itself resolves the fault according to the text.
20. FailureMode.material_context should reference an EXISTING Component.component_id
    when the text names a specific component or subsystem (e.g. "comp_spindle_motor").
    If no Component node represents a specifically named component/subsystem, add it
    FIRST, then set material_context to that component_id. If the failure is general
    to the whole asset or the manual does not state a component, set material_context
    to "asset_level". Do NOT invent a component solely to satisfy this field.
21. If the text contains alphanumeric patterns matching alarm/error conventions
    (e.g. "C0330", "H0216", "Alarm 215", "E504") or phrases of the form
    "<adjective> alarm is set", "alarm '<text>' is displayed", "error <code>
    occurs", "timeout in <subsystem>", you MUST produce an ErrorCode node AND a
    corresponding INDICATES relation (ErrorCode → FailureMode) whenever the text
    links the code to a specific failure. A GENERATES_ERROR relation (Asset →
    ErrorCode) MUST also be emitted for each ErrorCode.
    HOWEVER, an ErrorCode is ONLY valid when the text presents it as an alarm,
    error, or fault indication produced by the asset. Do NOT emit ErrorCode nodes for:
    - part numbers or position codes from parts lists, exploded views, or assembly drawings
    - referenced standards or regulations (e.g. "ANSI Z136", "ISO 13849")
    - fuse/connector/pin designators (e.g. "F3", "CN1") unless the text describes them as displayed codes
    If you cannot point to text presenting the token as an alarm/error/fault, OMIT it.
22. Preserve the granularity of alarm/fault tables. When a table presents distinct rows
    (typically one per error code or per problem), keep one distinct diagnostic chain per row:
    the row's own Symptom, its own FailureMode(s), its own CorrectiveAction(s), and — when the
    row shows a code — the ErrorCode with its INDICATES link to that row's FailureMode(s).
    Do NOT merge the causes or actions of one row into a broader symptom taken from another
    row or another section (e.g. a troubleshooting flowchart). When the same underlying failure
    appears both in an alarm table and in a flowchart, extract BOTH views and connect them by
    reusing the same FailureMode node — never by collapsing one view into the other.

## IMPORTANT: ID Uniqueness
- All IDs must be globally unique and descriptive, not just sequential numbers.
- Use a short type prefix + snake_case description derived from the node name:
  - Component "Hydraulic Pump" → component_id: "comp_hydraulic_pump"
  - Symptom "Motor overheating" → symptom_id: "sym_motor_overheating"
  - FailureMode "Bearing wear" → failure_mode_id: "fm_bearing_wear"
  - CorrectiveAction "Replace bearing" → action_id: "ca_replace_bearing"
  - ErrorCode "Alarm E05" → error_code_id: "err_alarm_e05"
- NEVER use generic sequential IDs like "SYM-001", "FM-002", "COMP-003".
  Sequential IDs collide when multiple document sections are processed independently.
- IDs must use only lowercase letters, digits, and underscores.
- When unsure, generate the ID by: lowercasing the name, replacing spaces with underscores,
  keeping only [a-z0-9_], and prepending the type prefix.
"""


VALIDATION_PROMPT_TEMPLATE = """\
You are an ontology validation agent.
Review the ontology instance against the ontology schema and the provided manual text.

## Ontology Schema
{schema_json}

## Validation Goals
1. Detect unsupported claims.
2. Detect missing required links between extracted entities when the text clearly supports them.
3. Detect semantic mismatches:
   - wrong relation direction
   - wrong node type
   - action written as a failure mode
   - symptom written as a cause
4. Do not complain about fields intentionally left blank when the source text does not provide them.

Return JSON only with this shape:
{{
  "issues": [
    {{
      "severity": "error|warning",
      "code": "short_code",
      "message": "what is wrong",
      "target_type": "NodeType or relation",
      "target_id": "entity id if any",
      "property_name": "field if any",
      "fix_hint": "minimal concrete fix"
    }}
  ]
}}
"""


def build_ontology_extraction_prompt(
    schema_json: str,
    source_type: str,
    source_title: str,
    candidate_candidates_block: str = "",
) -> str:
    return EXTRACTION_PROMPT_TEMPLATE.format(
        schema_json=schema_json,
        source_type=source_type,
        source_title=source_title,
        candidate_candidates_block=candidate_candidates_block,
    )


RELATION_EXTRACTION_PROMPT_TEMPLATE = """\
You are an ontology relation extraction agent.
Your task is to add only ontology relations between already-extracted nodes.

## Allowed Relations
- MAY_INDICATE: Symptom -> FailureMode
- AFFECTS: FailureMode -> Component
- RESOLVED_BY: FailureMode -> CorrectiveAction
- GENERATES_ERROR: Asset -> ErrorCode
- INDICATES: ErrorCode -> FailureMode

## Candidate Nodes
{candidate_nodes_json}

## Existing Relations
{existing_relations_json}

## Instructions
1. Do NOT create, rename, or delete nodes.
2. Use only the node IDs listed in Candidate Nodes.
3. Do NOT emit HAS_COMPONENT. The system derives it deterministically.
4. Do NOT repeat any relation already present in Existing Relations.
5. Return only relations strongly supported by the text. Prefer precision, but do not omit clear links.
   For causal relations (MAY_INDICATE, RESOLVED_BY, INDICATES) the evidence must come from the
   SAME text unit that states the link — the same table row, the same flowchart branch, or the
   same sentence. Two entities merely appearing on the same page is NOT evidence of causation.
6. Every returned relation MUST include an "evidence" array with at least one entry.
   Each evidence entry must use this exact shape:
     {{"source_page": 14, "source_reference": "PAGE 14", "quote": "short verbatim text from that page"}}
7. Use the integer page number from the "--- PAGE N ---" markers in the text as source_page.
8. The quote must be a short verbatim excerpt from the supporting page.
9. Return JSON only with this exact shape:
{{
  "relations": [
    {{
      "name": "RELATION_NAME",
      "from_type": "NodeType",
      "from_id": "node_id",
      "to_type": "NodeType",
      "to_id": "node_id",
      "evidence": [
        {{"source_page": 14, "source_reference": "PAGE 14", "quote": "supporting excerpt"}}
      ]
    }}
  ]
}}
"""


def build_ontology_relation_extraction_prompt(
    candidate_nodes_json: str,
    existing_relations_json: str,
) -> str:
    return RELATION_EXTRACTION_PROMPT_TEMPLATE.format(
        candidate_nodes_json=candidate_nodes_json,
        existing_relations_json=existing_relations_json,
    )


RE_EXTRACTION_PROMPT_TEMPLATE = """\
You are an ontology extraction agent performing a corrective re-extraction pass.

A previous extraction attempt produced the ontology instance below, but the semantic validator
identified the following issues that must be resolved:

## Issues to Fix
{issues_summary}

## Ontology Schema
{schema_json}

## Source Metadata
- source_type: {source_type}
- source_title: {source_title}

## Previous Ontology Instance (authoritative baseline — do NOT re-emit it)
{previous_ontology_json}

{candidate_candidates_block}

## Instructions
1. Return ONLY a JSON PATCH against the previous ontology instance. Do NOT return the full
   ontology: everything not mentioned in your patch is kept unchanged by the system.
   The patch must use exactly this shape (all four keys optional):
{{
  "upsert_nodes": {{"NodeType": [ complete node objects, same shape as in the previous instance ]}},
  "remove_node_ids": ["node_id", ...],
  "add_relations": [ complete relation objects with evidence ],
  "remove_relations": [{{"name": "RELATION_NAME", "from_id": "node_id", "to_id": "node_id"}}]
}}
2. For each issue, apply the fix_hint if provided; do not invent facts not in the text.
   When an issue has code="symptom_failure_duplicate", you MUST either:
   (a) upsert the FailureMode rewritten in causal form (name a component AND a stative condition
       like worn/loose/misaligned/dead/disconnected/out of adjustment/phased incorrectly/...), or
   (b) put the FailureMode id in remove_node_ids — its MAY_INDICATE edges are dropped automatically.
   Do NOT simply rename the FailureMode while keeping the same observational description.
3. Touch ONLY what the issues describe. Never re-emit nodes or relations that are already correct.
4. Each entry in "upsert_nodes" REPLACES the node with the same id, or ADDS a new node when the id
   does not exist yet. Always emit COMPLETE node objects (all properties), never partial diffs.
5. Preserve existing IDs and wording unless an issue specifically requires a change. New nodes
   follow the original ID rules: type prefix + snake_case name, lowercase [a-z0-9_] only.
6. Do NOT introduce new speculative nodes or relations beyond what the text supports.
   If no valid fix exists for an issue, omit it rather than inventing content — an empty patch
   {{}} is valid when nothing can be fixed from the text.
7. Removing nodes also removes every relation touching them; do not list those relations again
   in remove_relations.
8. Apply all constraints from the original extraction instructions to everything you upsert:
   - FailureMode must be a technical cause naming a component or subsystem (physical OR
     software/control) in a stative condition — physical (worn, loose, seized, ...) or
     configuration (not mapped, misconfigured, out of calibration, ...). Never a
     test/verification/inspection result, and never operator error without a system state.
   - CorrectiveAction must be a restorative action, not inspection-only.
   - Asset scope must remain aligned with source_title.
   - AFFECTS must point to the MOST SPECIFIC Component in the failure context;
     add a Component node BEFORE emitting AFFECTS when the specific part is missing.
   - FailureMode.material_context should reference an existing Component.component_id
     when the text names a specific part/subsystem, or "asset_level" when the failure
     is general to the whole asset.
   - ErrorCode nodes MUST be produced whenever the text shows alphanumeric alarm
     tokens or natural-language alarm phrases, with GENERATES_ERROR and (when
     linked to a failure) INDICATES relations. Do NOT emit ErrorCode nodes for
     part numbers from parts lists/exploded views, referenced standards
     (e.g. ANSI Z136), or fuse/connector designators not shown as displayed codes.
   - Preserve alarm/fault table granularity: one distinct diagnostic chain per table
     row; do not merge one row's causes or actions into a broader symptom from another
     row or section. Connect table and flowchart views by reusing the same FailureMode
     node, never by collapsing one into the other.
   - Symptom.severity must be exactly one of: "Low", "Medium", "High", "Critical".
9. Every relation in "add_relations" MUST include an "evidence" array with at least one entry.
   Each evidence entry must use this exact shape (all three fields required):
     {{"source_page": 14, "source_reference": "PAGE 14", "quote": "short verbatim text from that page"}}
   Use the integer page number from the "--- PAGE N ---" markers in the text as source_page.
   The quote should be a short verbatim excerpt (10-20 words) from the SAME text unit
   (table row, flowchart branch, or sentence) that states the relation.
10. Return JSON only — the patch object, nothing else. No markdown. No commentary.
"""


def build_ontology_re_extraction_prompt(
    schema_json: str,
    source_type: str,
    source_title: str,
    issues_summary: str,
    previous_ontology_json: str,
    candidate_candidates_block: str = "",
) -> str:
    return RE_EXTRACTION_PROMPT_TEMPLATE.format(
        schema_json=schema_json,
        source_type=source_type,
        source_title=source_title,
        issues_summary=issues_summary,
        previous_ontology_json=previous_ontology_json,
        candidate_candidates_block=candidate_candidates_block,
    )


def build_ontology_validation_prompt(schema_json: str) -> str:
    return VALIDATION_PROMPT_TEMPLATE.format(schema_json=schema_json)
