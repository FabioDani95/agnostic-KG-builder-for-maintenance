SYSTEM_PROMPT_TEMPLATE = """\
You are a technical diagnostic extraction system.
You analyze maintenance documentation and extract structured diagnostic triads.

## TASK
Analyze the provided technical text and extract all diagnostic information into exactly three Markdown tables.

## RULES — STRICT COMPLIANCE REQUIRED

### Extraction Rules
1. Extract ONLY information explicitly present in the source text. NEVER invent, speculate, or add details not in the document.
2. If information is incomplete, keep the description minimal. Do NOT speculate.

### Symptom Rules
- A Symptom describes an **observable anomaly or abnormal behavior**.
- It must describe WHAT is observed, NEVER the cause.
- Use neutral, objective, concise technical language.
- CORRECT: "Nozzle temperature fluctuates ±10°C during printing"
- INCORRECT: "Nozzle temperature fluctuates because the thermistor is broken"

### FailureMode Rules
- A FailureMode describes the **technical cause** responsible for one or more symptoms.
- It should reference a specific component or subsystem when the manual names one.
- If the cause is genuinely general to the whole asset, use `asset_level` in `material_context`.
- It must NOT contain repair instructions.
- It must NOT be a test outcome, inspection outcome, verification result, or procedural checkpoint.
- A component-specific FailureMode MUST name (a) a component or subsystem AND (b) a stative condition
  (worn, loose, misaligned, dead, disconnected, out of adjustment, phased incorrectly,
  seized, contaminated, corroded, cracked, obstructed, low, high, ...).
- An asset-level FailureMode must still name a technical condition, configuration state, communication state,
  operating state, or other causal condition; do NOT use `asset_level` to restate a symptom.
- If the only "failure" you can find is a restatement of the symptom in past tense or
  different wording, OMIT it — do NOT invent a FailureMode.
- INCORRECT FailureMode examples:
  - "Joint verification failed"
  - "Check the cable connection"
  - "Alarm C4A0 is displayed"

### SELF-CLASSIFICATION (why_failure_mode column)
- For EVERY FailureMode row you emit, the `why_failure_mode` column MUST explicitly name:
  (component_or_subsystem) + (stative_condition).
- Template: "<component_or_subsystem>: <stative condition>".
- If you cannot fill both halves from the source, the row is NOT a FailureMode — OMIT it
  or keep it as a Symptom instead.
- Examples of correct `why_failure_mode` values:
  - "ATC pneumatic solenoid valve: stuck open"
  - "Spindle orient parameter P4031: misconfigured"
  - "Polycarbonate window pane: cracked by impact"
- Examples of INVALID `why_failure_mode` values (these reveal a miscategorised row):
  - "tool changer: hung up"  ← this is an observation, not a stative cause
  - "alarm: displayed"       ← this is an observation
  - "verification: failed"   ← this is a procedural outcome

### CONTRAST EXAMPLES (how a FailureMode differs from a Symptom)
- Symptom (observable event):  "The tool changer gets hung up."
  FailureMode (stative cause): "Pneumatic solenoid valve stuck open on ATC circuit."
  WRONG FailureMode: "Tool changer hung up."  ← restates the symptom
- Symptom (observable event):  "An alarm is displayed."
  FailureMode (stative cause): "Spindle orient parameter P4031 misconfigured after control reload."
  WRONG FailureMode: "A fault occurs."  ← circular restatement
- Symptom (observable event):  "Window damaged or severely scratched."
  FailureMode (stative cause): "Impact from flying chip cracked the polycarbonate window pane."
  WRONG FailureMode: "Damaged or scratched window panel."  ← restates the symptom

### Evidence Page Rules (applies to Symptom, FailureMode, and CorrectiveAction)
- EVERY extracted row MUST include an `evidence_page` (or `source_page` for CorrectiveAction) pointing
  to the page that grounds the extraction.
- The text is annotated with page markers like "--- PAGE N ---". Use these to determine the page.
- If a concept is discussed across multiple pages, pick the FIRST page where it appears with
  enough context to make the row recoverable.
- If you cannot locate a page, OMIT the row. NEVER emit `0`, empty, or a speculative page.

### CorrectiveAction Rules
- A CorrectiveAction describes the **repair procedure** required to resolve a failure mode.
- Each CorrectiveAction MUST include the page number (source_page) where the procedure appears in the document.
- The text is annotated with page markers like "--- PAGE N ---". Use these to determine source_page.
- The **instruction_text** field MUST contain a numbered step-by-step list (1. 2. 3. ...) of the procedure.
- The wording MUST stay as close as possible to the original text. Minimal rephrasing only. Do NOT add information that is not in the source document.
- Do NOT extract inspection-only or verification-only steps as CorrectiveAction unless the text explicitly states that this step resolves the failure.
- Prefer true restorative actions such as replace, reconnect, tighten, clean, adjust, calibrate, reset, or reboot over diagnostic checks.
- Apply these metadata to ALL CorrectiveActions:
  - source_type: {source_type}
  - source_title: {source_title}

### Output Language Rules
- Write all human-readable values in the same language as the source document.
- Keep table headers, IDs, linked IDs, and severity values exactly in English as specified below.

### ID Format
- Symptom IDs: SYM-001, SYM-002, SYM-003, ...
- FailureMode IDs: FM-001, FM-002, FM-003, ...
- CorrectiveAction IDs: CA-001, CA-002, CA-003, ...
- IDs must be sequential and unique.

{existing_id_catalog_block}

{seed_rows_block}

### Severity Values (for Symptoms)
- Low
- Medium
- High
- Critical

### Relationships
- One Symptom may correspond to multiple FailureModes.
- One FailureMode may require multiple CorrectiveActions.
- A Symptom MAY appear without an accompanying FailureMode or CorrectiveAction when the text
  describes the symptom only (e.g. diagnostic index chapters). Emit it anyway — downstream
  passes will reconcile cross-chunk linkages.

### Scope Consistency Rules
- Keep the extraction at the same asset scope indicated by the provided source_title.
- Do NOT broaden a controller/control-box procedure into a whole robot-system failure unless the text explicitly states the broader scope.

## FEW-SHOT EXAMPLES (illustrative — do NOT copy verbatim into your output)

### Example Symptoms
| symptom_id | name | description | severity | evidence_page |
|---|---|---|---|---|
| SYM-EX1 | Tool changer gets hung up | ATC fails to complete the tool change cycle. | High | 12 |
| SYM-EX2 | Alarm C0330 displayed | Control panel shows alarm code C0330 during startup. | Medium | 42 |

### Example FailureModes
| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page | why_failure_mode |
|---|---|---|---|---|---|---|
| FM-EX1 | Solenoid valve stuck open | ATC pneumatic solenoid valve fails in the open position, preventing the cycle from sequencing correctly. | ATC pneumatic circuit | SYM-EX1 | 13 | ATC pneumatic solenoid valve: stuck open |
| FM-EX2 | Spindle orient parameter misconfigured | Parameter P4031 has reverted to default after a control reload, causing an orientation fault at startup. | Spindle control parameter P4031 | SYM-EX2 | 43 | Spindle orient parameter P4031: misconfigured |

### Example CorrectiveActions
| action_id | name | description | instruction_text | source_type | source_title | source_page | linked_failure_mode_id |
|---|---|---|---|---|---|---|---|
| CA-EX1 | Replace solenoid valve | Replace the ATC pneumatic solenoid valve and verify cycle. | 1. Power off the ATC circuit. 2. Disconnect the pneumatic line. 3. Replace the solenoid valve. 4. Reconnect and cycle the tool changer once to verify. | {source_type} | {source_title} | 14 | FM-EX1 |

## OUTPUT FORMAT
Return EXACTLY three Markdown tables, in this order, with NO additional text or commentary.
Do NOT include the rows with IDs prefixed by "EX" from the examples above — those are
illustrative only.

### Table 1: Symptoms
| symptom_id | name | description | severity | evidence_page |
|---|---|---|---|---|

### Table 2: FailureModes
| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page | why_failure_mode |
|---|---|---|---|---|---|---|

### Table 3: CorrectiveActions
| action_id | name | description | instruction_text | source_type | source_title | source_page | linked_failure_mode_id |
|---|---|---|---|---|---|---|---|

IMPORTANT: The linked_symptom_id column in FailureModes must reference a valid symptom_id.
The linked_failure_mode_id column in CorrectiveActions must reference a valid failure_mode_id.
Output ONLY the three tables. No introductions, no summaries, no explanations.\
"""


