# Catene estratte da verificare

Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.

## Ramo 1

ID: `dbranch_064c7b8bdef4a33caeaaf76e2eeeb0c11657f85a23831122d97c64e2feddf093`. Pagine: [37].

- Machine stops during cut due to unintentional pause → Intermittent pause circuit → Adjust pause plunger activation pressure

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure."
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
  "record_lineage_id": "drec_fea8604ce2284a598be72124869f571343109d745107709c60a3d53575a3e513",
  "branch_lineage_id": "dbranch_064c7b8bdef4a33caeaaf76e2eeeb0c11657f85a23831122d97c64e2feddf093",
  "record_window_id": "diagwin_e89f8ba594d535722e2fd2aa",
  "record_anchor": "ev_647f782b777847a5a84c09b6c845",
  "branch_anchor": "ev_55efde98a140f0a312240bdf7090",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Machine stops during cut due to unintentional pause",
      "description": "The machine stops in the middle of a cut and displays “Machine Paused, Press Zero, Next or Abort” on the touch screen; pressing NEXT on the keypad lets it continue where it left off.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
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
    "name": "Intermittent pause circuit",
    "description": "Typically caused by an intermittent pause circuit, usually in the stop discs.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
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
      "name": "Adjust pause plunger activation pressure",
      "description": "Tighten the plunger to increase activation pressure and loosen it to decrease activation pressure.",
      "instruction_text": "Remove gantry side cover. Check the pause plunger. Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
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
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
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
    "name": "Stop discs",
    "description": "Stop discs in the pause circuit.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
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

## Ramo 2

ID: `dbranch_0679dd5928036cb94effe7fccb4a5fab0a1e8718625d98783754632f6b3f7601`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty focusing lens → Clean or replace focusing lens

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the focusing lens."
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
  "record_lineage_id": "drec_e2020f616c2e546bf8db9b061b4eed41308c62c97ab38cb54a6e7d5b1a08ba97",
  "branch_lineage_id": "dbranch_0679dd5928036cb94effe7fccb4a5fab0a1e8718625d98783754632f6b3f7601",
  "record_window_id": "diagwin_23584feab16f4a15ab8563aa",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases, causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
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
    "name": "Damaged or dirty focusing lens",
    "description": "The focusing lens is damaged or dirty.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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
      "name": "Clean or replace focusing lens",
      "description": "Clean or replace the lens as required.",
      "instruction_text": "Check for damage or dirt on the focusing lens. Clean or replace lens as required.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the focusing lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
    "name": "Focusing lens",
    "description": "Focusing lens checked for damage or dirt.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "focusing lens",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "focusing lens",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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

## Ramo 3

ID: `dbranch_1ed448f634b2454f9139ba5a693ecbce0e5a444c702e7854ef7e201ad7044d06`. Pagine: [37].

