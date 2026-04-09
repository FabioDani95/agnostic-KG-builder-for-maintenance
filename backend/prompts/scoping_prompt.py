TOC_EXTRACTION_PROMPT_TEMPLATE = """\
You are a technical document analyst. Extract the Table of Contents from the following pages.

## CONTEXT
- These are pages {toc_start_page} to {toc_end_page} (absolute PDF page numbers) of a technical manual.
- The manual has {total_pages} total pages.

## FIRST PAGES (for product identification)
{first_pages_text}

## TABLE OF CONTENTS TEXT
{toc_text}

## TASK

### Part 1: Product & Document Info
From the text, identify:
- product_name: the product or machine the manual is about
- document_type: the type of document (e.g. "Operation Manual", "Service Manual")
- language: the primary language of the document (e.g. "English", "Italian", "Multilingual")

### Part 2: Structured Table of Contents
Extract every chapter/section entry from the Table of Contents as a JSON array.
- "title": the chapter or section title exactly as written in the ToC
- "page": the page number AS PRINTED IN THE MANUAL (not the absolute PDF page number)

Include all entries you can find, preserving the order as they appear in the ToC.

## OUTPUT FORMAT
Return a JSON object:

{{"product_info": {{"product_name": "...", "document_type": "...", "language": "..."}}, \
"toc_entries": [{{"title": "Chapter 1 - Introduction", "page": 1}}, \
{{"title": "Chapter 2 - Safety", "page": 5}}, ...]}}

Return ONLY the JSON object. No markdown fences, no commentary.\
"""

SECTION_SELECTION_PROMPT_TEMPLATE = """\
You are a technical document analyst. From the structured Table of Contents below, \
select which sections are relevant for extracting a Diagnostic Knowledge Graph \
(Symptom / FailureMode / CorrectiveAction triads).

## STRUCTURED TABLE OF CONTENTS
{toc_json}

## SELECTION CRITERIA (in priority order)

STRONGLY INCLUDE sections about:
1. Troubleshooting (tables, procedures, decision trees)
2. Diagnostics and diagnostic codes
3. Error codes, alarm codes, fault codes
4. Maintenance procedures related to failures
5. Calibration and inspection procedures
6. Repair and service procedures
7. Safety warnings linked to failure conditions
8. Failure analysis or failure handling

EXCLUDE sections about:
- General product description or marketing
- Installation instructions (unless failure-related)
- Warranty, legal disclaimers, packaging, shipping
- Table of Contents itself, index pages
- Copyright, legal notices, document metadata, revision history, prefaces, overview pages
- Generic safety chapters, safety signal legends, label symbol catalogs, note/tip legend pages
- Parts lists or spare parts catalogs (unless linked to failure modes)
- Specifications or dimensions (unless related to tolerances/calibration)

When in doubt, prefer precision over recall:
- Do NOT select generic safety or introductory sections unless the title clearly indicates failure handling, troubleshooting, alarm handling, diagnostics, repair, calibration, inspection, or service procedures.
- Do NOT select revision-history or overview sections even if they mention the word "trouble shooting" incidentally.

## TASK
For each selected section, determine:
- "name": the section title exactly as it appears in the ToC
- "manual_page_start": the start page as printed in the manual (from the ToC entry)
- "manual_page_end": the end page — use the start page of the NEXT section in the ToC \
minus 1. For the last selected section, estimate the end based on the next non-selected \
section or use the total document length.
- "reasoning": brief explanation (1 sentence) of why this section is relevant

## OUTPUT FORMAT
Return a JSON object:

{{"sections": [{{"name": "Chapter 7 - Troubleshooting", "manual_page_start": 45, \
"manual_page_end": 62, "reasoning": "Contains troubleshooting tables and error codes"}}]}}

Return ONLY the JSON object. No markdown fences, no commentary.\
"""


PRODUCT_ID_PROMPT_TEMPLATE = """\
You are a technical document analyst. From the following manual pages, identify the product.

## MANUAL PAGES
{first_pages_text}

## TASK
Identify:
- product_name: the name of the product or machine this manual is about (e.g. "Alex Duetto 3", "UR5 Robot", "Citiz Espresso Machine")
- document_type: the type of document (e.g. "Owner's Manual", "Service Manual", "User Guide")
- language: the primary language (e.g. "English", "Italian")

Return ONLY a JSON object, no markdown fences, no commentary:
{{"product_name": "...", "document_type": "...", "language": "..."}}\
"""


def build_product_id_prompt(first_pages_text: str) -> str:
    return PRODUCT_ID_PROMPT_TEMPLATE.format(first_pages_text=first_pages_text)


def build_toc_extraction_prompt(
    toc_start_page: int,
    toc_end_page: int,
    total_pages: int,
    toc_text: str,
    first_pages_text: str,
) -> str:
    return TOC_EXTRACTION_PROMPT_TEMPLATE.format(
        toc_start_page=toc_start_page,
        toc_end_page=toc_end_page,
        total_pages=total_pages,
        toc_text=toc_text,
        first_pages_text=first_pages_text,
    )


def build_section_selection_prompt(toc_json: str) -> str:
    return SECTION_SELECTION_PROMPT_TEMPLATE.format(toc_json=toc_json)