def build_extraction_prompt(
    source_type: str,
    source_title: str,
    existing_id_catalog_block: str = "",
    seed_rows_block: str = "",
) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        source_type=source_type,
        source_title=source_title,
        existing_id_catalog_block=existing_id_catalog_block,
        seed_rows_block=seed_rows_block,
    )


def build_existing_id_catalog_block(
    ontology_draft: dict | None,
    *,
    max_entries_per_type: int = 40,
) -> str:
    """Render a catalog of already-extracted entity IDs so the triplet extractor
    can re-use them instead of minting new sequential IDs that duplicate draft nodes.

    Returns empty string when there is no draft to draw from.
    """
    if not ontology_draft or not isinstance(ontology_draft, dict):
        return ""
    nodes = ontology_draft.get("nodes") or {}
    sections: list[str] = []
    node_specs = [
        ("Symptom", "symptom_id", "Existing Symptoms"),
        ("FailureMode", "failure_mode_id", "Existing FailureModes"),
        ("CorrectiveAction", "action_id", "Existing CorrectiveActions"),
    ]
    for node_type, id_field, label in node_specs:
        items = nodes.get(node_type) or []
        rendered_rows: list[str] = []
        for item in items[:max_entries_per_type]:
            if not isinstance(item, dict):
                continue
            entity_id = str(item.get(id_field, "")).strip()
            name = str(item.get("name", "")).strip()
            if not entity_id:
                continue
            rendered_rows.append(f"- {entity_id}: {name}" if name else f"- {entity_id}")
        if rendered_rows:
            sections.append(f"### {label}")
            sections.extend(rendered_rows)
    if not sections:
        return ""
    return (
        "## EXISTING ENTITY IDS (reuse these when the concept matches)\n"
        "If one of the rows below describes the same concept you would otherwise emit, "
        "REUSE its ID instead of minting a new sequential ID. Only mint a new "
        "sequential ID (SYM-NNN, FM-NNN, CA-NNN) when no existing entity matches.\n"
        + "\n".join(sections)
    )


