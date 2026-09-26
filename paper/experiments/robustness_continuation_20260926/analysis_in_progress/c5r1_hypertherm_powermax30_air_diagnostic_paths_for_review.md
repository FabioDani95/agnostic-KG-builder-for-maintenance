# Catene estratte da verificare

Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.

## Ramo 1

ID: `dbranch_0ae136c59c1ba8d0f1411aec6286c7529d2e681eefa1bdeb1779331fbc4d80f2`. Pagine: [77].

- Inverter saturation → Inverter saturation → Replace the power board
- Inverter saturation → Inverter saturation → Install new consumables in the torch

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The error code continues to appear after installing new torch consumables.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
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
  "record_lineage_id": "drec_8c3647862d411ed9cf74f829936c590e1e5dbbeb151d9670afc37df8f10962ea",
  "branch_lineage_id": "dbranch_0ae136c59c1ba8d0f1411aec6286c7529d2e681eefa1bdeb1779331fbc4d80f2",
  "record_window_id": "diagwin_a636065e7d8fdbeb029f934f",
  "record_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
  "branch_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
  "indicators": [
    {
      "kind": "error_code",
      "code": "6",
      "name": "Inverter saturation",
      "description": "Six Error LED blinks indicate inverter saturation.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
    "description": "Inverter saturation.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
        "source_page": 77,
        "quote": "Inverter saturation",
        "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
      "description": "Replace the power board if the error code continues after installing new torch consumables.",
      "instruction_text": "If you continue to see this error code, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
      "text": "The error code continues to appear after installing new torch consumables.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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

## Ramo 2

ID: `dbranch_29bbbc1225dc4c39dee8940dee7f65609166169ba9bd1a1004e468de882907c2`. Pagine: [94].

- Cap-sensor switch or torch lead fault → Faulty cap-sensor switch or broken wire in torch lead → Replace the faulty part

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
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
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
  "record_lineage_id": "drec_76fcf4e2826b599f8bd1157d39c03f3bb1f351d1997e07c4251467bc9e048b4c",
  "branch_lineage_id": "dbranch_29bbbc1225dc4c39dee8940dee7f65609166169ba9bd1a1004e468de882907c2",
  "record_window_id": "",
  "record_anchor": "ev_a66038063274758a45dcf8ab4a2b",
  "branch_anchor": "ev_a66038063274758a45dcf8ab4a2b",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Cap-sensor switch or torch lead fault",
      "description": "When the torch parts checked in steps 7 and 8 are working properly, the cap-sensor switch is faulty or the torch lead has a broken wire.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
          "source_page": 94,
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire",
          "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
          "source_page": 94,
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire",
          "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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
    "name": "Faulty cap-sensor switch or broken wire in torch lead",
    "description": "The cap-sensor switch is faulty or the torch lead has a broken wire.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
        "source_page": 94,
        "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire",
        "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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
      "instruction_text": "If the torch parts mentioned in step 7 and step 8 are working properly, the cap-sensor switch is faulty or the torch lead has a broken wire. Replace the faulty part.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
          "source_page": 94,
          "quote": "Replace the faulty part.",
          "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
          "source_page": 94,
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire. Replace the faulty part.",
          "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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
          "source_anchor": "ev_a66038063274758a45dcf8ab4a2b",
          "source_page": 94,
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly",
          "evidence_id": "ev_a66038063274758a45dcf8ab4a2b",
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

## Ramo 3

ID: `dbranch_336853fe382ea1a5dad8e816df5582568860dfbe7491f78cc3727a0379bac6c2`. Pagine: [77].

- Faulty power board or control board → Faulty power board or control board → Replace the power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If any of the values are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect"
        }
      ]
    },
    {
      "text": "If any of the values for pins 5, 7, or 12 are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values for pins 5, 7, or 12 are incorrect"
        }
      ]
    },
    {
      "text": "If the values are correct.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct"
        }
      ]
    },
    {
      "text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
  "record_lineage_id": "drec_51ac47a8c6cd84b019c179f81eadbf37b2e82b8e6a50a14abe405768cd26939a",
  "branch_lineage_id": "dbranch_336853fe382ea1a5dad8e816df5582568860dfbe7491f78cc3727a0379bac6c2",
  "record_window_id": "diagwin_685b6bad58403ed74f4d412b",
  "record_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
  "branch_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
  "indicators": [
    {
      "kind": "error_code",
      "code": "3",
      "name": "Faulty power board or control board",
      "description": "3 blinks: faulty power board or control board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "3",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "3",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
    "description": "Faulty power board or control board.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
        "source_page": 77,
        "quote": "Faulty power board or control board",
        "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "name": "Replace the power board",
      "description": "Replace the power board if any values from Test 3 are incorrect, or if pins 5, 7, or 12 are correct in Test 2 but any other Test 2 values are incorrect.",
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If any of the values are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "If any of the values for pins 5, 7, or 12 are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values for pins 5, 7, or 12 are incorrect",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "If the values are correct.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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

## Ramo 4

ID: `dbranch_464ac0535d5f46ef4bb8c9b236d16a8e81422c40fec963210a6113205214544a`. Pagine: [77].

- Faulty fan, solenoid valve, or power board → Faulty fan, solenoid valve, or power board → Replace the solenoid valve
- Faulty fan, solenoid valve, or power board → Faulty fan, solenoid valve, or power board → Replace the power board
- Faulty fan, solenoid valve, or power board → Faulty fan, solenoid valve, or power board → Replace the fan

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 4 – solenoid valve and Test 8 – fan.",
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass"
        }
      ]
    },
    {
      "text": "Test 4 fails.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If Test 4 fails"
        }
      ]
    },
    {
      "text": "Test 8 fails.",
      "applies_to": "action",
      "step_index": 2,
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "if Test 8 fails"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_22488f10ca4c7923caf225a22c49797d421f455476e64c62e5b4ab2d78e18d40",
  "branch_lineage_id": "dbranch_464ac0535d5f46ef4bb8c9b236d16a8e81422c40fec963210a6113205214544a",
  "record_window_id": "diagwin_d73d6da44416cb630474ff38",
  "record_anchor": "ev_48710dfeda680d5df46b372d1bea",
  "branch_anchor": "ev_48710dfeda680d5df46b372d1bea",
  "indicators": [
    {
      "kind": "error_code",
      "code": "4",
      "name": "Faulty fan, solenoid valve, or power board",
      "description": "Four Error LED blinks indicate a faulty fan, solenoid valve, or power board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "4 | Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "4 | Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
        "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
        "source_page": 77,
        "quote": "Faulty fan, solenoid valve, or power board",
        "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
      "name": "Replace the power board",
      "description": "Replace the power board if both the solenoid valve and fan tests pass.",
      "instruction_text": "Perform Test 4 – solenoid valve and Test 8 – fan. If the solenoid valve test and the fan test both pass, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass, replace the power board.",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
      "name": "Replace the solenoid valve",
      "description": "Replace the solenoid valve if Test 4 fails.",
      "instruction_text": "If Test 4 fails, replace the solenoid valve.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If Test 4 fails, replace the solenoid valve",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
      "name": "Replace the fan",
      "description": "Replace the fan if Test 8 fails.",
      "instruction_text": "If Test 8 fails, replace the fan.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "if Test 8 fails, replace the fan.",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "Faulty fan, solenoid valve, or power board",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "if Test 8 fails, replace the fan.",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95.",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If the solenoid valve test and the fan test both pass",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
      "text": "Test 4 fails.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "If Test 4 fails",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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
      "text": "Test 8 fails.",
      "applies_to": "action",
      "step_index": 2,
      "claim_evidence": [
        {
          "source_anchor": "ev_48710dfeda680d5df46b372d1bea",
          "source_page": 77,
          "quote": "if Test 8 fails",
          "evidence_id": "ev_48710dfeda680d5df46b372d1bea",
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

## Ramo 5

ID: `dbranch_4f0c4f1323fb95fd275eec3668fd073d09f817b28bd6171c278d44224f8c4dd3`. Pagine: [77].

- Inverter saturation → Inverter saturation → Install new consumables in the torch
- Inverter saturation → Inverter saturation → Replace the power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "If you continue to see this error code.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
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
  "record_lineage_id": "drec_ae48ae1505de78f2fe24056a120bd09b3dc602a0cf4889dba062820e5841ecf3",
  "branch_lineage_id": "dbranch_4f0c4f1323fb95fd275eec3668fd073d09f817b28bd6171c278d44224f8c4dd3",
  "record_window_id": "diagwin_a636065e7d8fdbeb029f934f",
  "record_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
  "branch_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
  "indicators": [
    {
      "kind": "error_code",
      "code": "6",
      "name": "Inverter saturation",
      "description": "6 blinks: inverter saturation.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "6",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
    "description": "Inverter saturation.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
        "source_page": 77,
        "quote": "Inverter saturation",
        "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Install new consumables in the torch.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
      "description": "Replace the power board if the error code continues after installing new consumables.",
      "instruction_text": "If you continue to see this error code, replace the power board.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code, replace the power board.",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "Inverter saturation",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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
      "text": "If you continue to see this error code.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a34ab66a7242316df2deb6e5fb39",
          "source_page": 77,
          "quote": "If you continue to see this error code",
          "evidence_id": "ev_a34ab66a7242316df2deb6e5fb39",
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

## Ramo 6

ID: `dbranch_6cd288526bb05e5546bcfbe011b6e78e00376d1e00c48946152547921cf7e0d9`. Pagine: [88].

- Voltage values differ by more than 30 V → Voltage imbalance → Replace the power board

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
  "record_lineage_id": "drec_69253acb858bdf32cb6444285f699e4c3d16feb9da5582826c9a6fe407d7bb81",
  "branch_lineage_id": "dbranch_6cd288526bb05e5546bcfbe011b6e78e00376d1e00c48946152547921cf7e0d9",
  "record_window_id": "",
  "record_anchor": "ev_b121f34244b1e7e0313d81bb918b",
  "branch_anchor": "ev_b121f34244b1e7e0313d81bb918b",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Voltage values differ by more than 30 V",
      "description": "The values found in step 7 and step 8 differ by more than 30 V.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
          "source_page": 88,
          "quote": "If they differ by more than 30 V",
          "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
          "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
          "source_page": 88,
          "quote": "If they differ by more than 30 V, replace the power board.",
          "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
    "name": "Voltage imbalance",
    "description": "The values found in step 7 and step 8 differ by more than 30 V.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
        "source_page": 88,
        "quote": "The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V",
        "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
      "instruction_text": "If they differ by more than 30 V, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
          "source_page": 88,
          "quote": "replace the power board",
          "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
          "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
          "source_page": 88,
          "quote": "If they differ by more than 30 V, replace the power board.",
          "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
    "description": "Power board identified for replacement when the voltage values differ by more than 30 V.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
        "source_page": 88,
        "quote": "replace the power board",
        "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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
        "source_anchor": "ev_b121f34244b1e7e0313d81bb918b",
        "source_page": 88,
        "quote": "If they differ by more than 30 V, replace the power board.",
        "evidence_id": "ev_b121f34244b1e7e0313d81bb918b",
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

## Ramo 7

ID: `dbranch_bdf76611f0da9b9dbe39a096e0feb77003959ea99222ed3a8e917f54c25d88ff`. Pagine: [48].

- Internal compressor LED illuminated or blinking → Fault condition → Correct the fault condition
- Power ON LED blinking → Fault condition → Correct the fault condition
- Temperature LED illuminated or blinking → Fault condition → Correct the fault condition
- Torch cap sensor LED illuminated or blinking → Fault condition → Correct the fault condition

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "Correct the fault condition before continuing.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "before continuing"
        }
      ]
    },
    {
      "text": "See Troubleshooting guide on page 65 for more information.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "See Troubleshooting guide on page 65"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_839935b6ef68b9d23a03283c0baa427cfe78183cadece7996c0f979f961db0ea",
  "branch_lineage_id": "dbranch_bdf76611f0da9b9dbe39a096e0feb77003959ea99222ed3a8e917f54c25d88ff",
  "record_window_id": "",
  "record_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
  "branch_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Internal compressor LED illuminated or blinking",
      "description": "The internal compressor LED illuminates or blinks.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "internal compressor LEDs illuminate or blink",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "this indicates a fault",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "kind": "symptom",
      "name": "Temperature LED illuminated or blinking",
      "description": "The temperature LED illuminates or blinks.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "temperature",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "this indicates a fault",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "kind": "symptom",
      "name": "Power ON LED blinking",
      "description": "The power ON LED blinks.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "the power ON LED blinks",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "this indicates a fault",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "kind": "symptom",
      "name": "Torch cap sensor LED illuminated or blinking",
      "description": "The torch cap sensor LED illuminates or blinks.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "torch cap sensor",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "this indicates a fault",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
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
    "name": "Fault condition",
    "description": "A fault condition is indicated by the temperature, torch cap sensor, or internal compressor LEDs illuminating or blinking, or by the power ON LED blinking.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
        "source_page": 48,
        "quote": "this indicates a fault",
        "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
        "locator": {
          "kind": "pdf",
          "page": 48,
          "section": null,
          "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 11,
          "bbox": [
            42.0,
            648.224,
            254.845,
            718.193
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
      "name": "Correct the fault condition",
      "description": "Correct the fault condition before continuing.",
      "instruction_text": "Correct the fault condition before continuing.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "Correct the fault condition before continuing.",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "Correct the fault condition",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
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
      "text": "Correct the fault condition before continuing.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "before continuing",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "See Troubleshooting guide on page 65 for more information.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "source_page": 48,
          "quote": "See Troubleshooting guide on page 65",
          "evidence_id": "ev_f9279ee7d1f2dabdf38a970bd52c",
          "locator": {
            "kind": "pdf",
            "page": 48,
            "section": null,
            "quote": "If the temperature, torch cap sensor, or internal \ncompressor LEDs illuminate or blink, or if the \npower ON LED blinks, this indicates a fault. \nCorrect the fault condition before continuing. See \nTroubleshooting guide on page 65 for more \ninformation.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 11,
            "bbox": [
              42.0,
              648.224,
              254.845,
              718.193
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

## Ramo 8

ID: `dbranch_d2ac15ce4a2b47b6b80945ec6dca6792fa4e700d2ddf44845d09a6924649ee5b`. Pagine: [77].

- Faulty power board or control board → Faulty power board or control board → Replace the control board
- Faulty power board or control board → Faulty power board or control board → Replace the power board
- Faulty power board or control board → Faulty power board or control board → Replace the power board

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board"
        }
      ]
    },
    {
      "instruction_text": "Perform Test 2 – power board voltage checks. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "Any Test 3 value is incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect"
        }
      ]
    },
    {
      "text": "The pins 5, 7, or 12 values are correct after removing the control board and testing again.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board."
        }
      ]
    },
    {
      "text": "Pins 5, 7, or 12 values are correct in Test 2, but any other Test 2 values are incorrect.",
      "applies_to": "action",
      "step_index": 2,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
  "record_lineage_id": "drec_756c9db711290c087710a0d16b641e74af69201677dc3b423f11985a83f1f27e",
  "branch_lineage_id": "dbranch_d2ac15ce4a2b47b6b80945ec6dca6792fa4e700d2ddf44845d09a6924649ee5b",
  "record_window_id": "diagwin_685b6bad58403ed74f4d412b",
  "record_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
  "branch_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
  "indicators": [
    {
      "kind": "error_code",
      "code": "3",
      "name": "Faulty power board or control board",
      "description": "Three Error LED blinks indicate a faulty power board or control board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "3 | Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "3 | Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
        "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
        "source_page": 77,
        "quote": "Faulty power board or control board",
        "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "name": "Replace the power board",
      "description": "Replace the power board when Test 3 values are incorrect.",
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board. If any of the values are incorrect, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "name": "Replace the control board",
      "description": "Replace the control board if pins 5, 7, or 12 have correct values after removing the control board.",
      "instruction_text": "Perform Test 2 – power board voltage checks. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "name": "Replace the power board",
      "description": "Replace the power board if pins 5, 7, and 12 are correct but other Test 2 values are incorrect.",
      "instruction_text": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks but any other values from Test 2 are incorrect, replace the power board.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Faulty power board or control board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "but any other values from Test 2 are incorrect, replace the power board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "instruction_text": "Perform Test 3 – VBUS and voltage balance on power board.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 3 – VBUS and voltage balance on power board",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "instruction_text": "Perform Test 2 – power board voltage checks. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "Any Test 3 value is incorrect.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If any of the values are incorrect",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "The pins 5, 7, or 12 values are correct after removing the control board and testing again.",
      "applies_to": "action",
      "step_index": 1,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values are correct, replace the control board.",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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
      "text": "Pins 5, 7, or 12 values are correct in Test 2, but any other Test 2 values are incorrect.",
      "applies_to": "action",
      "step_index": 2,
      "claim_evidence": [
        {
          "source_anchor": "ev_a54b0cbfd52b6135b02ac2242bf5",
          "source_page": 77,
          "quote": "If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect",
          "evidence_id": "ev_a54b0cbfd52b6135b02ac2242bf5",
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

## Ramo 9

ID: `dbranch_ef72115f47407714dadf0661182b4fb6af9e1993d7727fa57c8c6e0449619464`. Pagine: [89].

- Solenoid valve does not click → Faulty solenoid valve → Replace the solenoid valve

Ispezioni e condizioni:

```json
{
  "inspection_steps": [],
  "conditions": [
    {
      "text": "The voltage check reads 24 VDC.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "the voltage check reads 24 VDC"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_c884f48fb943f4c4c4224f7b3a995bb89262f1349b0df86ebba1d3cd0e0e8d61",
  "branch_lineage_id": "dbranch_ef72115f47407714dadf0661182b4fb6af9e1993d7727fa57c8c6e0449619464",
  "record_window_id": "",
  "record_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
  "branch_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Solenoid valve does not click",
      "description": "The valve does not click when the power is turned ON, while the voltage check reads 24 VDC.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_00bde3652fe91c95aa45ac11408b",
          "source_page": 89,
          "quote": "The valve should click.",
          "evidence_id": "ev_00bde3652fe91c95aa45ac11408b",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "6. Turn the power ON (I). The valve should click.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 10,
            "bbox": [
              64.5,
              556.545,
              270.973,
              566.967
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "If you do not hear the valve click",
          "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 16,
            "source_block_index": 13,
            "bbox": [
              64.5,
              628.835,
              566.734,
              650.87
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve.",
          "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 16,
            "source_block_index": 13,
            "bbox": [
              64.5,
              628.835,
              566.734,
              650.87
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
    "name": "Faulty solenoid valve",
    "description": "The valve does not click even though the voltage check reads 24 VDC.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
        "source_page": 89,
        "quote": "If you do not hear the valve click and the voltage check reads 24 VDC",
        "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
        "locator": {
          "kind": "pdf",
          "page": 89,
          "section": null,
          "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 16,
          "source_block_index": 13,
          "bbox": [
            64.5,
            628.835,
            566.734,
            650.87
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
      "name": "Replace the solenoid valve",
      "description": "Replace the solenoid valve.",
      "instruction_text": "If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "replace the solenoid valve",
          "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 16,
            "source_block_index": 13,
            "bbox": [
              64.5,
              628.835,
              566.734,
              650.87
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve.",
          "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 16,
            "source_block_index": 13,
            "bbox": [
              64.5,
              628.835,
              566.734,
              650.87
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
      "text": "The voltage check reads 24 VDC.",
      "applies_to": "branch",
      "step_index": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
          "source_page": 89,
          "quote": "the voltage check reads 24 VDC",
          "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
          "locator": {
            "kind": "pdf",
            "page": 89,
            "section": null,
            "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 16,
            "source_block_index": 13,
            "bbox": [
              64.5,
              628.835,
              566.734,
              650.87
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
    "name": "solenoid valve",
    "description": "Solenoid valve (V1), identified for replacement when it does not click and the voltage check reads 24 VDC.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_aeddb97b9e564cee591b7f2bc1ad",
        "source_page": 89,
        "quote": "solenoid valve (V1)",
        "evidence_id": "ev_aeddb97b9e564cee591b7f2bc1ad",
        "locator": {
          "kind": "pdf",
          "page": 89,
          "section": null,
          "quote": "This test verifies the proper operation of the solenoid valve (V1).",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 2,
          "source_block_index": 3,
          "bbox": [
            60.0,
            91.117,
            329.943,
            101.077
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
        "source_page": 89,
        "quote": "replace the solenoid valve",
        "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
        "locator": {
          "kind": "pdf",
          "page": 89,
          "section": null,
          "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 16,
          "source_block_index": 13,
          "bbox": [
            64.5,
            628.835,
            566.734,
            650.87
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_d53f1092ea46e44e29d6d64e0822",
        "source_page": 89,
        "quote": "replace the solenoid valve",
        "evidence_id": "ev_d53f1092ea46e44e29d6d64e0822",
        "locator": {
          "kind": "pdf",
          "page": 89,
          "section": null,
          "quote": "9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the \nsolenoid valve on page 151.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 16,
          "source_block_index": 13,
          "bbox": [
            64.5,
            628.835,
            566.734,
            650.87
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

## Ramo 10

ID: `dbranch_fa2ff2cd7c393fc003b30a8ef4a3036d9de70b3e61bfb795d1f1c714afec9af2`. Pagine: [103].

- Low air pressure → Faulty internal air compressor → Install a new air compressor

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Perform a test cut to sustain a plasma arc for several seconds and check the gauge pressure; it should read 2.9–3.4 bar (42–50 psi). Pressure will be lower during postflow.",
      "claim_evidence": [
        {
          "source_anchor": "ev_608550d14b87d64add2bb2a6ce20",
          "source_page": 103,
          "quote": "It should read 2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)"
        }
      ]
    },
    {
      "instruction_text": "With the compressor running, disregard the highest and lowest points of the gauge needle swings and check that the average pressure remains within the specified range.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f901a46be794ba1911570f53765e",
          "source_page": 103,
          "quote": "Make sure that, on average, the pressure remains within the range specified above."
        }
      ]
    },
    {
      "instruction_text": "Repeat the previous step 2–3 times to check that the pressure readings are consistent.",
      "claim_evidence": [
        {
          "source_anchor": "ev_cda01378c7068d1e40f9af01b5cf",
          "source_page": 103,
          "quote": "Repeat the previous step 2–3 times to make sure the pressure readings are consistent."
        }
      ]
    },
    {
      "instruction_text": "If air pressure was low, check that the air compressor has proper voltage (15 V).",
      "claim_evidence": [
        {
          "source_anchor": "ev_080b352d8cd37379b12f6556c017",
          "source_page": 103,
          "quote": "If the air pressure was low, check the air compressor for proper voltage (15 V)."
        }
      ]
    },
    {
      "instruction_text": "Apply leak detector solution to check for leaks at the six push-to-connect fittings between the air compressor and torch lead gas supply fitting, the two gas hoses connected to each side of the solenoid valve, the filter bowl-to-air-filter assembly connection, and the drain hose-to-filter bowl connection. Quickly tap the torch trigger to force gas flow without firing an arc.",
      "claim_evidence": [
        {
          "source_anchor": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "source_page": 103,
          "quote": "Quickly tap the torch trigger to force gas flow without firing an arc."
        },
        {
          "source_anchor": "ev_fe8116c31cc0743710a1ba8dd9e0",
          "source_page": 103,
          "quote": "The 6 push-to-connect fittings between the air compressor and the torch lead gas supply fitting"
        },
        {
          "source_anchor": "ev_5a7bfa0e6f0cb825507d4ca5018f",
          "source_page": 103,
          "quote": "The 2 gas hoses that connect to each side of the solenoid valve"
        },
        {
          "source_anchor": "ev_d36992c4fc7b0d09f3ccca81bfab",
          "source_page": 103,
          "quote": "Where the filter bowl screws into the air filter assembly"
        },
        {
          "source_anchor": "ev_4da1fb217a4f1224f42e6348b860",
          "source_page": 103,
          "quote": "Where the drain hose connects to the bottom of the filter bowl"
        }
      ]
    },
    {
      "instruction_text": "Disconnect the fan from J5 on the power board before the leak test to avoid the fan causing the appearance of a leak; reconnect the fan before using the system.",
      "claim_evidence": [
        {
          "source_anchor": "ev_7b4ffc7328c73368ad50d96e5633",
          "source_page": 103,
          "quote": "disconnect the fan from J5 on the power board before performing the leak test above. Make sure to reconnect the fan before using the system."
        }
      ]
    },
    {
      "instruction_text": "Check for leaks where the drain hose connects to the base of the power supply by tilting the power supply so you can feel whether air is escaping through the hole in the base where the drain hose exits.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a200c676ac3c665802fc7deb6b4a",
          "source_page": 103,
          "quote": "Tilt the power supply so that you can feel if air is escaping through the hole in the base where the drain hose lets out."
        }
      ]
    },
    {
      "instruction_text": "Install a different torch to see if the low pressure issue persists.",
      "claim_evidence": [
        {
          "source_anchor": "ev_3ac16b8463e741a62c34ba6d66f1",
          "source_page": 103,
          "quote": "Install a different torch to see if the low pressure issue persists."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "The stated gauge pressure range is 2.9–3.4 bar (42–50 psi); pressure is lower during postflow.",
      "applies_to": "inspection",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_608550d14b87d64add2bb2a6ce20",
          "source_page": 103,
          "quote": "2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)"
        }
      ]
    },
    {
      "text": "Check compressor voltage if air pressure was low; the proper voltage is 15 V.",
      "applies_to": "inspection",
      "step_index": 3,
      "claim_evidence": [
        {
          "source_anchor": "ev_080b352d8cd37379b12f6556c017",
          "source_page": 103,
          "quote": "If the air pressure was low, check the air compressor for proper voltage (15 V)."
        }
      ]
    },
    {
      "text": "Quickly tap the torch trigger to force gas flow without firing an arc during the leak check.",
      "applies_to": "inspection",
      "step_index": 4,
      "claim_evidence": [
        {
          "source_anchor": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "source_page": 103,
          "quote": "Quickly tap the torch trigger to force gas flow without firing an arc."
        }
      ]
    },
    {
      "text": "Disconnect the fan from J5 before the leak test and reconnect it before using the system.",
      "applies_to": "inspection",
      "step_index": 5,
      "claim_evidence": [
        {
          "source_anchor": "ev_7b4ffc7328c73368ad50d96e5633",
          "source_page": 103,
          "quote": "disconnect the fan from J5 on the power board before performing the leak test above. Make sure to reconnect the fan before using the system."
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_eac96babdef082a16bc74cb56714fac21b4986783117897140c9681cae224906",
  "branch_lineage_id": "dbranch_fa2ff2cd7c393fc003b30a8ef4a3036d9de70b3e61bfb795d1f1c714afec9af2",
  "record_window_id": "",
  "record_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
  "branch_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Low air pressure",
      "description": "Low pressure persists after completing the checks.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
          "source_page": 103,
          "quote": "If low pressure persists",
          "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 18,
            "source_block_index": 18,
            "bbox": [
              60.009,
              507.469,
              570.253,
              529.431
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
          "source_page": 103,
          "quote": "If low pressure persists after you complete all of these checks, the internal air compressor may be faulty.",
          "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 18,
            "source_block_index": 18,
            "bbox": [
              60.009,
              507.469,
              570.253,
              529.431
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
    "name": "Faulty internal air compressor",
    "description": "The internal air compressor may be faulty if low pressure persists after completing the checks.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
        "source_page": 103,
        "quote": "the internal air compressor may be faulty",
        "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
        "locator": {
          "kind": "pdf",
          "page": 103,
          "section": null,
          "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 18,
          "source_block_index": 18,
          "bbox": [
            60.009,
            507.469,
            570.253,
            529.431
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
      "name": "Install a new air compressor",
      "description": "Replace the internal air compressor.",
      "instruction_text": "Install a new air compressor.",
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
          "source_page": 103,
          "quote": "Install a new air compressor.",
          "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 18,
            "source_block_index": 18,
            "bbox": [
              60.009,
              507.469,
              570.253,
              529.431
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
          "source_page": 103,
          "quote": "the internal air compressor may be faulty. Install a new air compressor.",
          "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 18,
            "source_block_index": 18,
            "bbox": [
              60.009,
              507.469,
              570.253,
              529.431
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
      "instruction_text": "Perform a test cut to sustain a plasma arc for several seconds and check the gauge pressure; it should read 2.9–3.4 bar (42–50 psi). Pressure will be lower during postflow.",
      "claim_evidence": [
        {
          "source_anchor": "ev_608550d14b87d64add2bb2a6ce20",
          "source_page": 103,
          "quote": "It should read 2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)",
          "evidence_id": "ev_608550d14b87d64add2bb2a6ce20",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "11. Perform a test cut in order to sustain a plasma arc for several seconds. Check the pressure reading on the gauge. It \nshould read 2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 1,
            "source_block_index": 2,
            "bbox": [
              60.72,
              65.137,
              569.451,
              87.099
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "With the compressor running, disregard the highest and lowest points of the gauge needle swings and check that the average pressure remains within the specified range.",
      "claim_evidence": [
        {
          "source_anchor": "ev_f901a46be794ba1911570f53765e",
          "source_page": 103,
          "quote": "Make sure that, on average, the pressure remains within the range specified above.",
          "evidence_id": "ev_f901a46be794ba1911570f53765e",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "With the compressor running, the needle on the gauge vibrates a lot. Ignore the highest and lowest points on the \nneedle “swings.” Make sure that, on average, the pressure remains within the range specified above.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 2,
            "source_block_index": 3,
            "bbox": [
              78.001,
              95.137,
              557.819,
              117.098
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Repeat the previous step 2–3 times to check that the pressure readings are consistent.",
      "claim_evidence": [
        {
          "source_anchor": "ev_cda01378c7068d1e40f9af01b5cf",
          "source_page": 103,
          "quote": "Repeat the previous step 2–3 times to make sure the pressure readings are consistent.",
          "evidence_id": "ev_cda01378c7068d1e40f9af01b5cf",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "12. Repeat the previous step 2–3 times to make sure the pressure readings are consistent.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 3,
            "source_block_index": 4,
            "bbox": [
              60.302,
              131.142,
              447.418,
              141.212
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "If air pressure was low, check that the air compressor has proper voltage (15 V).",
      "claim_evidence": [
        {
          "source_anchor": "ev_080b352d8cd37379b12f6556c017",
          "source_page": 103,
          "quote": "If the air pressure was low, check the air compressor for proper voltage (15 V).",
          "evidence_id": "ev_080b352d8cd37379b12f6556c017",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "16. If the air pressure was low, check the air compressor for proper voltage (15 V). See Test 9a – Check the diagnostic \nLED (D5) on the compressor-driver board on page 96.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              60.302,
              227.084,
              568.781,
              249.118
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Apply leak detector solution to check for leaks at the six push-to-connect fittings between the air compressor and torch lead gas supply fitting, the two gas hoses connected to each side of the solenoid valve, the filter bowl-to-air-filter assembly connection, and the drain hose-to-filter bowl connection. Quickly tap the torch trigger to force gas flow without firing an arc.",
      "claim_evidence": [
        {
          "source_anchor": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "source_page": 103,
          "quote": "Quickly tap the torch trigger to force gas flow without firing an arc.",
          "evidence_id": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "17.  Apply leak detector solution (for example, Snoop®) to check for leaks at the following points on the gas supply line. \nQuickly tap the torch trigger to force gas flow without firing an arc. See Figure 23 on page 104.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 9,
            "bbox": [
              61.308,
              263.137,
              568.081,
              285.099
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_4da1fb217a4f1224f42e6348b860",
          "source_page": 103,
          "quote": "Where the drain hose connects to the bottom of the filter bowl",
          "evidence_id": "ev_4da1fb217a4f1224f42e6348b860",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nWhere the drain hose connects to the bottom of the filter bowl",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              96.0,
              347.137,
              378.109,
              357.097
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_5a7bfa0e6f0cb825507d4ca5018f",
          "source_page": 103,
          "quote": "The 2 gas hoses that connect to each side of the solenoid valve",
          "evidence_id": "ev_5a7bfa0e6f0cb825507d4ca5018f",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nThe 2 gas hoses that connect to each side of the solenoid valve",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              96.0,
              311.137,
              383.873,
              321.097
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_d36992c4fc7b0d09f3ccca81bfab",
          "source_page": 103,
          "quote": "Where the filter bowl screws into the air filter assembly",
          "evidence_id": "ev_d36992c4fc7b0d09f3ccca81bfab",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nWhere the filter bowl screws into the air filter assembly",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              96.0,
              329.137,
              346.008,
              339.097
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_fe8116c31cc0743710a1ba8dd9e0",
          "source_page": 103,
          "quote": "The 6 push-to-connect fittings between the air compressor and the torch lead gas supply fitting",
          "evidence_id": "ev_fe8116c31cc0743710a1ba8dd9e0",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nThe 6 push-to-connect fittings between the air compressor and the torch lead gas supply fitting",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              96.0,
              293.137,
              518.526,
              303.097
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Disconnect the fan from J5 on the power board before the leak test to avoid the fan causing the appearance of a leak; reconnect the fan before using the system.",
      "claim_evidence": [
        {
          "source_anchor": "ev_7b4ffc7328c73368ad50d96e5633",
          "source_page": 103,
          "quote": "disconnect the fan from J5 on the power board before performing the leak test above. Make sure to reconnect the fan before using the system.",
          "evidence_id": "ev_7b4ffc7328c73368ad50d96e5633",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nThe fan may cause the appearance of a leak on some fittings even if there is not one. To \navoid this, disconnect the fan from J5 on the power board before performing the leak \ntest above. Make sure to reconnect the fan before using the system.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              108.0,
              369.154,
              504.049,
              405.101
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Check for leaks where the drain hose connects to the base of the power supply by tilting the power supply so you can feel whether air is escaping through the hole in the base where the drain hose exits.",
      "claim_evidence": [
        {
          "source_anchor": "ev_a200c676ac3c665802fc7deb6b4a",
          "source_page": 103,
          "quote": "Tilt the power supply so that you can feel if air is escaping through the hole in the base where the drain hose lets out.",
          "evidence_id": "ev_a200c676ac3c665802fc7deb6b4a",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "18. Also check for leaks where the drain hose connects to the base of the power supply\n. Tilt the power supply so that \nyou can feel if air is escaping through the hole in the base where the drain hose lets out.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 15,
            "source_block_index": 16,
            "bbox": [
              60.308,
              447.46,
              570.204,
              469.422
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Install a different torch to see if the low pressure issue persists.",
      "claim_evidence": [
        {
          "source_anchor": "ev_3ac16b8463e741a62c34ba6d66f1",
          "source_page": 103,
          "quote": "Install a different torch to see if the low pressure issue persists.",
          "evidence_id": "ev_3ac16b8463e741a62c34ba6d66f1",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "19. Install a different torch to see if the low pressure issue persists. See page 153.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 17,
            "source_block_index": 17,
            "bbox": [
              60.248,
              483.466,
              411.449,
              493.536
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
      "text": "The stated gauge pressure range is 2.9–3.4 bar (42–50 psi); pressure is lower during postflow.",
      "applies_to": "inspection",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_608550d14b87d64add2bb2a6ce20",
          "source_page": 103,
          "quote": "2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)",
          "evidence_id": "ev_608550d14b87d64add2bb2a6ce20",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "11. Perform a test cut in order to sustain a plasma arc for several seconds. Check the pressure reading on the gauge. It \nshould read 2.9 – 3.4 bar (42 – 50 psi). (The pressure will be lower during postflow.)",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 1,
            "source_block_index": 2,
            "bbox": [
              60.72,
              65.137,
              569.451,
              87.099
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "Check compressor voltage if air pressure was low; the proper voltage is 15 V.",
      "applies_to": "inspection",
      "step_index": 3,
      "claim_evidence": [
        {
          "source_anchor": "ev_080b352d8cd37379b12f6556c017",
          "source_page": 103,
          "quote": "If the air pressure was low, check the air compressor for proper voltage (15 V).",
          "evidence_id": "ev_080b352d8cd37379b12f6556c017",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "16. If the air pressure was low, check the air compressor for proper voltage (15 V). See Test 9a – Check the diagnostic \nLED (D5) on the compressor-driver board on page 96.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              60.302,
              227.084,
              568.781,
              249.118
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "Quickly tap the torch trigger to force gas flow without firing an arc during the leak check.",
      "applies_to": "inspection",
      "step_index": 4,
      "claim_evidence": [
        {
          "source_anchor": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "source_page": 103,
          "quote": "Quickly tap the torch trigger to force gas flow without firing an arc.",
          "evidence_id": "ev_3f2e1c347e4f14b31b0fdf8cc42b",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "17.  Apply leak detector solution (for example, Snoop®) to check for leaks at the following points on the gas supply line. \nQuickly tap the torch trigger to force gas flow without firing an arc. See Figure 23 on page 104.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 8,
            "source_block_index": 9,
            "bbox": [
              61.308,
              263.137,
              568.081,
              285.099
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "text": "Disconnect the fan from J5 before the leak test and reconnect it before using the system.",
      "applies_to": "inspection",
      "step_index": 5,
      "claim_evidence": [
        {
          "source_anchor": "ev_7b4ffc7328c73368ad50d96e5633",
          "source_page": 103,
          "quote": "disconnect the fan from J5 on the power board before performing the leak test above. Make sure to reconnect the fan before using the system.",
          "evidence_id": "ev_7b4ffc7328c73368ad50d96e5633",
          "locator": {
            "kind": "pdf",
            "page": 103,
            "section": null,
            "quote": "\nThe fan may cause the appearance of a leak on some fittings even if there is not one. To \navoid this, disconnect the fan from J5 on the power board before performing the leak \ntest above. Make sure to reconnect the fan before using the system.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              108.0,
              369.154,
              504.049,
              405.101
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
    "name": "Internal air compressor",
    "description": "Air compressor in the system.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
        "source_page": 103,
        "quote": "the internal air compressor may be faulty",
        "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
        "locator": {
          "kind": "pdf",
          "page": 103,
          "section": null,
          "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 18,
          "source_block_index": 18,
          "bbox": [
            60.009,
            507.469,
            570.253,
            529.431
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_f6aff4e1c283bd224b906725f3e5",
        "source_page": 103,
        "quote": "the internal air compressor may be faulty. Install a new air compressor.",
        "evidence_id": "ev_f6aff4e1c283bd224b906725f3e5",
        "locator": {
          "kind": "pdf",
          "page": 103,
          "section": null,
          "quote": "20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new \nair compressor. See page 169.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 18,
          "source_block_index": 18,
          "bbox": [
            60.009,
            507.469,
            570.253,
            529.431
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
