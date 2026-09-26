# Catene estratte da verificare

Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.

## Ramo 1

ID: `dbranch_03a669ef60b4b54789ea37dfa909388cf372e5ed0235bdcbc0ae0b6928dfaae3`. Pagine: [69].

- Internal compressor LED and temperature LED illuminate → Internal compressor air inlet filter completely clogged → Replace the compressor’s air inlet filter

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_7c4836b614e4b3aad94395b22379ddaaff48c1da5388b6d291a598843d365269",
  "branch_lineage_id": "dbranch_03a669ef60b4b54789ea37dfa909388cf372e5ed0235bdcbc0ae0b6928dfaae3",
  "record_window_id": "diagwin_801ada29217e8fba589c7ff1",
  "record_anchor": "ev_4e090bb09612002cb933451d4a14",
  "branch_anchor": "ev_72ec954354dc034de91d5d68ac77",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Internal compressor LED and temperature LED illuminate",
      "description": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_4e090bb09612002cb933451d4a14",
          "source_page": 69,
          "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
          "evidence_id": "ev_4e090bb09612002cb933451d4a14",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 1,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_4e090bb09612002cb933451d4a14",
          "source_page": 69,
          "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
          "evidence_id": "ev_4e090bb09612002cb933451d4a14",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 1,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "The air inlet filter on the internal compressor is completely clogged.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Internal compressor air inlet filter completely clogged",
    "description": "The air inlet filter on the internal compressor is completely clogged.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
        "source_page": 69,
        "quote": "The air inlet filter on the internal compressor is completely clogged.",
        "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
        "locator": {
          "kind": "pdf",
          "page": 69,
          "section": null,
          "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 35,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the compressor’s air inlet filter",
      "description": "Replace the compressor’s air inlet filter.",
      "instruction_text": "6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "6. Replace the compressor’s air inlet filter.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "6. Replace the compressor’s air inlet filter.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "The air inlet filter on the internal compressor is completely clogged.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [
    {
      "text": "For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 2

ID: `dbranch_0559d463b4dc0ee1dbfc8e0a94dbe9c81e23280335a2932643f7f81a18f028e3`. Pagine: [77].

- Faulty fan, solenoid valve, or power board → Faulty fan, solenoid valve, or power board → Replace power board, solenoid valve, or fan as indicated by test results

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If the solenoid valve test and the fan test both pass",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board."
        }
      ]
    },
    {
      "text": "If Test 4 fails",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan."
        }
      ]
    },
    {
      "text": "If Test 8 fails",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_68354036288761ccd22975fcda82aa0bd2b03879a80b116a8ae0e79b48471e8f",
  "branch_lineage_id": "dbranch_0559d463b4dc0ee1dbfc8e0a94dbe9c81e23280335a2932643f7f81a18f028e3",
  "record_window_id": "diagwin_3659468740cbcfd9c85bf398",
  "record_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
  "branch_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
  "indicators": [
    {
      "kind": "error_code",
      "code": "4",
      "name": "Faulty fan, solenoid valve, or power board",
      "description": "Number of blinks: 4. The problem is a faulty fan, solenoid valve, or power board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "4",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "4",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Faulty fan, solenoid valve, or power board",
    "description": "The fan, solenoid valve, or power board is faulty.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "source_page": 77,
        "quote": "Faulty fan, solenoid valve, or power board",
        "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace power board, solenoid valve, or fan as indicated by test results",
      "description": "Replace the power board if both tests pass; replace the solenoid valve if Test 4 fails; replace the fan if Test 8 fails.",
      "instruction_text": "If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If the solenoid valve test and the fan test both pass",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "If Test 4 fails",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "If Test 8 fails",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 3

ID: `dbranch_0ea78fc318cfb2b57c9523af4fa1062c17b22f5b982e9af08c2145f2468e5d80`. Pagine: [77].

- Faulty fan, solenoid valve, or power board → Power board faulty → Replace power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 4 – solenoid valve and Test 8 – fan.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The solenoid valve test and the fan test both pass.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_fb08899dd1d74a4275f741613cb2c63740d3c3c80aa06bccbddd07be798f2a52",
  "branch_lineage_id": "dbranch_0ea78fc318cfb2b57c9523af4fa1062c17b22f5b982e9af08c2145f2468e5d80",
  "record_window_id": "",
  "record_anchor": "ev_0c4635222e570b2e437ae45dd11e",
  "branch_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
  "indicators": [
    {
      "kind": "error_code",
      "code": "4",
      "name": "Faulty fan, solenoid valve, or power board",
      "description": "Four Error LED blinks indicate a faulty fan, solenoid valve, or power board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_0c4635222e570b2e437ae45dd11e",
          "source_page": 77,
          "quote": "Number of blinks | Problem | Solution",
          "evidence_id": "ev_0c4635222e570b2e437ae45dd11e",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "Number of blinks | Problem | Solution",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 1,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "4 | Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Power board faulty",
    "description": "Both the solenoid valve test and fan test pass, but the table directs replacement of the power board.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "source_page": 77,
        "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
        "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace power board",
      "description": "Replace the power board if both component tests pass.",
      "instruction_text": "Perform Test 4 – solenoid valve and Test 8 – fan. If the solenoid valve test and the fan test both pass, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "replace the power board.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 4 – solenoid valve and Test 8 – fan.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95.",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The solenoid valve test and the fan test both pass.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass",
          "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "Power board",
    "description": "Board replaced if both the solenoid valve and fan tests pass.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "source_page": 77,
        "quote": "replace the power board",
        "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "source_page": 77,
        "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
        "evidence_id": "ev_f48195d5a388d3e9e8cc2e7819b8",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 4

ID: `dbranch_279702e89ecf58fae5b413ccec6680a4a7a608ed3fa3fffe1de2fd44a3382fa0`. Pagine: [91].

- Torch stuck closed → Nozzle and electrode contact or short-circuit in a torch lead wire; torch plunger does not move freely → Replace the torch body

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check whether the torch plunger moves freely in the torch head.",
      "claim_evidence": [
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?"
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The torch plunger does not move freely in the torch head.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
          "source_page": 91,
          "quote": "If no"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_a90f20a0a82d83f9a4b9edc0f538335489adf42a6b055796aae8d75bff991190",
  "branch_lineage_id": "dbranch_279702e89ecf58fae5b413ccec6680a4a7a608ed3fa3fffe1de2fd44a3382fa0",
  "record_window_id": "",
  "record_anchor": "ev_99fc8a78f1fca22a83b311926169",
  "branch_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Torch stuck closed",
      "description": "The nozzle and electrode remain in contact after the torch trigger is pulled; the test’s low resistance with gas flowing identifies the stuck-closed condition for follow-up.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_99fc8a78f1fca22a83b311926169",
          "source_page": 90,
          "quote": "the power supply detects a “torch stuck closed” fault.",
          "evidence_id": "ev_99fc8a78f1fca22a83b311926169",
          "locator": {
            "kind": "pdf",
            "page": 90,
            "section": null,
            "quote": "If the nozzle and electrode are not in contact before the torch trigger is pulled, the power supply detects a “torch stuck \nopen” fault. If the nozzle and electrode remain in contact after the torch trigger is pulled, the power supply detects a \n“torch stuck closed” fault.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 2,
            "source_block_index": 3,
            "bbox": [
              42.0,
              91.117,
              545.654,
              125.081
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a47305167f876ca6329572b168b0",
          "source_page": 91,
          "quote": "If the resistance reads as very low (closed circuit) with the gas flowing",
          "evidence_id": "ev_a47305167f876ca6329572b168b0",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 4,
            "bbox": [
              113.998,
              263.437,
              548.24,
              285.399
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_a47305167f876ca6329572b168b0",
          "source_page": 91,
          "quote": "the nozzle and electrode are in contact or a short-circuit occurred in one of the wires in the torch lead",
          "evidence_id": "ev_a47305167f876ca6329572b168b0",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 4,
            "bbox": [
              113.998,
              263.437,
              548.24,
              285.399
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Nozzle and electrode contact or short-circuit in a torch lead wire; torch plunger does not move freely",
    "description": "For the low-resistance, gas-flowing branch, if the torch plunger does not move freely, replace the torch body.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
        "source_page": 91,
        "quote": "If no, replace the torch body.",
        "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 10,
          "source_block_index": 8,
          "bbox": [
            78.0,
            353.364,
            397.932,
            363.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_a47305167f876ca6329572b168b0",
        "source_page": 91,
        "quote": "the nozzle and electrode are in contact or a short-circuit occurred in one of the wires in the torch lead",
        "evidence_id": "ev_a47305167f876ca6329572b168b0",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 6,
          "source_block_index": 4,
          "bbox": [
            113.998,
            263.437,
            548.24,
            285.399
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
        "source_page": 91,
        "quote": "Does the torch plunger move freely in the torch head?",
        "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "6. Does the torch plunger move freely in the torch head?",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 8,
          "source_block_index": 6,
          "bbox": [
            64.497,
            317.441,
            306.319,
            327.511
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the torch body",
      "description": "Replace the torch body when the torch plunger does not move freely.",
      "instruction_text": "If the torch plunger does not move freely in the torch head, replace the torch body.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
          "source_page": 91,
          "quote": "replace the torch body",
          "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 8,
            "bbox": [
              78.0,
              353.364,
              397.932,
              363.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
          "source_page": 91,
          "quote": "If no, replace the torch body.",
          "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 8,
            "bbox": [
              78.0,
              353.364,
              397.932,
              363.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?",
          "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "6. Does the torch plunger move freely in the torch head?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 6,
            "bbox": [
              64.497,
              317.441,
              306.319,
              327.511
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Check whether the torch plunger moves freely in the torch head.",
      "claim_evidence": [
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?",
          "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "6. Does the torch plunger move freely in the torch head?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 6,
            "bbox": [
              64.497,
              317.441,
              306.319,
              327.511
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The torch plunger does not move freely in the torch head.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
          "source_page": 91,
          "quote": "If no",
          "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 8,
            "bbox": [
              78.0,
              353.364,
              397.932,
              363.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "torch body",
    "description": "Torch body identified for replacement when the torch plunger does not move freely.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
        "source_page": 91,
        "quote": "replace the torch body",
        "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 10,
          "source_block_index": 8,
          "bbox": [
            78.0,
            353.364,
            397.932,
            363.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_15e76da4ba28a5deb6a0999db3cb",
        "source_page": 91,
        "quote": "If no, replace the torch body.",
        "evidence_id": "ev_15e76da4ba28a5deb6a0999db3cb",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf no, replace the torch body. See Replace the torch body on page 201.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 10,
          "source_block_index": 8,
          "bbox": [
            78.0,
            353.364,
            397.932,
            363.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 5

ID: `dbranch_29ce8aff4ea1ef19213cabc8ef5b6e4fc808fb18c4e0daac2f14d38447eca112`. Pagine: [91].

- Torch stuck closed → Nozzle and electrode contact or short-circuit in a torch lead wire; torch plunger moves freely → Replace the torch lead

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check whether the torch plunger moves freely in the torch head.",
      "claim_evidence": [
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?"
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The torch plunger moves freely in the torch head.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
          "source_page": 91,
          "quote": "If yes"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_a90f20a0a82d83f9a4b9edc0f538335489adf42a6b055796aae8d75bff991190",
  "branch_lineage_id": "dbranch_29ce8aff4ea1ef19213cabc8ef5b6e4fc808fb18c4e0daac2f14d38447eca112",
  "record_window_id": "",
  "record_anchor": "ev_99fc8a78f1fca22a83b311926169",
  "branch_anchor": "ev_62d938c8fbf31e5819077bda045b",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Torch stuck closed",
      "description": "The nozzle and electrode remain in contact after the torch trigger is pulled; the test’s low resistance with gas flowing identifies the stuck-closed condition for follow-up.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_99fc8a78f1fca22a83b311926169",
          "source_page": 90,
          "quote": "the power supply detects a “torch stuck closed” fault.",
          "evidence_id": "ev_99fc8a78f1fca22a83b311926169",
          "locator": {
            "kind": "pdf",
            "page": 90,
            "section": null,
            "quote": "If the nozzle and electrode are not in contact before the torch trigger is pulled, the power supply detects a “torch stuck \nopen” fault. If the nozzle and electrode remain in contact after the torch trigger is pulled, the power supply detects a \n“torch stuck closed” fault.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 2,
            "source_block_index": 3,
            "bbox": [
              42.0,
              91.117,
              545.654,
              125.081
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a47305167f876ca6329572b168b0",
          "source_page": 91,
          "quote": "If the resistance reads as very low (closed circuit) with the gas flowing",
          "evidence_id": "ev_a47305167f876ca6329572b168b0",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 4,
            "bbox": [
              113.998,
              263.437,
              548.24,
              285.399
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_a47305167f876ca6329572b168b0",
          "source_page": 91,
          "quote": "the nozzle and electrode are in contact or a short-circuit occurred in one of the wires in the torch lead",
          "evidence_id": "ev_a47305167f876ca6329572b168b0",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 4,
            "bbox": [
              113.998,
              263.437,
              548.24,
              285.399
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Nozzle and electrode contact or short-circuit in a torch lead wire; torch plunger moves freely",
    "description": "For the low-resistance, gas-flowing branch, if the torch plunger moves freely, replace the torch lead.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
        "source_page": 91,
        "quote": "If yes, replace the torch lead.",
        "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 7,
          "bbox": [
            78.0,
            335.364,
            396.288,
            345.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_a47305167f876ca6329572b168b0",
        "source_page": 91,
        "quote": "the nozzle and electrode are in contact or a short-circuit occurred in one of the wires in the torch lead",
        "evidence_id": "ev_a47305167f876ca6329572b168b0",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "If the resistance reads as very low (closed circuit) with the gas flowing, the nozzle and electrode are in \ncontact or a short-circuit occurred in one of the wires in the torch lead. Continue with step 6.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 6,
          "source_block_index": 4,
          "bbox": [
            113.998,
            263.437,
            548.24,
            285.399
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
        "source_page": 91,
        "quote": "Does the torch plunger move freely in the torch head?",
        "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "6. Does the torch plunger move freely in the torch head?",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 8,
          "source_block_index": 6,
          "bbox": [
            64.497,
            317.441,
            306.319,
            327.511
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the torch lead",
      "description": "Replace the torch lead when the torch plunger moves freely.",
      "instruction_text": "If the torch plunger moves freely in the torch head, replace the torch lead.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
          "source_page": 91,
          "quote": "replace the torch lead",
          "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 7,
            "bbox": [
              78.0,
              335.364,
              396.288,
              345.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
          "source_page": 91,
          "quote": "If yes, replace the torch lead.",
          "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 7,
            "bbox": [
              78.0,
              335.364,
              396.288,
              345.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?",
          "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "6. Does the torch plunger move freely in the torch head?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 6,
            "bbox": [
              64.497,
              317.441,
              306.319,
              327.511
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Check whether the torch plunger moves freely in the torch head.",
      "claim_evidence": [
        {
          "source_anchor": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "source_page": 91,
          "quote": "Does the torch plunger move freely in the torch head?",
          "evidence_id": "ev_dcd17bd57d4d65e8523f39e46b7a",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "6. Does the torch plunger move freely in the torch head?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 6,
            "bbox": [
              64.497,
              317.441,
              306.319,
              327.511
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The torch plunger moves freely in the torch head.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
          "source_page": 91,
          "quote": "If yes",
          "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
          "locator": {
            "kind": "pdf",
            "page": 91,
            "section": null,
            "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 7,
            "bbox": [
              78.0,
              335.364,
              396.288,
              345.397
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "torch lead",
    "description": "Torch lead identified for replacement when the torch plunger moves freely.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
        "source_page": 91,
        "quote": "replace the torch lead",
        "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 7,
          "bbox": [
            78.0,
            335.364,
            396.288,
            345.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_62d938c8fbf31e5819077bda045b",
        "source_page": 91,
        "quote": "If yes, replace the torch lead.",
        "evidence_id": "ev_62d938c8fbf31e5819077bda045b",
        "locator": {
          "kind": "pdf",
          "page": 91,
          "section": null,
          "quote": "\nIf yes, replace the torch lead. See Replace the torch lead on page 205.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 7,
          "bbox": [
            78.0,
            335.364,
            396.288,
            345.397
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 6

ID: `dbranch_3bb391429fbbec8fb4dc9955ccc45448c35c20a1c134e82a2064cdc21ea634a7`. Pagine: [97].

- Compressor does not run or air does not blow from the torch → Faulty internal compressor → Replace the internal compressor

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Connect the internal compressor to an external 12 VDC power source (for example, a car battery).",
      "claim_evidence": [
        {
          "source_anchor": "ev_b47f768a452bc97b3eb69ae5f37d",
          "source_page": 97,
          "quote": "Connect the internal compressor to an external 12 VDC power source (for example, a car battery)."
        }
      ]
    },
    {
      "instruction_text": "Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Check whether the compressor is running and air is blowing from the torch.",
      "claim_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger."
        },
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?"
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If no, replace the internal compressor.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?"
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_450bac09bbebef1e20a0e7f21c591bd170bded9dfd5a988637e17f3b72151f81",
  "branch_lineage_id": "dbranch_3bb391429fbbec8fb4dc9955ccc45448c35c20a1c134e82a2064cdc21ea634a7",
  "record_window_id": "",
  "record_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
  "branch_anchor": "ev_f21a03de65e8a3d53ae773388182",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Compressor does not run or air does not blow from the torch",
      "description": "During the external 12 VDC compressor test with the gas shut-off override button held down, the compressor is not running or air is not blowing from the torch.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Faulty internal compressor",
    "description": "The internal compressor fails the external 12 VDC test: the compressor is not running or air is not blowing from the torch.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
        "source_page": 97,
        "quote": "If no, replace the internal compressor.",
        "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
        "locator": {
          "kind": "pdf",
          "page": 97,
          "section": null,
          "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 21,
          "source_block_index": 13,
          "bbox": [
            82.472,
            649.927,
            570.083,
            672.24
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the internal compressor",
      "description": "Replace the internal compressor after a negative test result, then return the solenoid valve to its position between both clips from the center panel.",
      "instruction_text": "If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push the solenoid valve back into place between both clips from the center panel.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "Be sure to push the solenoid valve back into place between both clips from the center panel.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Connect the internal compressor to an external 12 VDC power source (for example, a car battery).",
      "claim_evidence": [
        {
          "source_anchor": "ev_b47f768a452bc97b3eb69ae5f37d",
          "source_page": 97,
          "quote": "Connect the internal compressor to an external 12 VDC power source (for example, a car battery).",
          "evidence_id": "ev_b47f768a452bc97b3eb69ae5f37d",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "12. Connect the internal compressor to an external 12 VDC power source (for example, a car battery).",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 18,
            "source_block_index": 10,
            "bbox": [
              60.281,
              578.218,
              494.026,
              588.288
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Check whether the compressor is running and air is blowing from the torch.",
      "claim_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger.",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If no, replace the internal compressor.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_87590a4f299bb3fd1eb3869883ef",
          "source_page": 97,
          "quote": "Is the compressor running, and is air blowing from the torch?",
          "evidence_id": "ev_87590a4f299bb3fd1eb3869883ef",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "13. Hold down the gas shut-off override button on top of the solenoid valve, then quickly tap the torch trigger. Is the \ncompressor running, and is air blowing from the torch?",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 19,
            "source_block_index": 11,
            "bbox": [
              60.281,
              602.221,
              552.927,
              624.183
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
          "source_page": 97,
          "quote": "If no, replace the internal compressor.",
          "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
          "locator": {
            "kind": "pdf",
            "page": 97,
            "section": null,
            "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 21,
            "source_block_index": 13,
            "bbox": [
              82.472,
              649.927,
              570.083,
              672.24
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "internal compressor",
    "description": "Internal compressor tested on an external 12 VDC source and replaced if it fails the test.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
        "source_page": 97,
        "quote": "replace the internal compressor.",
        "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
        "locator": {
          "kind": "pdf",
          "page": 97,
          "section": null,
          "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 21,
          "source_block_index": 13,
          "bbox": [
            82.472,
            649.927,
            570.083,
            672.24
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_f21a03de65e8a3d53ae773388182",
        "source_page": 97,
        "quote": "replace the internal compressor.",
        "evidence_id": "ev_f21a03de65e8a3d53ae773388182",
        "locator": {
          "kind": "pdf",
          "page": 97,
          "section": null,
          "quote": "b. If no, replace the internal compressor. See Replace the internal compressor on page 169. Be sure to push \nthe solenoid valve back into place between both clips from the center panel.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 21,
          "source_block_index": 13,
          "bbox": [
            82.472,
            649.927,
            570.083,
            672.24
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 7

ID: `dbranch_45cd1dfa9939539866eb58d1518630da9f002bd46a0caddca8c2d1f274324574`. Pagine: [67].

- Temperature LED blinks while the machine is powered ON → Excessive input current for too long → Allow the system to cool

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The fault most often occurs when operating on a 120 VAC input circuit with cutting current set above 20 A; operating on a 120 V / 15 A circuit; frequently stretching the arc while cutting on a 120 VAC input circuit; or using an extension cord that is too long. Maximum extension-cord length is 16 m (53 feet) on a 120 VAC input circuit and 40.5 m (133 feet) on a 240 VAC input circuit.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "This fault most often occurs when:"
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A."
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 V / 15 A circuit."
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting."
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet)."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_e53d88d0de78e444369ffa51767a4e3703cbcbf9f370f6cad7d74eeb6ef5274a",
  "branch_lineage_id": "dbranch_45cd1dfa9939539866eb58d1518630da9f002bd46a0caddca8c2d1f274324574",
  "record_window_id": "diagwin_be9291e25e5559fcce43ef32",
  "record_anchor": "ev_021c59f68c0f5b48976426813da8",
  "branch_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Temperature LED blinks while the machine is powered ON",
      "description": "The temperature LED blinks while the machine is powered ON.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_021c59f68c0f5b48976426813da8",
          "source_page": 67,
          "quote": "The temperature LED blinks while the machine is powered ON.",
          "evidence_id": "ev_021c59f68c0f5b48976426813da8",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "The temperature LED blinks while the machine is powered ON. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 1,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_021c59f68c0f5b48976426813da8",
          "source_page": 67,
          "quote": "The temperature LED blinks while the machine is powered ON.",
          "evidence_id": "ev_021c59f68c0f5b48976426813da8",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "The temperature LED blinks while the machine is powered ON. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 1,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Excessive input current for too long",
    "description": "The system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
        "source_page": 67,
        "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating.",
        "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
        "locator": {
          "kind": "pdf",
          "page": 67,
          "section": null,
          "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 33,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Allow the system to cool",
      "description": "Let the system cool before using it.",
      "instruction_text": "Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The fault most often occurs when operating on a 120 VAC input circuit with cutting current set above 20 A; operating on a 120 V / 15 A circuit; frequently stretching the arc while cutting on a 120 VAC input circuit; or using an extension cord that is too long. Maximum extension-cord length is 16 m (53 feet) on a 120 VAC input circuit and 40.5 m (133 feet) on a 240 VAC input circuit.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "This fault most often occurs when:",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 V / 15 A circuit.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_98cb10b3b6e3b82529cdf1603a65",
          "source_page": 67,
          "quote": "You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet).",
          "evidence_id": "ev_98cb10b3b6e3b82529cdf1603a65",
          "locator": {
            "kind": "pdf",
            "page": 67,
            "section": null,
            "quote": "This fault occurs when the system continuously draws too much input current for too long. The fault protects the power switch and power cord from damage caused by overheating. This fault most often occurs when:  You are operating the system on a 120 VAC input circuit and the cutting current is set above 20 A.  You are operating the system on a 120 V / 15 A circuit.  You are operating the system on a 120 VAC input circuit and are frequently stretching the arc while cutting.  You are using an extension cord that is too long. The maximum length for an extension cord on a 120 VAC input circuit is 16 m (53 feet). The maximum length for an extension cord on a 240 VAC input circuit is 40.5 m (133 feet). | Let the system cool for 3 minutes before using it. Leave the system on to allow the fan to cool the power supply. To prevent the fault from occurring:  Operate the system on a 240 VAC input circuit whenever possible.  Turn down the cutting current. See Step 3 – Adjust the output current on page 47.  If you do operate the system on a120 VAC input circuit, use a 20 A circuit and set the cutting current below 20 A.  Avoid stretching the arc. Drag the torch on the workpiece. See Edge start on a workpiece on page 54.  Operate the system without using an extension cord. If you must use an extension cord, use a heavy conductor cord of the shortest possible length. See Extension cord recommendations on page 33.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 33,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 8

ID: `dbranch_4b9d763ddc06c298979dab2340346809fc0b848d5cc332b6b84f94d84464df13`. Pagine: [88].

- Unequal step 7 and step 8 voltage values → Power board voltage balance out of specification → Replace the power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_bf112e5f21c0fc3da62415195df91bcc5761f13ccc9557b5efd126c976d6fb7e",
  "branch_lineage_id": "dbranch_4b9d763ddc06c298979dab2340346809fc0b848d5cc332b6b84f94d84464df13",
  "record_window_id": "",
  "record_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
  "branch_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Unequal step 7 and step 8 voltage values",
      "description": "The values found in step 7 and step 8 differ by more than 30 V.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
          "source_page": 88,
          "quote": "The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V",
          "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
          "locator": {
            "kind": "pdf",
            "page": 88,
            "section": null,
            "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              46.48,
              161.059,
              540.187,
              183.093
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
          "source_page": 88,
          "quote": "If they differ by more than 30 V, replace the power board.",
          "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
          "locator": {
            "kind": "pdf",
            "page": 88,
            "section": null,
            "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              46.48,
              161.059,
              540.187,
              183.093
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Power board voltage balance out of specification",
    "description": "The step 7 and step 8 voltage values differ by more than 30 V.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
        "source_page": 88,
        "quote": "If they differ by more than 30 V",
        "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
        "locator": {
          "kind": "pdf",
          "page": 88,
          "section": null,
          "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 6,
          "source_block_index": 7,
          "bbox": [
            46.48,
            161.059,
            540.187,
            183.093
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the power board",
      "description": "Replace the power board when the step 7 and step 8 values differ by more than 30 V.",
      "instruction_text": "If the values found in step 7 and step 8 differ by more than 30 V, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
          "source_page": 88,
          "quote": "If they differ by more than 30 V, replace the power board.",
          "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
          "locator": {
            "kind": "pdf",
            "page": 88,
            "section": null,
            "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              46.48,
              161.059,
              540.187,
              183.093
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
          "source_page": 88,
          "quote": "If they differ by more than 30 V, replace the power board.",
          "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
          "locator": {
            "kind": "pdf",
            "page": 88,
            "section": null,
            "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              46.48,
              161.059,
              540.187,
              183.093
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [],
  "affected_component": {
    "name": "power board",
    "description": "Power board identified as the component to replace for the voltage imbalance.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
        "source_page": 88,
        "quote": "replace the power board",
        "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
        "locator": {
          "kind": "pdf",
          "page": 88,
          "section": null,
          "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 6,
          "source_block_index": 7,
          "bbox": [
            46.48,
            161.059,
            540.187,
            183.093
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_92e730463ed0402f2cf2e53c58f1",
        "source_page": 88,
        "quote": "If they differ by more than 30 V, replace the power board.",
        "evidence_id": "ev_92e730463ed0402f2cf2e53c58f1",
        "locator": {
          "kind": "pdf",
          "page": 88,
          "section": null,
          "quote": "9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the \npower board.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 6,
          "source_block_index": 7,
          "bbox": [
            46.48,
            161.059,
            540.187,
            183.093
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 9

ID: `dbranch_4f7c6f61c7d9e946c8d9404923e9819130dba7519075782e4f604178213c9add`. Pagine: [71].

- Arc goes out during cutting or intermittently will not fire → Poor work lead connection → Reposition work lead
- Arc goes out during cutting or intermittently will not fire → Poor work lead connection → Clean cutting surface
- Arc goes out during cutting or intermittently will not fire → Poor work lead connection → Repair work lead connection if necessary

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_c0e1a01447173f54f134cb12a56e9c293b3c50ad09650689cc692a7aaecfa499",
  "branch_lineage_id": "dbranch_4f7c6f61c7d9e946c8d9404923e9819130dba7519075782e4f604178213c9add",
  "record_window_id": "diagwin_ed089becc44a9e16948bbe84",
  "record_anchor": "ev_725f1905aac98639afe4f36bca25",
  "branch_anchor": "ev_725f1905aac98639afe4f36bca25",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Arc goes out during cutting or intermittently will not fire",
      "description": "The arc goes out during cutting or intermittently will not fire.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The arc goes out during cutting or intermittently will not fire.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The arc goes out during cutting or intermittently will not fire.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Poor work lead connection",
    "description": "The work lead may be damaged or not properly connected to the workpiece.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_725f1905aac98639afe4f36bca25",
        "source_page": 71,
        "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
        "evidence_id": "ev_725f1905aac98639afe4f36bca25",
        "locator": {
          "kind": "pdf",
          "page": 71,
          "section": null,
          "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 40,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Repair work lead connection if necessary",
      "description": "Inspect for loose connections at the ground clamp and power supply, and repair if necessary.",
      "instruction_text": "Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary.",
      "action_kind": "repair",
      "claim_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "name": "Reposition work lead",
      "description": "Reposition the work lead on the workpiece.",
      "instruction_text": "Reposition the work lead on the workpiece.",
      "action_kind": "adjustment",
      "claim_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Reposition the work lead on the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Reposition the work lead on the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "name": "Clean cutting surface",
      "description": "Clean the cutting surface to make a better connection with the work lead.",
      "instruction_text": "Clean the cutting surface to make a better connection with the work lead.",
      "action_kind": "cleaning",
      "claim_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Clean the cutting surface to make a better connection with the work lead.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "Clean the cutting surface to make a better connection with the work lead.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_725f1905aac98639afe4f36bca25",
          "source_page": 71,
          "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
          "evidence_id": "ev_725f1905aac98639afe4f36bca25",
          "locator": {
            "kind": "pdf",
            "page": 71,
            "section": null,
            "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 40,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [],
  "affected_component": {
    "name": "Work lead",
    "description": "The work lead may be damaged or not properly connected to the workpiece.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_725f1905aac98639afe4f36bca25",
        "source_page": 71,
        "quote": "The work lead may be damaged or not properly connected to the workpiece.",
        "evidence_id": "ev_725f1905aac98639afe4f36bca25",
        "locator": {
          "kind": "pdf",
          "page": 71,
          "section": null,
          "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 40,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_725f1905aac98639afe4f36bca25",
        "source_page": 71,
        "quote": "The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece.",
        "evidence_id": "ev_725f1905aac98639afe4f36bca25",
        "locator": {
          "kind": "pdf",
          "page": 71,
          "section": null,
          "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 40,
          "row_index": 3,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_725f1905aac98639afe4f36bca25",
        "source_page": 71,
        "quote": "The work lead may be damaged or not properly connected to the workpiece.",
        "evidence_id": "ev_725f1905aac98639afe4f36bca25",
        "locator": {
          "kind": "pdf",
          "page": 71,
          "section": null,
          "quote": "The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 40,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 10

ID: `dbranch_79816025152c69b36fe6fa3c20482f506171f440f75182f4bec44da2d8e8f6a3`. Pagine: [77].

- Faulty power board or control board → Faulty power board or control board → Replace power board or control board as indicated by test results

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board on page 86.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board on page 86."
        }
      ]
    },
    {
      "instruction_text": "Perform Test 2 – power board voltage checks on page 84.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Perform Test 2 – power board voltage checks on page 84."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If any of the values are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board."
        }
      ]
    },
    {
      "text": "If any of the values for pins 5, 7, or 12 are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again."
        }
      ]
    },
    {
      "text": "If the values are correct",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board."
        }
      ]
    },
    {
      "text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_5885f59cdab73bb2989221a5f15cd4599aa458ee99f39f25e7175e21abf14689",
  "branch_lineage_id": "dbranch_79816025152c69b36fe6fa3c20482f506171f440f75182f4bec44da2d8e8f6a3",
  "record_window_id": "diagwin_5da0a69fcdb848697f6b347a",
  "record_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
  "branch_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
  "indicators": [
    {
      "kind": "error_code",
      "code": "3",
      "name": "Faulty power board or control board",
      "description": "Number of blinks: 3. The problem is a faulty power board or control board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "3",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "3",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Faulty power board or control board",
    "description": "The power board or control board is faulty.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
        "source_page": 77,
        "quote": "Faulty power board or control board",
        "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 2,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace power board or control board as indicated by test results",
      "description": "Replace the power board or control board according to the specified test outcomes.",
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board on page 86.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board on page 86.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Perform Test 2 – power board voltage checks on page 84.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Perform Test 2 – power board voltage checks on page 84.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If any of the values are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "If any of the values for pins 5, 7, or 12 are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "If the values are correct",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 11

ID: `dbranch_7a8129c80e21de80b161fca651e5cf2ad095ebd7612ae92aad13d4695f897b93`. Pagine: [94].

- Cap-sensor switch circuit fault → Cap-sensor switch faulty or torch lead has a broken wire → Replace the faulty part

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The torch parts mentioned in step 7 and step 8 are working properly.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_ca72c36699c15636c89170e0acaf5cb2a117cb0a1db1d7616872bec87eafa155",
  "branch_lineage_id": "dbranch_7a8129c80e21de80b161fca651e5cf2ad095ebd7612ae92aad13d4695f897b93",
  "record_window_id": "",
  "record_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
  "branch_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Cap-sensor switch circuit fault",
      "description": "With the torch parts in steps 7 and 8 working properly, the cap-sensor switch is faulty or the torch lead has a broken wire.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly, the cap-sensor switch is faulty or the torch lead has a broken wire.",
          "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 14,
            "source_block_index": 13,
            "bbox": [
              46.49,
              588.585,
              282.073,
              658.626
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Make sure the consumables are correctly installed.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_b0ace9f0b83dcc265b75377fc3b4",
          "source_page": 94,
          "quote": "Make sure the torch plunger moves smoothly.",
          "evidence_id": "ev_b0ace9f0b83dcc265b75377fc3b4",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "7. Make sure the torch plunger moves smoothly. If it \ndoes not, replace the torch body. See Replace the \ntorch body on page 201.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 11,
            "bbox": [
              47.635,
              504.645,
              275.907,
              538.608
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly, the cap-sensor switch is faulty or the torch lead has a broken wire.",
          "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 14,
            "source_block_index": 13,
            "bbox": [
              46.49,
              588.585,
              282.073,
              658.626
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Cap-sensor switch faulty or torch lead has a broken wire",
    "description": "The cap-sensor switch is faulty or the torch lead has a broken wire, provided the torch plunger and consumables are working properly.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
        "source_page": 94,
        "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire.",
        "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
        "locator": {
          "kind": "pdf",
          "page": 94,
          "section": null,
          "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 14,
          "source_block_index": 13,
          "bbox": [
            46.49,
            588.585,
            282.073,
            658.626
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the faulty part",
      "description": "Replace the faulty cap-sensor switch or torch lead.",
      "instruction_text": "Replace the faulty part. See Replace the cap-sensor switch on page 204 or Replace the torch lead and strain relief on page 153.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "Replace the faulty part.",
          "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 14,
            "source_block_index": 13,
            "bbox": [
              46.49,
              588.585,
              282.073,
              658.626
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire. Replace the faulty part.",
          "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 14,
            "source_block_index": 13,
            "bbox": [
              46.49,
              588.585,
              282.073,
              658.626
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The torch parts mentioned in step 7 and step 8 are working properly.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_d2c9a2d42b1a901ad1d262e765be",
          "source_page": 94,
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly",
          "evidence_id": "ev_d2c9a2d42b1a901ad1d262e765be",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "9. If the torch parts mentioned in step 7 and step 8 are \nworking properly, the cap-sensor switch is faulty or \nthe torch lead has a broken wire. Replace the faulty \npart. See Replace the cap-sensor switch on \npage 204 or Replace the torch lead and strain relief \non page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 14,
            "source_block_index": 13,
            "bbox": [
              46.49,
              588.585,
              282.073,
              658.626
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 12

ID: `dbranch_8be7c3b622de137381f1edacacbec93eff999f8359a4df6f388c79da640c40ee`. Pagine: [94].

- Consumables incorrectly installed → Consumables incorrectly installed → Adjust the consumables

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Make sure the consumables are correctly installed.",
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Make sure the consumables are correctly installed."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "Adjust the consumables if necessary.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "if necessary"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_d0d38140ba5d9d082c63fc4b772026c3053a609d98c4153c1fb5dc95710cf6cf",
  "branch_lineage_id": "dbranch_8be7c3b622de137381f1edacacbec93eff999f8359a4df6f388c79da640c40ee",
  "record_window_id": "",
  "record_anchor": "ev_832e1777815a1a52791ced6e75ea",
  "branch_anchor": "ev_832e1777815a1a52791ced6e75ea",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Consumables incorrectly installed",
      "description": "The consumables are not correctly installed.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Make sure the consumables are correctly installed. Adjust the consumables if necessary.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Make sure the consumables are correctly installed. Adjust the consumables if necessary.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Consumables incorrectly installed",
    "description": "The consumables are not correctly installed.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
        "source_page": 94,
        "quote": "Make sure the consumables are correctly installed.",
        "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
        "locator": {
          "kind": "pdf",
          "page": 94,
          "section": null,
          "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 12,
          "bbox": [
            46.49,
            552.652,
            277.24,
            574.614
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Adjust the consumables",
      "description": "Adjust the consumables if necessary to ensure correct installation.",
      "instruction_text": "Adjust the consumables if necessary.",
      "action_kind": "adjustment",
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Adjust the consumables if necessary.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Adjust the consumables if necessary.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Make sure the consumables are correctly installed.",
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "Make sure the consumables are correctly installed.",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "Adjust the consumables if necessary.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
          "source_page": 94,
          "quote": "if necessary",
          "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
          "locator": {
            "kind": "pdf",
            "page": 94,
            "section": null,
            "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 12,
            "bbox": [
              46.49,
              552.652,
              277.24,
              574.614
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "consumables",
    "description": "Torch consumables.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
        "source_page": 94,
        "quote": "the consumables are correctly installed.",
        "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
        "locator": {
          "kind": "pdf",
          "page": 94,
          "section": null,
          "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 12,
          "bbox": [
            46.49,
            552.652,
            277.24,
            574.614
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_832e1777815a1a52791ced6e75ea",
        "source_page": 94,
        "quote": "Adjust the consumables if necessary.",
        "evidence_id": "ev_832e1777815a1a52791ced6e75ea",
        "locator": {
          "kind": "pdf",
          "page": 94,
          "section": null,
          "quote": "8. Make sure the consumables are correctly installed. \nAdjust the consumables if necessary.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 12,
          "bbox": [
            46.49,
            552.652,
            277.24,
            574.614
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 13

ID: `dbranch_a32246165ff84c6717af412f85f2419c48fbed3ac9e9a9ccc9048133265676ab`. Pagine: [77].

- Faulty power board or control board → Power board faulty → Replace power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 2 – power board voltage checks.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Test 2 – power board voltage checks on page 84"
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "Pins 5, 7, or 12 have correct values, but any other Test 2 values are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_f0fc16abc0a145e64a8ec2c7b13c7cdc376bd420521007676b4bfb6b8ca0c256",
  "branch_lineage_id": "dbranch_a32246165ff84c6717af412f85f2419c48fbed3ac9e9a9ccc9048133265676ab",
  "record_window_id": "diagwin_5da0a69fcdb848697f6b347a",
  "record_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
  "branch_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
  "indicators": [
    {
      "kind": "error_code",
      "code": "3",
      "name": "Faulty power board or control board",
      "description": "Three Error LED blinks indicate a faulty power board or control board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "3 | Faulty power board or control board",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "3 | Faulty power board or control board",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Power board faulty",
    "description": "Pins 5, 7, or 12 are correct in Test 2, but one or more other Test 2 values are incorrect.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
        "source_page": 77,
        "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
        "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 2,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace power board",
      "description": "Replace the power board if the specified pins are correct but any other Test 2 values are incorrect.",
      "instruction_text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks but any other values from Test 2 are incorrect, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "replace the power board.",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 2 – power board voltage checks.",
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "Test 2 – power board voltage checks on page 84",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "Pins 5, 7, or 12 have correct values, but any other Test 2 values are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
          "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 2,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": {
    "name": "Power board",
    "description": "Power board tested in Test 2 and replaced for incorrect other test values.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
        "source_page": 77,
        "quote": "replace the power board",
        "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 2,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
        "source_page": 77,
        "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
        "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 2,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_ea66fbc46f45f38a715f5208c40f",
        "source_page": 77,
        "quote": "replace the power board",
        "evidence_id": "ev_ea66fbc46f45f38a715f5208c40f",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 2,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 14

ID: `dbranch_c1d31e9963fb04745cf5911ad5c3ba07bf19ccb1ca2705a9e7112a677376f0f2`. Pagine: [69].

- Internal compressor LED and temperature LED illuminate → Internal compressor air inlet filter completely clogged → Replace the compressor’s air inlet filter

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_7c4836b614e4b3aad94395b22379ddaaff48c1da5388b6d291a598843d365269",
  "branch_lineage_id": "dbranch_c1d31e9963fb04745cf5911ad5c3ba07bf19ccb1ca2705a9e7112a677376f0f2",
  "record_window_id": "diagwin_801ada29217e8fba589c7ff1",
  "record_anchor": "ev_4e090bb09612002cb933451d4a14",
  "branch_anchor": "ev_72ec954354dc034de91d5d68ac77",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Internal compressor LED and temperature LED illuminate",
      "description": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_4e090bb09612002cb933451d4a14",
          "source_page": 69,
          "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
          "evidence_id": "ev_4e090bb09612002cb933451d4a14",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 1,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_4e090bb09612002cb933451d4a14",
          "source_page": 69,
          "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.",
          "evidence_id": "ev_4e090bb09612002cb933451d4a14",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": "The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled. |",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 1,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Internal compressor air inlet filter completely clogged",
    "description": "The filter is blocked so that no air can flow through it.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
        "source_page": 69,
        "quote": "The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
        "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
        "locator": {
          "kind": "pdf",
          "page": 69,
          "section": null,
          "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 35,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the compressor’s air inlet filter",
      "description": "Replace the compressor’s air inlet filter.",
      "instruction_text": "Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "Replace the compressor’s air inlet filter.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "Replace the compressor’s air inlet filter.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
          "source_page": 69,
          "quote": "The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
          "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
          "locator": {
            "kind": "pdf",
            "page": 69,
            "section": null,
            "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 35,
            "row_index": 3,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [],
  "affected_component": {
    "name": "Compressor’s air inlet filter",
    "description": "Air inlet filter on the internal compressor.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
        "source_page": 69,
        "quote": "The air inlet filter on the internal compressor is completely clogged.",
        "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
        "locator": {
          "kind": "pdf",
          "page": 69,
          "section": null,
          "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 35,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
        "source_page": 69,
        "quote": "The air inlet filter on the internal compressor is completely clogged.",
        "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
        "locator": {
          "kind": "pdf",
          "page": 69,
          "section": null,
          "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 35,
          "row_index": 3,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_72ec954354dc034de91d5d68ac77",
        "source_page": 69,
        "quote": "The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it.",
        "evidence_id": "ev_72ec954354dc034de91d5d68ac77",
        "locator": {
          "kind": "pdf",
          "page": 69,
          "section": null,
          "quote": " The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 35,
          "row_index": 3,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```

## Ramo 15

ID: `dbranch_c5aee8a8c1a5e2e787ec26199cceeca8614adfc9d9bc11f93988ddfaf152ba94`. Pagine: [77].

- Inverter saturation → Inverter saturation → Install new consumables in the torch
- Inverter saturation → Inverter saturation → Replace the power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If you continue to see this error code",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_caec0f7cb72d837d41af321ca308242e37953ec354490337063776d6c83a4454",
  "branch_lineage_id": "dbranch_c5aee8a8c1a5e2e787ec26199cceeca8614adfc9d9bc11f93988ddfaf152ba94",
  "record_window_id": "diagwin_a319f078824047540dfd744a",
  "record_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
  "branch_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
  "indicators": [
    {
      "kind": "error_code",
      "code": "6",
      "name": "Inverter saturation",
      "description": "Inverter saturation",
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Inverter saturation",
    "description": "Inverter saturation",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
        "source_page": 77,
        "quote": "Inverter saturation",
        "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 4,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Install new consumables in the torch",
      "description": "Install new consumables in the torch.",
      "instruction_text": "Install new consumables in the torch.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "name": "Replace the power board",
      "description": "Replace the power board.",
      "instruction_text": "If you continue to see this error code, replace the power board.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If you continue to see this error code",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 16

ID: `dbranch_cedda5a2cfbd18114690d9e9645c2ea1bb33efcbcde858b12fd922b585953977`. Pagine: [77].

- Inverter saturation → Inverter saturation → Install new consumables in the torch

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If the error code continues after installing new consumables in the torch, replace the power board.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_c0c4f7f57a8495a7971861c7e3e112cbf4173e130709b226b1979c8693fa92f3",
  "branch_lineage_id": "dbranch_cedda5a2cfbd18114690d9e9645c2ea1bb33efcbcde858b12fd922b585953977",
  "record_window_id": "",
  "record_anchor": "ev_0c4635222e570b2e437ae45dd11e",
  "branch_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
  "indicators": [
    {
      "kind": "error_code",
      "code": "6",
      "name": "Inverter saturation",
      "description": "Six Error LED blinks indicate inverter saturation.",
      "claim_evidence": [
        {
          "source_anchor": "ev_0c4635222e570b2e437ae45dd11e",
          "source_page": 77,
          "quote": "Number of blinks | Problem | Solution",
          "evidence_id": "ev_0c4635222e570b2e437ae45dd11e",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "Number of blinks | Problem | Solution",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 1,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "6 | Inverter saturation",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "6 | Inverter saturation",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Inverter saturation",
    "description": "The inverter is saturated.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
        "source_page": 77,
        "quote": "6 | Inverter saturation",
        "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
        "locator": {
          "kind": "pdf",
          "page": 77,
          "section": null,
          "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
          "extraction_method": "table",
          "printed_page": null,
          "block_index": null,
          "source_block_index": null,
          "bbox": null,
          "table_index": 44,
          "row_index": 4,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Install new consumables in the torch",
      "description": "Install new torch consumables; replace the power board if the error continues.",
      "instruction_text": "Install new consumables in the torch. If you continue to see this error code, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "Install new consumables in the torch. If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If the error code continues after installing new consumables in the torch, replace the power board.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_82e55906d6d6ecf4aec3b82bfcb7",
          "locator": {
            "kind": "pdf",
            "page": 77,
            "section": null,
            "quote": "6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.",
            "extraction_method": "table",
            "printed_page": null,
            "block_index": null,
            "source_block_index": null,
            "bbox": null,
            "table_index": 44,
            "row_index": 4,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "affected_component": null,
  "resolution_status": "action_stated"
}
```

## Ramo 17

ID: `dbranch_ff4bf68b07eb0cc88705339741d3dd1bf5a791b07d3c877bfefd2e7fe6080f4a`. Pagine: [95].

- Fan does not operate → Fan does not operate → Replace the fan

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Test the fan (M1) for proper operation.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f97e9cde5b3eb5012c86caa461de",
          "source_page": 95,
          "quote": "Test the fan (M1) for proper operation."
        }
      ]
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_aa5796b1c20ce2b0df6f5aace30a46c7fd90dedef34bb722861d7737bdbde859",
  "branch_lineage_id": "dbranch_ff4bf68b07eb0cc88705339741d3dd1bf5a791b07d3c877bfefd2e7fe6080f4a",
  "record_window_id": "",
  "record_anchor": "ev_f97e9cde5b3eb5012c86caa461de",
  "branch_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Fan does not operate",
      "description": "The fan does not operate during the fan test.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
          "source_page": 95,
          "quote": "If the fan does not operate, replace the fan.",
          "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
          "locator": {
            "kind": "pdf",
            "page": 95,
            "section": null,
            "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 9,
            "bbox": [
              64.472,
              391.428,
              409.64,
              401.571
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
          "source_page": 95,
          "quote": "If the fan does not operate, replace the fan.",
          "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
          "locator": {
            "kind": "pdf",
            "page": 95,
            "section": null,
            "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 9,
            "bbox": [
              64.472,
              391.428,
              409.64,
              401.571
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "failure": {
    "name": "Fan does not operate",
    "description": "The fan does not operate during the test.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
        "source_page": 95,
        "quote": "If the fan does not operate",
        "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
        "locator": {
          "kind": "pdf",
          "page": 95,
          "section": null,
          "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 9,
          "bbox": [
            64.472,
            391.428,
            409.64,
            401.571
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "actions": [
    {
      "name": "Replace the fan",
      "description": "Replace the fan if it does not operate.",
      "instruction_text": "If the fan does not operate, replace the fan. See Replace the fan on page 164.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
          "source_page": 95,
          "quote": "replace the fan.",
          "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
          "locator": {
            "kind": "pdf",
            "page": 95,
            "section": null,
            "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 9,
            "bbox": [
              64.472,
              391.428,
              409.64,
              401.571
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
          "source_page": 95,
          "quote": "If the fan does not operate, replace the fan.",
          "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
          "locator": {
            "kind": "pdf",
            "page": 95,
            "section": null,
            "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 9,
            "bbox": [
              64.472,
              391.428,
              409.64,
              401.571
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "inspection_steps": [
    {
      "instruction_text": "Test the fan (M1) for proper operation.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f97e9cde5b3eb5012c86caa461de",
          "source_page": 95,
          "quote": "Test the fan (M1) for proper operation.",
          "evidence_id": "ev_f97e9cde5b3eb5012c86caa461de",
          "locator": {
            "kind": "pdf",
            "page": 95,
            "section": null,
            "quote": "Test the fan (M1) for proper operation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 2,
            "source_block_index": 3,
            "bbox": [
              60.0,
              91.117,
              221.734,
              101.077
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    }
  ],
  "conditions": [],
  "affected_component": {
    "name": "fan (M1)",
    "description": "Fan tested for proper operation.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f97e9cde5b3eb5012c86caa461de",
        "source_page": 95,
        "quote": "fan (M1)",
        "evidence_id": "ev_f97e9cde5b3eb5012c86caa461de",
        "locator": {
          "kind": "pdf",
          "page": 95,
          "section": null,
          "quote": "Test the fan (M1) for proper operation.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 2,
          "source_block_index": 3,
          "bbox": [
            60.0,
            91.117,
            221.734,
            101.077
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_778e40c1b8cadeceefd1bfbc9621",
        "source_page": 95,
        "quote": "replace the fan.",
        "evidence_id": "ev_778e40c1b8cadeceefd1bfbc9621",
        "locator": {
          "kind": "pdf",
          "page": 95,
          "section": null,
          "quote": "6. If the fan does not operate, replace the fan. See Replace the fan on page 164.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 9,
          "bbox": [
            64.472,
            391.428,
            409.64,
            401.571
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ]
  },
  "resolution_status": "action_stated"
}
```
