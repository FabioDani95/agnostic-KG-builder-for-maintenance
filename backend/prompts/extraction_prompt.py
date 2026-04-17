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
- It must reference a specific component or subsystem.
- It must NOT contain repair instructions.
- It must NOT be a test outcome, inspection outcome, verification result, or procedural checkpoint.
- A FailureMode MUST name (a) a component or subsystem AND (b) a stative condition
  (worn, loose, misaligned, dead, disconnected, out of adjustment, phased incorrectly,
  seized, contaminated, corroded, cracked, obstructed, low, high, ...).
- If the only "failure" you can find is a restatement of the symptom in past tense or
  different wording, OMIT it — do NOT invent a FailureMode.
- INCORRECT FailureMode examples:
  - "Joint verification failed"
  - "Check the cable connection"
  - "Alarm C4A0 is displayed"

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

### Severity Values (for Symptoms)
- Low
- Medium
- High
- Critical

### Relationships
- One Symptom may correspond to multiple FailureModes.
- One FailureMode may require multiple CorrectiveActions.

### Scope Consistency Rules
- Keep the extraction at the same asset scope indicated by the provided source_title.
- Do NOT broaden a controller/control-box procedure into a whole robot-system failure unless the text explicitly states the broader scope.

## OUTPUT FORMAT
Return EXACTLY three Markdown tables, in this order, with NO additional text or commentary.

### Table 1: Symptoms
| symptom_id | name | description | severity | evidence_page |
|---|---|---|---|---|

### Table 2: FailureModes
| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page |
|---|---|---|---|---|---|

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
) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        source_type=source_type,
        source_title=source_title,
        existing_id_catalog_block=existing_id_catalog_block,
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