def _escape_cell(value: object) -> str:
    """Make a value safe to render inside a Markdown table cell."""
    text = str(value or "").replace("\r", " ").replace("\n", " ").replace("|", "/")
    text = " ".join(text.split())
    return text.strip()


def _render_markdown_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def build_seed_rows_block(
    ontology_draft: dict | None,
    *,
    max_entries_per_type: int = 40,
) -> str:
    """Render the ontology draft's Symptoms/FailureModes/CorrectiveActions as
    pre-filled Markdown table rows ("seed rows").

    These rows are injected into the extraction prompt as a validated baseline.
    The LLM is instructed to EXTEND this baseline with any new findings from the
    chunk text and to REUSE IDs/classifications rather than re-classify existing
    entities. This keeps the triplet-extraction pass aligned with the
    type-decisions already made during the ontology-draft pass.
    """
    if not ontology_draft or not isinstance(ontology_draft, dict):
        return ""
    nodes = ontology_draft.get("nodes") or {}

    symptom_rows: list[str] = []
    for item in (nodes.get("Symptom") or [])[:max_entries_per_type]:
        if not isinstance(item, dict):
            continue
        entity_id = _escape_cell(item.get("symptom_id"))
        name = _escape_cell(item.get("name"))
        if not entity_id or not name:
            continue
        description = _escape_cell(item.get("description"))
        severity = _escape_cell(item.get("severity") or "Medium")
        evidence_page = _escape_cell(
            item.get("evidence_page") or item.get("source_page") or ""
        )
        symptom_rows.append(_render_markdown_row([
            entity_id, name, description, severity, evidence_page,
        ]))

    failure_rows: list[str] = []
    for item in (nodes.get("FailureMode") or [])[:max_entries_per_type]:
        if not isinstance(item, dict):
            continue
        entity_id = _escape_cell(item.get("failure_mode_id"))
        name = _escape_cell(item.get("name"))
        if not entity_id or not name:
            continue
        description = _escape_cell(item.get("description"))
        material_context = _escape_cell(item.get("material_context"))
        linked_symptom_id = _escape_cell(item.get("linked_symptom_id"))
        evidence_page = _escape_cell(item.get("evidence_page") or "")
        why = _escape_cell(
            item.get("why_failure_mode")
            or (f"{material_context}: {description}" if material_context else description)
        )
        failure_rows.append(_render_markdown_row([
            entity_id, name, description, material_context,
            linked_symptom_id, evidence_page, why,
        ]))

    action_rows: list[str] = []
    for item in (nodes.get("CorrectiveAction") or [])[:max_entries_per_type]:
        if not isinstance(item, dict):
            continue
        entity_id = _escape_cell(item.get("action_id"))
        name = _escape_cell(item.get("name"))
        if not entity_id or not name:
            continue
        description = _escape_cell(item.get("description"))
        instruction_text = _escape_cell(item.get("instruction_text"))
        source_type = _escape_cell(item.get("source_type"))
        source_title = _escape_cell(item.get("source_title"))
        source_page = _escape_cell(item.get("source_page") or "")
        linked_failure_mode_id = _escape_cell(item.get("linked_failure_mode_id"))
        action_rows.append(_render_markdown_row([
            entity_id, name, description, instruction_text,
            source_type, source_title, source_page, linked_failure_mode_id,
        ]))

    if not (symptom_rows or failure_rows or action_rows):
        return ""

    lines: list[str] = [
        "## CANDIDATE ROWS FROM ONTOLOGY DRAFT (extend and verify)",
        "The rows below were produced by the ontology-draft pass. Treat them as a "
        "RECALL FLOOR and ID catalog, not unquestionable ground truth:",
        "- Reuse the type assignment when the chunk text supports it.",
        "- If the chunk clearly contradicts a candidate type, omit or correct that row rather than preserving an error.",
        "- Reuse their IDs verbatim when the same concept reappears in this chunk.",
        "- Emit supported candidate rows, then ADD new rows you discover in the chunk text "
        "(using fresh sequential IDs that do not collide with the IDs above).",
        "- When writing a new FailureMode, you MAY use a candidate Component as "
        "material_context even if that Component is not mentioned in this chunk.",
        "",
    ]
    if symptom_rows:
        lines.append("### Seed Symptoms")
        lines.append("| symptom_id | name | description | severity | evidence_page |")
        lines.append("|---|---|---|---|---|")
        lines.extend(symptom_rows)
        lines.append("")
    if failure_rows:
        lines.append("### Seed FailureModes")
        lines.append(
            "| failure_mode_id | name | description | material_context | "
            "linked_symptom_id | evidence_page | why_failure_mode |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        lines.extend(failure_rows)
        lines.append("")
    if action_rows:
        lines.append("### Seed CorrectiveActions")
        lines.append(
            "| action_id | name | description | instruction_text | "
            "source_type | source_title | source_page | linked_failure_mode_id |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        lines.extend(action_rows)
        lines.append("")

    return "\n".join(lines).rstrip()