- Machine stops during cut due to unintentional pause → Intermittent pause circuit → Adjust the pause plunger activation pressure

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "1.Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure."
        }
      ]
    },
    {
      "instruction_text": "Remove gantry side cover. Check the pause plunger.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Remove gantry side cover. Check the pause plunger."
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
  "record_lineage_id": "drec_a8e74d2631fccd1fc2af8038bf5073604b297a7bde1978645423def734a0056d",
  "branch_lineage_id": "dbranch_1ed448f634b2454f9139ba5a693ecbce0e5a444c702e7854ef7e201ad7044d06",
  "record_window_id": "diagwin_e89f8ba594d535722e2fd2aa",
  "record_anchor": "ev_647f782b777847a5a84c09b6c845",
  "branch_anchor": "ev_55efde98a140f0a312240bdf7090",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Machine Stop during Cut Due to Unintentional pause",
      "description": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
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
    "name": "Intermittent pause circuit",
    "description": "Typically caused by an intermittent pause circuit, usually in thestop discs.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
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
      "name": "Adjust the pause plunger activation pressure",
      "description": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
      "instruction_text": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_647f782b777847a5a84c09b6c845",
          "source_page": 37,
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "evidence_id": "ev_647f782b777847a5a84c09b6c845",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 9,
            "source_block_index": 10,
            "bbox": [
              45.0,
              535.238,
              296.772,
              622.278
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
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "1.Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ]
    },
    {
      "instruction_text": "Remove gantry side cover. Check the pause plunger.",
      "claim_evidence": [
        {
          "source_anchor": "ev_55efde98a140f0a312240bdf7090",
          "source_page": 37,
          "quote": "Remove gantry side cover. Check the pause plunger.",
          "evidence_id": "ev_55efde98a140f0a312240bdf7090",
          "locator": {
            "kind": "pdf",
            "page": 37,
            "section": null,
            "quote": "Troubleshooting:\n1.Check stop disc activation. The stop discs should not\nactivate by a slight touch or vibration. They should activate\nonly when moved by minimum pressure. Remove gantry\nside cover. Check the pause plunger. Tighten the plunger\nto increase activation pressure and loosen to decrease\nactivation pressure.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              45.0,
              634.238,
              296.781,
              710.238
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
    "name": "stop discs",
    "description": "The intermittent pause circuit is usually in the stop discs.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_647f782b777847a5a84c09b6c845",
        "source_page": 37,
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "evidence_id": "ev_647f782b777847a5a84c09b6c845",
        "locator": {
          "kind": "pdf",
          "page": 37,
          "section": null,
          "quote": "Problem: Machine Stop during Cut Due to Uninten-\ntional pause\nDescription of Problem:\nThe machine stops in middle of cut and displays message\n“Machine Paused, Press Zero, Next or Abort” on Touch\nScreen.  When pressing NEXT on the keypad, the machine\nwill continue to cut where it left off.  This is typically caused\nby an intermittent pause circuit, usually in thestop discs.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 9,
          "source_block_index": 10,
          "bbox": [
            45.0,
            535.238,
            296.772,
            622.278
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

## Ramo 4

ID: `dbranch_2162357e6126adaf41af8274af96642ac4008d9617187fbdd7e43ff777e5fab8`. Pagine: [39].

- Loss of laser cutting power → Damage or debris in laser nozzle → Clean or replace laser nozzle

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage or debris in the laser nozzle.",
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Check for damage or debris in laser nozzle."
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
  "record_lineage_id": "drec_0b42654d3f4ebf6b55f4139cce7c0082e47d0d47dd406a2ba2811ee076c42ec5",
  "branch_lineage_id": "dbranch_2162357e6126adaf41af8274af96642ac4008d9617187fbdd7e43ff777e5fab8",
  "record_window_id": "diagwin_1037b2f350a605889c403eb5",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases, causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Damage or debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
    "name": "Damage or debris in laser nozzle",
    "description": "The laser nozzle is damaged or contains debris.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "Damage or debris in laser nozzle.",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
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
      "name": "Clean or replace laser nozzle",
      "description": "Clean or replace the laser nozzle as required.",
      "instruction_text": "Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Clean or replace laser nozzle as required.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Clean or replace laser nozzle as required.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Damage or debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
      "instruction_text": "Check for damage or debris in the laser nozzle.",
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Check for damage or debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
    "name": "Laser nozzle",
    "description": "Nozzle checked for damage or debris.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "laser nozzle",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "Damage or debris in laser nozzle.",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "laser nozzle",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
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

ID: `dbranch_336f91a3525961b7b152447448ddd9070f3b0af4b529ed49af00d76020d497ae`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty mirror → Clean or replace mirrors

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
      "claim_evidence": [
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors."
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
  "record_lineage_id": "drec_7d76de3cd170a4ebe812c65ad7457c112d6933b7881229c67d8a2fe7f035d53b",
  "branch_lineage_id": "dbranch_336f91a3525961b7b152447448ddd9070f3b0af4b529ed49af00d76020d497ae",
  "record_window_id": "diagwin_5acfc5d11d6b9dfe89b04edf",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Damaged or dirty Mirror.",
          "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              324.24,
              161.918,
              575.984,
              193.998
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
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
    "name": "Damaged or dirty mirror",
    "description": "A mirror is damaged or dirty.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
        "source_page": 39,
        "quote": "Damaged or dirty Mirror.",
        "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 13,
          "bbox": [
            324.24,
            161.918,
            575.984,
            193.998
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
      "name": "Clean or replace mirrors",
      "description": "Clean or replace mirrors as required.",
      "instruction_text": "Clean or replace mirrors as required.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Clean or replace mirrors as required.",
          "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              324.24,
              161.918,
              575.984,
              193.998
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Clean or replace mirrors as required.",
          "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              324.24,
              161.918,
              575.984,
              193.998
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Damaged or dirty Mirror.",
          "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              324.24,
              161.918,
              575.984,
              193.998
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
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
      "claim_evidence": [
        {
          "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
          "source_page": 39,
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
          "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 12,
            "source_block_index": 13,
            "bbox": [
              324.24,
              161.918,
              575.984,
              193.998
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
    "name": "beam deflecting mirrors",
    "description": "Mirrors checked for damage, burn mark or dirt; clean or replace as required.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
        "source_page": 39,
        "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
        "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 13,
          "bbox": [
            324.24,
            161.918,
            575.984,
            193.998
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
        "source_page": 39,
        "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
        "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 13,
          "bbox": [
            324.24,
            161.918,
            575.984,
            193.998
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_23bab1124d64ad42c0b9d4a19552",
        "source_page": 39,
        "quote": "Damaged or dirty Mirror.",
        "evidence_id": "ev_23bab1124d64ad42c0b9d4a19552",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "2. Damaged or dirty Mirror. Check for damage, burn mark or\ndirt on the beam deflecting mirrors. Clean or replace\nmirrors as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 12,
          "source_block_index": 13,
          "bbox": [
            324.24,
            161.918,
            575.984,
            193.998
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

ID: `dbranch_8b93167091acc5b52afe8c1bc6db3ed2f496263c76aa8eb175cb65f8528f740a`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty focusing lens → Clean or replace lens

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the focusing lens."
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
  "record_lineage_id": "drec_ce128e8c8c13c8444942ed2864c43936c1d2b0c73b1a2a51c0d8ea1bb180e58c",
  "branch_lineage_id": "dbranch_8b93167091acc5b52afe8c1bc6db3ed2f496263c76aa8eb175cb65f8528f740a",
  "record_window_id": "diagwin_23584feab16f4a15ab8563aa",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
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
    "name": "Damaged or dirty focusing lens",
    "description": "The focusing lens is damaged or dirty.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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
      "name": "Clean or replace lens",
      "description": "Clean or replace the focusing lens as required.",
      "instruction_text": "Clean or replace lens as required.",
      "action_kind": "cleaning_or_replacement",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the focusing lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
    "name": "focusing lens",
    "description": "Focusing lens checked for damage or dirt, then cleaned or replaced as required.",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "focusing lens",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "focusing lens",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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

ID: `dbranch_dc99071851c71cf4761bb0002f1f62fcb0d8caa3e1a05a90ae9b0d349cc73096`. Pagine: [39].

- Loss of laser cutting power → Damage or debris in laser nozzle → Clean or replace laser nozzle as required

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage or debris in laser nozzle.",
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Check for damage or"
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "debris in laser nozzle."
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
  "record_lineage_id": "drec_93af56e720d332f6ca4b0b53e6655e5386b65452b030e008e1960d83220c9105",
  "branch_lineage_id": "dbranch_dc99071851c71cf4761bb0002f1f62fcb0d8caa3e1a05a90ae9b0d349cc73096",
  "record_window_id": "diagwin_1037b2f350a605889c403eb5",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Damage or debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
    "name": "Damage or debris in laser nozzle",
    "description": "Damage or debris in laser nozzle.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "Damage or debris in laser nozzle.",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
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
      "name": "Clean or replace laser nozzle as required",
      "description": "Clean or replace laser nozzle as required.",
      "instruction_text": "Clean or replace laser nozzle as required.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Clean or replace laser nozzle as required.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Clean or replace laser nozzle as required.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Damage or debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
      "instruction_text": "Check for damage or debris in laser nozzle.",
      "claim_evidence": [
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "Check for damage or",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
          "source_page": 39,
          "quote": "debris in laser nozzle.",
          "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 13,
            "source_block_index": 14,
            "bbox": [
              324.24,
              205.958,
              576.0,
              237.918
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
    "name": "laser nozzle",
    "description": "laser nozzle",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "Damage or debris in laser nozzle.",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_de6e0457bbca62ff8d3858c645b1",
        "source_page": 39,
        "quote": "Damage or debris in laser nozzle.",
        "evidence_id": "ev_de6e0457bbca62ff8d3858c645b1",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "3. Damage or debris in laser nozzle. Check for damage or\ndebris in laser nozzle. Clean or replace laser nozzle as\nrequired.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 13,
          "source_block_index": 14,
          "bbox": [
            324.24,
            205.958,
            576.0,
            237.918
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

## Ramo 8

ID: `dbranch_ee466ba6236f657cb8facbc4e59903afe913c6de300cf191f481397806454b6e`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty lens → Clean or replace lens as required

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the"
        },
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "focusing lens."
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
  "record_lineage_id": "drec_bc49e1e5092c70a1504c030e4283cf7cad32807f82175368b47b9c974bcd6385",
  "branch_lineage_id": "dbranch_ee466ba6236f657cb8facbc4e59903afe913c6de300cf191f481397806454b6e",
  "record_window_id": "diagwin_23584feab16f4a15ab8563aa",
  "record_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
  "branch_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
  "indicators": [
    {
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "description": "The laser cutting power decreases causing non-cut edges.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "Problem: Loss of laser cutting power",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "source_page": 39,
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "evidence_id": "ev_a3a6e49bd52afba866c7b8d35ad3",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Problem: Loss of laser cutting power\nDescription of Problem:\nThe laser cutting power decreases causing non-cut edges.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 10,
            "source_block_index": 11,
            "bbox": [
              324.24,
              73.958,
              575.993,
              105.918
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
    "name": "Damaged or dirty lens",
    "description": "Damaged or dirty lens.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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
      "name": "Clean or replace lens as required",
      "description": "Clean or replace lens as required.",
      "instruction_text": "Clean or replace lens as required.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Clean or replace lens as required.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Damaged or dirty lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
      "instruction_text": "Check for damage or dirt on the focusing lens.",
      "claim_evidence": [
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "Check for damage or dirt on the",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "source_page": 39,
          "quote": "focusing lens.",
          "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
          "locator": {
            "kind": "pdf",
            "page": 39,
            "section": null,
            "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 11,
            "source_block_index": 12,
            "bbox": [
              324.24,
              117.998,
              576.008,
              149.958
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
    "name": "focusing lens",
    "description": "focusing lens",
    "category": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Check for damage or dirt on the focusing lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      }
    ],
    "affects_link_evidence": [
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Check for damage or dirt on the focusing lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "source_page": 39,
        "quote": "Damaged or dirty lens.",
        "evidence_id": "ev_34ea0b42f8e582b47aec9aaf6e11",
        "locator": {
          "kind": "pdf",
          "page": 39,
          "section": null,
          "quote": "Troubleshooting:\n1. Damaged or dirty lens. Check for damage or dirt on the\nfocusing lens. Clean or replace lens as required.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 11,
          "source_block_index": 12,
          "bbox": [
            324.24,
            117.998,
            576.008,
            149.958
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

ID: `dbranch_fba140e60cad3ca800eea6edc048ef0216fcd2272af3dc2d3ffb121c0b6a8d53`. Pagine: [38].

- The Cutting Tool or Pen does not move down → Layer or tool mapping is incorrect → Correct the tool or layer mapping

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "instruction_text": "Verify the mapping of your tools and layers are mapped properly under each tool. Look at the tool bar at the bottom of the Cut window to quickly verify tool and layer mapping. If there is no Tool Bar as shown, then click on “View” then click on “Layers” and “Tools” in the main E-Suite menu.",
      "claim_evidence": [
        {
          "source_anchor": "ev_c0de2495c4b6369b621b4966eed4",
          "source_page": 38,
          "quote": "Verify the mapping of your tools and layers are mapped properly under each tool."
        },
        {
          "source_anchor": "ev_3302559758fac20cd829b5abf509",
          "source_page": 38,
          "quote": "Look at the tool bar at the bottom of the Cut window to quickly verify tool and layer mapping."
        },
        {
          "source_anchor": "ev_3302559758fac20cd829b5abf509",
          "source_page": 38,
          "quote": "If there is no Tool Bar as shown, then click on “View” then click on “Layers” and “Tools” in the main E-Suite menu."
        }
      ]
    }
  ],
  "conditions": [
    {
      "text": "If the layer is not mapped to a tool or the tool is not on the tool holder.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "If the layer is not mapped to a tool or the tool is not on the tool holder"
        }
      ]
    }
  ]
}
```

Evidenze del record e dei collegamenti:

```json
{
  "record_lineage_id": "drec_ca7948cae9073f3e051fd4508772cbf02d8f9d66b03f1842cd727eb4d945aee0",
  "branch_lineage_id": "dbranch_fba140e60cad3ca800eea6edc048ef0216fcd2272af3dc2d3ffb121c0b6a8d53",
  "record_window_id": "diagwin_708aa3a806c259850c5e6eec",
  "record_anchor": "ev_1fc5ed15d735b334667612b4385b",
  "branch_anchor": "ev_c0de2495c4b6369b621b4966eed4",
  "indicators": [
    {
      "kind": "symptom",
      "name": "The Cutting Tool or Pen does not move down",
      "description": "The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut.",
      "severity": "Unknown",
      "claim_evidence": [
        {
          "source_anchor": "ev_1fc5ed15d735b334667612b4385b",
          "source_page": 38,
          "quote": "The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut.",
          "evidence_id": "ev_1fc5ed15d735b334667612b4385b",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "Problem: The Cutting Tool or Pen does not move down\nDescription of Problem:\nThe tool or Pen does not move down when cutting a file or\nthey are delayed coming down at the beginning of a cut.  This\ncan be caused by an electrical short, tool mapping in\nsoftware or a problem with the power supply.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 3,
            "source_block_index": 4,
            "bbox": [
              36.0,
              377.558,
              287.758,
              442.518
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "failure_link_evidence": [
        {
          "source_anchor": "ev_1fc5ed15d735b334667612b4385b",
          "source_page": 38,
          "quote": "The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut.",
          "evidence_id": "ev_1fc5ed15d735b334667612b4385b",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "Problem: The Cutting Tool or Pen does not move down\nDescription of Problem:\nThe tool or Pen does not move down when cutting a file or\nthey are delayed coming down at the beginning of a cut.  This\ncan be caused by an electrical short, tool mapping in\nsoftware or a problem with the power supply.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 3,
            "source_block_index": 4,
            "bbox": [
              36.0,
              377.558,
              287.758,
              442.518
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "If the layer is not mapped to a tool or the tool is not on the tool holder",
          "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              40.56,
              655.958,
              287.888,
              687.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_c0de2495c4b6369b621b4966eed4",
          "source_page": 38,
          "quote": "Verify the mapping of your tools and layers are mapped properly under each tool.",
          "evidence_id": "ev_c0de2495c4b6369b621b4966eed4",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "2.Verify the mapping of your tools and layers are mapped\nproperly under each tool.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 5,
            "source_block_index": 6,
            "bbox": [
              36.0,
              498.518,
              287.754,
              519.558
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
    "name": "Layer or tool mapping is incorrect",
    "description": "The layer is not mapped to a tool or the tool is not on the tool holder.",
    "material_context": null,
    "claim_evidence": [
      {
        "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
        "source_page": 38,
        "quote": "If the layer is not mapped to a tool or the tool is not on the tool holder",
        "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
        "locator": {
          "kind": "pdf",
          "page": 38,
          "section": null,
          "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 7,
          "source_block_index": 8,
          "bbox": [
            40.56,
            655.958,
            287.888,
            687.918
          ],
          "table_index": null,
          "row_index": null,
          "ocr_region_index": null
        }
      },
      {
        "source_anchor": "ev_c0de2495c4b6369b621b4966eed4",
        "source_page": 38,
        "quote": "Verify the mapping of your tools and layers are mapped properly under each tool.",
        "evidence_id": "ev_c0de2495c4b6369b621b4966eed4",
        "locator": {
          "kind": "pdf",
          "page": 38,
          "section": null,
          "quote": "2.Verify the mapping of your tools and layers are mapped\nproperly under each tool.",
          "extraction_method": "native_text",
          "printed_page": null,
          "block_index": 5,
          "source_block_index": 6,
          "bbox": [
            36.0,
            498.518,
            287.754,
            519.558
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
      "name": "Correct the tool or layer mapping",
      "description": "Drag the tool to the spindle or the layer to the tool.",
      "instruction_text": "If the layer is not mapped to a tool or the tool is not on the tool holder then just click and drag the tool to the spindle or the layer to the tool before sending the file to the cutter.",
      "action_kind": null,
      "claim_evidence": [
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "then just click and drag the tool to the spindle or the layer to the tool before sending the file to the cutter.",
          "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              40.56,
              655.958,
              287.888,
              687.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        }
      ],
      "resolution_link_evidence": [
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "If the layer is not mapped to a tool or the tool is not on the tool holder",
          "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              40.56,
              655.958,
              287.888,
              687.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "then just click and drag the tool to the spindle or the layer to the tool before sending the file to the cutter.",
          "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              40.56,
              655.958,
              287.888,
              687.918
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_c0de2495c4b6369b621b4966eed4",
          "source_page": 38,
          "quote": "Verify the mapping of your tools and layers are mapped properly under each tool.",
          "evidence_id": "ev_c0de2495c4b6369b621b4966eed4",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "2.Verify the mapping of your tools and layers are mapped\nproperly under each tool.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 5,
            "source_block_index": 6,
            "bbox": [
              36.0,
              498.518,
              287.754,
              519.558
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
      "instruction_text": "Verify the mapping of your tools and layers are mapped properly under each tool. Look at the tool bar at the bottom of the Cut window to quickly verify tool and layer mapping. If there is no Tool Bar as shown, then click on “View” then click on “Layers” and “Tools” in the main E-Suite menu.",
      "claim_evidence": [
        {
          "source_anchor": "ev_3302559758fac20cd829b5abf509",
          "source_page": 38,
          "quote": "If there is no Tool Bar as shown, then click on “View” then click on “Layers” and “Tools” in the main E-Suite menu.",
          "evidence_id": "ev_3302559758fac20cd829b5abf509",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "a)Look at the tool bar at the bottom of the Cut window to\nquickly verify tool and layer mapping.  If there is no Tool Bar\nas shown, then click on “View” then click on “Layers” and\n“Tools” in the main E-Suite menu.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              40.56,
              600.878,
              287.902,
              643.878
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_3302559758fac20cd829b5abf509",
          "source_page": 38,
          "quote": "Look at the tool bar at the bottom of the Cut window to quickly verify tool and layer mapping.",
          "evidence_id": "ev_3302559758fac20cd829b5abf509",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "a)Look at the tool bar at the bottom of the Cut window to\nquickly verify tool and layer mapping.  If there is no Tool Bar\nas shown, then click on “View” then click on “Layers” and\n“Tools” in the main E-Suite menu.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 6,
            "source_block_index": 7,
            "bbox": [
              40.56,
              600.878,
              287.902,
              643.878
            ],
            "table_index": null,
            "row_index": null,
            "ocr_region_index": null
          }
        },
        {
          "source_anchor": "ev_c0de2495c4b6369b621b4966eed4",
          "source_page": 38,
          "quote": "Verify the mapping of your tools and layers are mapped properly under each tool.",
          "evidence_id": "ev_c0de2495c4b6369b621b4966eed4",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "2.Verify the mapping of your tools and layers are mapped\nproperly under each tool.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 5,
            "source_block_index": 6,
            "bbox": [
              36.0,
              498.518,
              287.754,
              519.558
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
      "text": "If the layer is not mapped to a tool or the tool is not on the tool holder.",
      "applies_to": "action",
      "step_index": 0,
      "claim_evidence": [
        {
          "source_anchor": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "source_page": 38,
          "quote": "If the layer is not mapped to a tool or the tool is not on the tool holder",
          "evidence_id": "ev_8159cea3a524cf9e54d7e85e8a2a",
          "locator": {
            "kind": "pdf",
            "page": 38,
            "section": null,
            "quote": "b)If the layer is not mapped to a tool or the tool is not on the\ntool holder then just click and drag the tool to the spindle\nor the layer to the tool before sending the file to the cutter.",
            "extraction_method": "native_text",
            "printed_page": null,
            "block_index": 7,
            "source_block_index": 8,
            "bbox": [
              40.56,
              655.958,
              287.888,
              687.918
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
