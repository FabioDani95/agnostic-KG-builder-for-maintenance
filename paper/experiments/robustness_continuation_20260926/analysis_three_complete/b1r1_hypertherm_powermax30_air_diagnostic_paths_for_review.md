# Catene estratte da verificare

Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.

## Ramo 1

ID: `dbranch_1f656aab9ba50266f77b084bc6bb92c996e1bc9703fd4b15373f908cfec19466`. Pagine: [103].

- Low air pressure → Damaged or defective gas-supply parts → Replace damaged or defective parts

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Apply leak detector solution (for example, Snoop®) to check for leaks at the following points on the gas supply line.",
          "source_anchor": "ev_b11d6868fcd7b8471ab10c639627",
          "source_page": 103
        },
        {
          "quote": "The 6 push-to-connect fittings between the air compressor and the torch lead gas supply fitting",
          "source_anchor": "ev_b9e1a53d969b9927f765ba645778",
          "source_page": 103
        },
        {
          "quote": "The 2 gas hoses that connect to each side of the solenoid valve",
          "source_anchor": "ev_fbbb7cf6cfc2af93668f7e1ff7a5",
          "source_page": 103
        },
        {
          "quote": "Where the filter bowl screws into the air filter assembly",
          "source_anchor": "ev_c2c831e8e3397ca183fd5c731099",
          "source_page": 103
        },
        {
          "quote": "Where the drain hose connects to the bottom of the filter bowl",
          "source_anchor": "ev_15d5658cdbba86db27edf40ada5c",
          "source_page": 103
        },
        {
          "quote": "Also check for leaks where the drain hose connects to the base of the power supply",
          "source_anchor": "ev_c2735ab53c61f1f92de9507141b0",
          "source_page": 103
        }
      ],
      "instruction_text": "Apply leak detector solution to check for leaks at the gas-supply-line connections and parts listed."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "Replace damaged or defective parts as needed.",
          "source_anchor": "ev_84481866966721284eae6604fd3c",
          "source_page": 103
        }
      ],
      "description": "Replace damaged or defective parts as needed.",
      "instruction_text": "Replace damaged or defective parts as needed.",
      "name": "Replace damaged or defective parts",
      "resolution_link_evidence": [
        {
          "quote": "Replace damaged or defective parts as needed.",
          "source_anchor": "ev_84481866966721284eae6604fd3c",
          "source_page": 103
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_338d315920be0528317a45f28d96",
    "ev_b11d6868fcd7b8471ab10c639627",
    "ev_b9e1a53d969b9927f765ba645778",
    "ev_fbbb7cf6cfc2af93668f7e1ff7a5",
    "ev_c2c831e8e3397ca183fd5c731099",
    "ev_15d5658cdbba86db27edf40ada5c",
    "ev_84481866966721284eae6604fd3c",
    "ev_c2735ab53c61f1f92de9507141b0"
  ],
  "branch_anchor": "ev_84481866966721284eae6604fd3c",
  "failure": {
    "claim_evidence": [
      {
        "quote": "damaged or defective parts",
        "source_anchor": "ev_84481866966721284eae6604fd3c",
        "source_page": 103
      }
    ],
    "description": "Damaged or defective parts at the checked gas-supply-line locations may require replacement.",
    "material_context": null,
    "name": "Damaged or defective gas-supply parts"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "low pressure issue",
          "source_anchor": "ev_ec96a88ba564ad4f295f8293748c",
          "source_page": 103
        }
      ],
      "code": null,
      "description": "low pressure issue",
      "failure_link_evidence": [
        {
          "quote": "check for leaks at the following points on the gas supply line.",
          "source_anchor": "ev_b11d6868fcd7b8471ab10c639627",
          "source_page": 103
        },
        {
          "quote": "Replace damaged or defective parts as needed.",
          "source_anchor": "ev_84481866966721284eae6604fd3c",
          "source_page": 103
        }
      ],
      "kind": "symptom",
      "name": "Low air pressure",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Apply leak detector solution (for example, Snoop®) to check for leaks at the following points on the gas supply line.",
          "source_anchor": "ev_b11d6868fcd7b8471ab10c639627",
          "source_page": 103
        },
        {
          "quote": "The 6 push-to-connect fittings between the air compressor and the torch lead gas supply fitting",
          "source_anchor": "ev_b9e1a53d969b9927f765ba645778",
          "source_page": 103
        },
        {
          "quote": "The 2 gas hoses that connect to each side of the solenoid valve",
          "source_anchor": "ev_fbbb7cf6cfc2af93668f7e1ff7a5",
          "source_page": 103
        },
        {
          "quote": "Where the filter bowl screws into the air filter assembly",
          "source_anchor": "ev_c2c831e8e3397ca183fd5c731099",
          "source_page": 103
        },
        {
          "quote": "Where the drain hose connects to the bottom of the filter bowl",
          "source_anchor": "ev_15d5658cdbba86db27edf40ada5c",
          "source_page": 103
        },
        {
          "quote": "Also check for leaks where the drain hose connects to the base of the power supply",
          "source_anchor": "ev_c2735ab53c61f1f92de9507141b0",
          "source_page": 103
        }
      ],
      "instruction_text": "Apply leak detector solution to check for leaks at the gas-supply-line connections and parts listed."
    }
  ],
  "record_anchor": "ev_b11d6868fcd7b8471ab10c639627",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 2

ID: `dbranch_3d28d6c1650b7224824c85bd7091408197eda89803a2db9df96585647c249068`. Pagine: [94].

- Torch cap-sensor test fault → Consumables incorrectly installed → Adjust the consumables

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the consumables are correctly installed.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ],
      "instruction_text": "Make sure the consumables are correctly installed."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "adjustment",
      "claim_evidence": [
        {
          "quote": "Adjust the consumables if necessary.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ],
      "description": "Adjust the consumables if necessary.",
      "instruction_text": "Adjust the consumables if necessary.",
      "name": "Adjust the consumables",
      "resolution_link_evidence": [
        {
          "quote": "Adjust the consumables if necessary.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Adjust the consumables if necessary.",
        "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
        "source_page": 94
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "Make sure the consumables are correctly installed.",
        "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
        "source_page": 94
      }
    ],
    "description": "Consumables whose installation should be checked and adjusted if necessary.",
    "name": "Consumables"
  },
  "allowed_source_anchors": [
    "ev_3a62cbcb8a46ed20edbc041ea3f7"
  ],
  "branch_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Make sure the consumables are correctly installed.",
        "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
        "source_page": 94
      }
    ],
    "description": "The consumables are not correctly installed.",
    "material_context": null,
    "name": "Consumables incorrectly installed"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the consumables are correctly installed.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ],
      "code": null,
      "description": "Consumables are not correctly installed.",
      "failure_link_evidence": [
        {
          "quote": "Adjust the consumables if necessary.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ],
      "kind": "symptom",
      "name": "Torch cap-sensor test fault",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the consumables are correctly installed.",
          "source_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
          "source_page": 94
        }
      ],
      "instruction_text": "Make sure the consumables are correctly installed."
    }
  ],
  "record_anchor": "ev_3a62cbcb8a46ed20edbc041ea3f7",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 3

ID: `dbranch_442efa599e3ecddfb7c5b7a281a4ce41f9da5835943e12168f64af05dc5bf656`. Pagine: [100].

- Only one of VBUS and compressor-enable voltage is present on the power board → Power board fault → Replace the power board

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "replace the power board",
          "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
          "source_page": 100
        }
      ],
      "description": "Replace the power board.",
      "instruction_text": "replace the power board. See Replace the power board on page 135.",
      "name": "Replace the power board",
      "resolution_link_evidence": [
        {
          "quote": "If VBUS or compressor-enable voltage is present on the power board but the other is not, replace the power board.",
          "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
          "source_page": 100
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If VBUS or compressor-enable voltage is present on the power board but the other is not, replace the power board.",
        "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
        "source_page": 100
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the power board",
        "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
        "source_page": 100
      }
    ],
    "description": "Power board identified for replacement.",
    "name": "power board"
  },
  "allowed_source_anchors": [
    "ev_31d4d11f1676b0332821758d2a54"
  ],
  "branch_anchor": "ev_31d4d11f1676b0332821758d2a54",
  "failure": {
    "claim_evidence": [
      {
        "quote": "replace the power board",
        "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
        "source_page": 100
      }
    ],
    "description": "The prescribed replacement of the power board follows when only one of the two voltages is present.",
    "material_context": null,
    "name": "Power board fault"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "If VBUS or compressor-enable voltage is present on the power board but the other is not",
          "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
          "source_page": 100
        }
      ],
      "code": null,
      "description": "One voltage is present on the power board but the other is not.",
      "failure_link_evidence": [
        {
          "quote": "replace the power board",
          "source_anchor": "ev_31d4d11f1676b0332821758d2a54",
          "source_page": 100
        }
      ],
      "kind": "symptom",
      "name": "Only one of VBUS and compressor-enable voltage is present on the power board",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_31d4d11f1676b0332821758d2a54",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 4

ID: `dbranch_58ed9ac8a06e4a1da5757ee10440a8d2df64a45373070e18f6676b4d5e77b6b0`. Pagine: [100].

- VBUS and compressor-enable voltage are both present on the power board → Compressor-driver board fault → Replace the compressor-driver board

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "replace the compressor-driver board",
          "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
          "source_page": 100
        }
      ],
      "description": "Replace the compressor-driver board.",
      "instruction_text": "replace the compressor-driver board. See Replace the compressor-driver board on page 129.",
      "name": "Replace the compressor-driver board",
      "resolution_link_evidence": [
        {
          "quote": "If VBUS and compressor-enable voltage are both present on the power board, replace the compressor-driver board.",
          "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
          "source_page": 100
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If VBUS and compressor-enable voltage are both present on the power board, replace the compressor-driver board.",
        "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
        "source_page": 100
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the compressor-driver board",
        "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
        "source_page": 100
      }
    ],
    "description": "Compressor-driver board identified for replacement.",
    "name": "compressor-driver board"
  },
  "allowed_source_anchors": [
    "ev_63a16d3bcaf0b7a4efc0e66a778b",
    "ev_4e4a7b4b260c7a2bd5f0604d2f50",
    "ev_31d4d11f1676b0332821758d2a54"
  ],
  "branch_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
  "failure": {
    "claim_evidence": [
      {
        "quote": "replace the compressor-driver board",
        "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
        "source_page": 100
      }
    ],
    "description": "The prescribed replacement of the compressor-driver board follows when both voltages are present on the power board.",
    "material_context": null,
    "name": "Compressor-driver board fault"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "If VBUS and compressor-enable voltage are both present on the power board",
          "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
          "source_page": 100
        }
      ],
      "code": null,
      "description": "VBUS and compressor-enable voltage are both present on the power board.",
      "failure_link_evidence": [
        {
          "quote": "replace the compressor-driver board",
          "source_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
          "source_page": 100
        }
      ],
      "kind": "symptom",
      "name": "VBUS and compressor-enable voltage are both present on the power board",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_63a16d3bcaf0b7a4efc0e66a778b",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 5

ID: `dbranch_60a494b94ad459c3860458c72004dcff8ac40307f2d762900683d432170cf50d`. Pagine: [101].

- Low air pressure affecting system performance → Cracked or worn torch O-ring → Replace torch O-ring

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "replace it (428179)",
          "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
          "source_page": 101
        }
      ],
      "description": "Replace the cracked or worn torch O-ring.",
      "instruction_text": "replace it (428179).",
      "name": "Replace torch O-ring",
      "resolution_link_evidence": [
        {
          "quote": "If the O-ring is cracked or worn, replace it (428179).",
          "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
          "source_page": 101
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If the O-ring is cracked or worn, replace it (428179).",
        "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
        "source_page": 101
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "the O-ring",
        "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
        "source_page": 101
      }
    ],
    "description": "O-ring on the torch head.",
    "name": "torch O-ring"
  },
  "allowed_source_anchors": [
    "ev_f94a7c0f7a2f974547d32ee34856",
    "ev_cab44f0ae7e8541023241ec59b1b"
  ],
  "branch_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If the O-ring is cracked or worn",
        "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
        "source_page": 101
      }
    ],
    "description": "The torch O-ring is cracked or worn.",
    "material_context": null,
    "name": "Cracked or worn torch O-ring"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "if low air pressure is affecting system performance",
          "source_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
          "source_page": 101
        }
      ],
      "code": null,
      "description": "Low air pressure is affecting system performance.",
      "failure_link_evidence": [
        {
          "quote": "If the O-ring is cracked or worn",
          "source_anchor": "ev_cab44f0ae7e8541023241ec59b1b",
          "source_page": 101
        }
      ],
      "kind": "symptom",
      "name": "Low air pressure affecting system performance",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 6

ID: `dbranch_6480512507d2f96006ac0e8ec717357409d702f1979d9353f38effc631b09401`. Pagine: [70].

- Internal compressor, temperature, and power ON LEDs blink, and torch cap LED illuminates → Torch repeatedly fired with worn out consumables → Install new consumables

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "Install new consumables in the torch (they may be corroded or approaching end of life).",
          "source_anchor": "ev_9373235a66db1146553971eb7a4d",
          "source_page": 70
        }
      ],
      "description": "Install new consumables in the torch; they may be corroded or approaching end of life.",
      "instruction_text": "Install new consumables in the torch (they may be corroded or approaching end of life).",
      "name": "Install new consumables",
      "resolution_link_evidence": [
        {
          "quote": "Install new consumables in the torch",
          "source_anchor": "ev_9373235a66db1146553971eb7a4d",
          "source_page": 70
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_ae01749c40947bfcb624307d6fe2",
    "ev_a82a5a3b9cb55ad43fefc4c4ede1",
    "ev_9373235a66db1146553971eb7a4d",
    "ev_3831faec4354524f9e26d695a99d"
  ],
  "branch_anchor": "ev_a82a5a3b9cb55ad43fefc4c4ede1",
  "failure": {
    "claim_evidence": [
      {
        "quote": "The torch was repeatedly fired with worn out consumables.",
        "source_anchor": "ev_a82a5a3b9cb55ad43fefc4c4ede1",
        "source_page": 70
      }
    ],
    "description": "The torch was repeatedly fired with worn out consumables.",
    "material_context": null,
    "name": "Torch repeatedly fired with worn out consumables"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The internal compressor, temperature, and power ON LEDs blink, and the torch cap LED illuminates.",
          "source_anchor": "ev_ae01749c40947bfcb624307d6fe2",
          "source_page": 70
        }
      ],
      "code": null,
      "description": "The internal compressor, temperature, and power ON LEDs blink, and the torch cap LED illuminates.",
      "failure_link_evidence": [
        {
          "quote": "The torch was repeatedly fired with worn out consumables.",
          "source_anchor": "ev_a82a5a3b9cb55ad43fefc4c4ede1",
          "source_page": 70
        }
      ],
      "kind": "symptom",
      "name": "Internal compressor, temperature, and power ON LEDs blink, and torch cap LED illuminates",
      "severity": "High"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_ae01749c40947bfcb624307d6fe2",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 7

ID: `dbranch_65dd5e3ea1fbd121e8c81607d1a0a4e0572e7a23145aefb3df85166cdc418ba8`. Pagine: [61].

- Consumable damage or wear → Consumable damage or wear → Repair or replace components

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ],
      "description": "Repair or replace affected components as necessary.",
      "instruction_text": "Repair or replace components as necessary.",
      "name": "Repair or replace components",
      "resolution_link_evidence": [
        {
          "quote": "Inspect the consumables for damage or wear.",
          "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
          "source_page": 61
        },
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Inspect the consumables for damage or wear.",
        "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
        "source_page": 61
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "Inspect the consumables for damage or wear.",
        "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
        "source_page": 61
      }
    ],
    "description": "The consumables are inspected for damage or wear.",
    "name": "Consumables"
  },
  "allowed_source_anchors": [
    "ev_e4ea6b858902ca2bd26929bffe18",
    "ev_3a3d5150e16b34ae8619957a30ac"
  ],
  "branch_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
  "failure": {
    "claim_evidence": [
      {
        "quote": "the consumables for damage or wear.",
        "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
        "source_page": 61
      }
    ],
    "description": "The consumables are damaged or worn.",
    "material_context": null,
    "name": "Consumable damage or wear"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Inspect the consumables for damage or wear.",
          "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
          "source_page": 61
        }
      ],
      "code": null,
      "description": "Inspect the consumables for damage or wear.",
      "failure_link_evidence": [
        {
          "quote": "Inspect the consumables for damage or wear.",
          "source_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
          "source_page": 61
        }
      ],
      "kind": "symptom",
      "name": "Consumable damage or wear",
      "severity": "Low"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_e4ea6b858902ca2bd26929bffe18",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 8

ID: `dbranch_81833511bc0033d7c3187d868accafe50a32aecc8bc121d0dbe5ed30df1fd5f1`. Pagine: [61].

- Broken or loose wiring connections, burn or char marks, or damaged components → Power board side wiring or component fault → Repair or replace components

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_275a9b088354eecd0020e51aae04",
          "source_page": 61
        }
      ],
      "description": "Repair or replace affected components as necessary.",
      "instruction_text": "Repair or replace components as necessary.",
      "name": "Repair or replace components",
      "resolution_link_evidence": [
        {
          "quote": "Power board side: Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
          "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
          "source_page": 61
        },
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_275a9b088354eecd0020e51aae04",
          "source_page": 61
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Power board side: Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
        "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
        "source_page": 61
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "Power board side: Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
        "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
        "source_page": 61
      }
    ],
    "description": "Wiring connections and components on the power board side of the power supply.",
    "name": "Power board side wiring and components"
  },
  "allowed_source_anchors": [
    "ev_44a6381f8f7c90684339c28d16df",
    "ev_275a9b088354eecd0020e51aae04"
  ],
  "branch_anchor": "ev_44a6381f8f7c90684339c28d16df",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Power board side: Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
        "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
        "source_page": 61
      }
    ],
    "description": "Broken or loose wiring connections, burn or char marks, or damaged components are present on the power board side.",
    "material_context": null,
    "name": "Power board side wiring or component fault"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
          "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
          "source_page": 61
        }
      ],
      "code": null,
      "description": "Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
      "failure_link_evidence": [
        {
          "quote": "Look for broken or loose wiring connections, burn and char marks, damaged components, and so on.",
          "source_anchor": "ev_44a6381f8f7c90684339c28d16df",
          "source_page": 61
        }
      ],
      "kind": "symptom",
      "name": "Broken or loose wiring connections, burn or char marks, or damaged components",
      "severity": "Low"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_44a6381f8f7c90684339c28d16df",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 9

ID: `dbranch_8a3842a06ac098eb745560db008e94229a90518f52bb864e1bcff84e5c56a512`. Pagine: [91].

- Torch stuck open or torch stuck closed → Torch plunger does not move freely → Replace the torch body

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the torch body",
          "source_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
          "source_page": 91
        }
      ],
      "description": "Replace the torch body.",
      "instruction_text": "Replace the torch body. See Replace the torch body on page 201.",
      "name": "Replace the torch body",
      "resolution_link_evidence": [
        {
          "quote": "If no, replace the torch body.",
          "source_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
          "source_page": 91
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If no, replace the torch body.",
        "source_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
        "source_page": 91
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the torch body",
        "source_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
        "source_page": 91
      }
    ],
    "description": "Torch body to be replaced when the plunger does not move freely.",
    "name": "Torch body"
  },
  "allowed_source_anchors": [
    "ev_0a2b75ac3b2f798a356b4d534808"
  ],
  "branch_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Does the torch plunger move freely in the torch head?",
        "source_anchor": "ev_7135e9bd83651bf6a8530024f2c0",
        "source_page": 91
      }
    ],
    "description": "The torch plunger does not move freely in the torch head.",
    "material_context": null,
    "name": "Torch plunger does not move freely"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "“torch stuck open” and “torch stuck closed” failures",
          "source_anchor": "ev_bcf0cd35a343ca8384ee3fc2882d",
          "source_page": 91
        }
      ],
      "code": null,
      "description": "Intermittent torch stuck open or torch stuck closed failure.",
      "failure_link_evidence": [
        {
          "quote": "If no, replace the torch body.",
          "source_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
          "source_page": 91
        }
      ],
      "kind": "symptom",
      "name": "Torch stuck open or torch stuck closed",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_0a2b75ac3b2f798a356b4d534808",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 10

ID: `dbranch_8fd6a2727244085f79b7b3f94a54ed6c0f44ad967cb1c0308bc06461e5cebb04`. Pagine: [61].

- Damage to the torch or torch lead → Damage to the torch or torch lead → Repair or replace components

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ],
      "description": "Repair or replace affected components as necessary.",
      "instruction_text": "Repair or replace components as necessary.",
      "name": "Repair or replace components",
      "resolution_link_evidence": [
        {
          "quote": "Inspect the torch and the torch lead for damage.",
          "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
          "source_page": 61
        },
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Inspect the torch and the torch lead for damage.",
        "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
        "source_page": 61
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "Inspect the torch and the torch lead for damage.",
        "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
        "source_page": 61
      }
    ],
    "description": "The torch and torch lead are inspected for damage.",
    "name": "Torch and torch lead"
  },
  "allowed_source_anchors": [
    "ev_f26220469694e7feb92d0d1072ec",
    "ev_3a3d5150e16b34ae8619957a30ac"
  ],
  "branch_anchor": "ev_f26220469694e7feb92d0d1072ec",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Inspect the torch and the torch lead for damage.",
        "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
        "source_page": 61
      }
    ],
    "description": "The torch or torch lead is damaged.",
    "material_context": null,
    "name": "Damage to the torch or torch lead"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Inspect the torch and the torch lead for damage.",
          "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
          "source_page": 61
        }
      ],
      "code": null,
      "description": "Inspect the torch and the torch lead for damage.",
      "failure_link_evidence": [
        {
          "quote": "Inspect the torch and the torch lead for damage.",
          "source_anchor": "ev_f26220469694e7feb92d0d1072ec",
          "source_page": 61
        }
      ],
      "kind": "symptom",
      "name": "Damage to the torch or torch lead",
      "severity": "Low"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_f26220469694e7feb92d0d1072ec",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 11

ID: `dbranch_919a526b14a864d45f66049450ade07277507987b4febfde0cb5ab8b1845d2c1`. Pagine: [93].

- Invalid torch start signal → Fault in torch start switch or torch wires → Replace torch start switch or torch wires if necessary

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "check the torch start switch and the torch wires",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ],
      "instruction_text": "Check the torch start switch and the torch wires."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "Replace if necessary.",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ],
      "description": "Replace the torch start switch or torch wires if necessary.",
      "instruction_text": "Check the torch start switch and the torch wires. Replace if necessary. See Replace the start switch on page 203 or Replace the torch lead and strain relief on page 153.",
      "name": "Replace torch start switch or torch wires if necessary",
      "resolution_link_evidence": [
        {
          "quote": "check the torch start switch and the torch wires. Replace if necessary.",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_5378f0832ffda3272b70fc7a223c"
  ],
  "branch_anchor": "ev_5378f0832ffda3272b70fc7a223c",
  "failure": {
    "claim_evidence": [
      {
        "quote": "check the torch start switch and the torch wires",
        "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
        "source_page": 93
      }
    ],
    "description": "The troubleshooting step identifies the torch start switch and torch wires as items to check when the test fails.",
    "material_context": null,
    "name": "Fault in torch start switch or torch wires"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "If this test fails",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ],
      "code": null,
      "description": "The plasma-start test fails to verify the valid start signal.",
      "failure_link_evidence": [
        {
          "quote": "check the torch start switch and the torch wires",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ],
      "kind": "symptom",
      "name": "Invalid torch start signal",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "check the torch start switch and the torch wires",
          "source_anchor": "ev_5378f0832ffda3272b70fc7a223c",
          "source_page": 93
        }
      ],
      "instruction_text": "Check the torch start switch and the torch wires."
    }
  ],
  "record_anchor": "ev_5378f0832ffda3272b70fc7a223c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 12

ID: `dbranch_9ae2d0a223c852ecb90df911730357b2bea4fe23451b3d7a3b509d2050e3e8c1`. Pagine: [61].

- Damage to the power supply cover or external components → Damage to the power supply cover or external components → Repair or replace components

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ],
      "description": "Repair or replace affected components as necessary.",
      "instruction_text": "Repair or replace components as necessary.",
      "name": "Repair or replace components",
      "resolution_link_evidence": [
        {
          "quote": "Inspect the exterior of the power supply for damage to the cover and external components, such as the power cord and plug.",
          "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
          "source_page": 61
        },
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_3a3d5150e16b34ae8619957a30ac",
          "source_page": 61
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Inspect the exterior of the power supply for damage to the cover and external components, such as the power cord and plug.",
        "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
        "source_page": 61
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "the cover and external components, such as the power cord and plug.",
        "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
        "source_page": 61
      }
    ],
    "description": "External components include the power cord and plug.",
    "name": "Power supply cover and external components"
  },
  "allowed_source_anchors": [
    "ev_3b2d00f5705ed4f38fb697c65606",
    "ev_3a3d5150e16b34ae8619957a30ac"
  ],
  "branch_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
  "failure": {
    "claim_evidence": [
      {
        "quote": "damage to the cover and external components, such as the power cord and plug.",
        "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
        "source_page": 61
      }
    ],
    "description": "The power supply cover or an external component, such as the power cord or plug, is damaged.",
    "material_context": null,
    "name": "Damage to the power supply cover or external components"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Inspect the exterior of the power supply for damage to the cover and external components, such as the power cord and plug.",
          "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
          "source_page": 61
        }
      ],
      "code": null,
      "description": "Inspect the exterior of the power supply for damage to the cover and external components, such as the power cord and plug.",
      "failure_link_evidence": [
        {
          "quote": "Inspect the exterior of the power supply for damage to the cover and external components, such as the power cord and plug.",
          "source_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
          "source_page": 61
        }
      ],
      "kind": "symptom",
      "name": "Damage to the power supply cover or external components",
      "severity": "Low"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_3b2d00f5705ed4f38fb697c65606",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 13

ID: `dbranch_a41e2887ad1067fa81134fb0306c91a243c2f124ddf14adddb93ba1894bed2b0`. Pagine: [103].

- Low pressure issue persists after checks → Faulty internal air compressor → Install a new air compressor

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Install a new air compressor.",
          "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
          "source_page": 103
        }
      ],
      "description": "Install a new air compressor.",
      "instruction_text": "Install a new air compressor. See page 169.",
      "name": "Install a new air compressor",
      "resolution_link_evidence": [
        {
          "quote": "the internal air compressor may be faulty. Install a new air compressor.",
          "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
          "source_page": 103
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "the internal air compressor may be faulty. Install a new air compressor.",
        "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
        "source_page": 103
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "the internal air compressor may be faulty",
        "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
        "source_page": 103
      }
    ],
    "description": "Internal air compressor identified as potentially faulty and to be replaced.",
    "name": "internal air compressor"
  },
  "allowed_source_anchors": [
    "ev_f94a7c0f7a2f974547d32ee34856",
    "ev_2021a0c1fa73e2335fb7234f7a50"
  ],
  "branch_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
  "failure": {
    "claim_evidence": [
      {
        "quote": "the internal air compressor may be faulty",
        "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
        "source_page": 103
      }
    ],
    "description": "The internal air compressor may be faulty if low pressure persists after all checks.",
    "material_context": null,
    "name": "Faulty internal air compressor"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "if low air pressure is affecting system performance",
          "source_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
          "source_page": 101
        }
      ],
      "code": null,
      "description": "The low pressure issue persists after all of the checks.",
      "failure_link_evidence": [
        {
          "quote": "If low pressure persists after you complete all of these checks",
          "source_anchor": "ev_2021a0c1fa73e2335fb7234f7a50",
          "source_page": 103
        }
      ],
      "kind": "symptom",
      "name": "Low pressure issue persists after checks",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 14

ID: `dbranch_a5266bff31c02deb628968f99b2074b9b69293412cd7f97db1f1f21c5b673f40`. Pagine: [94].

- Torch cap-sensor test fault → Faulty cap-sensor switch or broken torch-lead wire → Replace the faulty part

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "Replace the faulty part.",
          "source_anchor": "ev_3c579d72ba632e5016c8f47389a1",
          "source_page": 94
        }
      ],
      "description": "Replace the faulty cap-sensor switch or torch lead.",
      "instruction_text": "Replace the faulty part. See Replace the cap-sensor switch on page 204 or Replace the torch lead and strain relief on page 153.",
      "name": "Replace the faulty part",
      "resolution_link_evidence": [
        {
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire. Replace the faulty part.",
          "source_anchor": "ev_3c579d72ba632e5016c8f47389a1",
          "source_page": 94
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_3c579d72ba632e5016c8f47389a1"
  ],
  "branch_anchor": "ev_3c579d72ba632e5016c8f47389a1",
  "failure": {
    "claim_evidence": [
      {
        "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire",
        "source_anchor": "ev_3c579d72ba632e5016c8f47389a1",
        "source_page": 94
      }
    ],
    "description": "With the torch plunger and consumables working properly, the cap-sensor switch is faulty or the torch lead has a broken wire.",
    "material_context": null,
    "name": "Faulty cap-sensor switch or broken torch-lead wire"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "If the torch parts mentioned in step 7 and step 8 are working properly",
          "source_anchor": "ev_3c579d72ba632e5016c8f47389a1",
          "source_page": 94
        }
      ],
      "code": null,
      "description": "Torch parts mentioned in the preceding checks are working properly, but a fault remains in the cap-sensor switch or torch lead.",
      "failure_link_evidence": [
        {
          "quote": "the cap-sensor switch is faulty or the torch lead has a broken wire",
          "source_anchor": "ev_3c579d72ba632e5016c8f47389a1",
          "source_page": 94
        }
      ],
      "kind": "symptom",
      "name": "Torch cap-sensor test fault",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_3c579d72ba632e5016c8f47389a1",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 15

ID: `dbranch_ae259100929a009020c40aca7730a95c8b7b78e817d72d3e6fc92e3e9fd70e62`. Pagine: [70].

- Torch cap LED illuminates while the machine is powered ON → Cap-sensing circuit open due to loose, incorrectly installed, or missing consumables → Install consumables correctly

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Perform Test 7 – torch cap-sensor on page 94.",
          "source_anchor": "ev_464ae4cac226af35c7dc4ee5c4b0",
          "source_page": 70
        }
      ],
      "instruction_text": "Perform Test 7 – torch cap-sensor on page 94."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "adjustment",
      "claim_evidence": [
        {
          "quote": "Make sure the consumables are installed correctly.",
          "source_anchor": "ev_baf1f2bca0a1d77b48c41f2ba720",
          "source_page": 70
        }
      ],
      "description": "Make sure the consumables are installed correctly.",
      "instruction_text": "Make sure the consumables are installed correctly.",
      "name": "Install consumables correctly",
      "resolution_link_evidence": [
        {
          "quote": "Make sure the consumables are installed correctly.",
          "source_anchor": "ev_baf1f2bca0a1d77b48c41f2ba720",
          "source_page": 70
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_4b254e7056eb0c4a57115f7dcf5f"
  ],
  "branch_anchor": "ev_1c46d41b0b9510d06aed123dc501",
  "failure": {
    "claim_evidence": [
      {
        "quote": "The cap-sensing circuit is open due to:",
        "source_anchor": "ev_1c46d41b0b9510d06aed123dc501",
        "source_page": 70
      },
      {
        "quote": "The consumables are loose, incorrectly installed, or missing.",
        "source_anchor": "ev_ddc7e1de0374b8e25d31558aca24",
        "source_page": 70
      }
    ],
    "description": "The cap-sensing circuit is open because the consumables are loose, incorrectly installed, or missing.",
    "material_context": null,
    "name": "Cap-sensing circuit open due to loose, incorrectly installed, or missing consumables"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The torch cap LED illuminates while the machine is powered ON.",
          "source_anchor": "ev_4b254e7056eb0c4a57115f7dcf5f",
          "source_page": 70
        }
      ],
      "code": null,
      "description": "The torch cap LED illuminates while the machine is powered ON.",
      "failure_link_evidence": [
        {
          "quote": "The cap-sensing circuit is open due to:",
          "source_anchor": "ev_1c46d41b0b9510d06aed123dc501",
          "source_page": 70
        },
        {
          "quote": "The consumables are loose, incorrectly installed, or missing.",
          "source_anchor": "ev_ddc7e1de0374b8e25d31558aca24",
          "source_page": 70
        }
      ],
      "kind": "symptom",
      "name": "Torch cap LED illuminates while the machine is powered ON",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Perform Test 7 – torch cap-sensor on page 94.",
          "source_anchor": "ev_464ae4cac226af35c7dc4ee5c4b0",
          "source_page": 70
        }
      ],
      "instruction_text": "Perform Test 7 – torch cap-sensor on page 94."
    }
  ],
  "record_anchor": "ev_4b254e7056eb0c4a57115f7dcf5f",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 16

ID: `dbranch_b1dd54cd3e970f607dae221147f0951a91995f823adf6ed3a18d1678524d1733`. Pagine: [91].

- Torch stuck open or torch stuck closed → Torch plunger moves freely → Replace the torch lead

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the torch lead",
          "source_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
          "source_page": 91
        }
      ],
      "description": "Replace the torch lead.",
      "instruction_text": "Replace the torch lead. See Replace the torch lead on page 205.",
      "name": "Replace the torch lead",
      "resolution_link_evidence": [
        {
          "quote": "If yes, replace the torch lead.",
          "source_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
          "source_page": 91
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If yes, replace the torch lead.",
        "source_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
        "source_page": 91
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the torch lead",
        "source_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
        "source_page": 91
      }
    ],
    "description": "Torch lead to be replaced in this troubleshooting branch.",
    "name": "Torch lead"
  },
  "allowed_source_anchors": [
    "ev_364be271fe4d53d986dbb4f9b0b4"
  ],
  "branch_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Does the torch plunger move freely in the torch head?",
        "source_anchor": "ev_7135e9bd83651bf6a8530024f2c0",
        "source_page": 91
      }
    ],
    "description": "The torch plunger moves freely in the torch head; the troubleshooting branch directs replacement of the torch lead.",
    "material_context": null,
    "name": "Torch plunger moves freely"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "“torch stuck open” and “torch stuck closed” failures",
          "source_anchor": "ev_bcf0cd35a343ca8384ee3fc2882d",
          "source_page": 91
        }
      ],
      "code": null,
      "description": "Intermittent torch stuck open or torch stuck closed failure.",
      "failure_link_evidence": [
        {
          "quote": "If yes, replace the torch lead.",
          "source_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
          "source_page": 91
        }
      ],
      "kind": "symptom",
      "name": "Torch stuck open or torch stuck closed",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_364be271fe4d53d986dbb4f9b0b4",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 17

ID: `dbranch_bc130d4f76411c743eed21f1d5191a5a3687a9b99490d6119004ad677d292dce`. Pagine: [89].

- Solenoid valve does not click → Solenoid valve faulty → Replace the solenoid valve

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the solenoid valve",
          "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
          "source_page": 89
        }
      ],
      "description": "Replace the solenoid valve when it does not click and the voltage check reads 24 VDC.",
      "instruction_text": "replace the solenoid valve",
      "name": "Replace the solenoid valve",
      "resolution_link_evidence": [
        {
          "quote": "If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve.",
          "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
          "source_page": 89
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "replace the solenoid valve",
        "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
        "source_page": 89
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "solenoid valve (V1)",
        "source_anchor": "ev_785e3d3d3ce9c8bbe51917fb248c",
        "source_page": 89
      }
    ],
    "description": "The valve identified as V1.",
    "name": "solenoid valve"
  },
  "allowed_source_anchors": [
    "ev_785e3d3d3ce9c8bbe51917fb248c",
    "ev_b8db6427673cd7cc86a27433b7c9",
    "ev_9e3366563600a9e5359a1a28a47b"
  ],
  "branch_anchor": "ev_9e3366563600a9e5359a1a28a47b",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If you do not hear the valve click and the voltage check reads 24 VDC",
        "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
        "source_page": 89
      }
    ],
    "description": "The solenoid valve is faulty when it does not click and the voltage check reads 24 VDC.",
    "material_context": null,
    "name": "Solenoid valve faulty"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The valve should click.",
          "source_anchor": "ev_b8db6427673cd7cc86a27433b7c9",
          "source_page": 89
        },
        {
          "quote": "If you do not hear the valve click",
          "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
          "source_page": 89
        }
      ],
      "code": null,
      "description": "The solenoid valve does not click when power is turned on during the test.",
      "failure_link_evidence": [
        {
          "quote": "If you do not hear the valve click and the voltage check reads 24 VDC",
          "source_anchor": "ev_9e3366563600a9e5359a1a28a47b",
          "source_page": 89
        }
      ],
      "kind": "symptom",
      "name": "Solenoid valve does not click",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_785e3d3d3ce9c8bbe51917fb248c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 18

ID: `dbranch_c4a714919ce7deb992e26ed9ec3738cca746a9e96b7d30b1bde840204db12af5`. Pagine: [93].

- Incorrect torch-start test values → Control board fault indicated by correct test values → Replace the control board

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the control board",
          "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
          "source_page": 93
        }
      ],
      "description": "Replace the control board.",
      "instruction_text": "Replace the control board. See Replace the control board on page 126.",
      "name": "Replace the control board",
      "resolution_link_evidence": [
        {
          "quote": "If yes, replace the control board.",
          "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
          "source_page": 93
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If yes, replace the control board.",
        "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
        "source_page": 93
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the control board",
        "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
        "source_page": 93
      }
    ],
    "description": "Control board replaced when measured values are correct.",
    "name": "Control board"
  },
  "allowed_source_anchors": [
    "ev_1fa22c65aa4daa3df1b9af44f117"
  ],
  "branch_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If yes, replace the control board.",
        "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
        "source_page": 93
      }
    ],
    "description": "When the measured values are correct, the troubleshooting branch directs replacement of the control board.",
    "material_context": null,
    "name": "Control board fault indicated by correct test values"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Are the values correct?",
          "source_anchor": "ev_297d962d2f2e7af9e54ef6d6fbc3",
          "source_page": 93
        }
      ],
      "code": null,
      "description": "The pin 16 of J7 measurement values are not correct.",
      "failure_link_evidence": [
        {
          "quote": "If yes, replace the control board.",
          "source_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
          "source_page": 93
        }
      ],
      "kind": "symptom",
      "name": "Incorrect torch-start test values",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_1fa22c65aa4daa3df1b9af44f117",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 19

ID: `dbranch_c8b3a03377866837ddc1ec4304ea263ab8926b9916de284fcc825b9a9a7350fe`. Pagine: [101].

- Low air pressure affecting system performance → Dry torch O-ring → Lubricate torch O-ring and threads

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "apply a thin film of silicone lubricant (027055) on the O-ring and the threads",
          "source_anchor": "ev_cf6f952243a922763f06bf760859",
          "source_page": 101
        }
      ],
      "description": "Apply a thin film of silicone lubricant to the O-ring and threads.",
      "instruction_text": "apply a thin film of silicone lubricant (027055) on the O-ring and the threads.",
      "name": "Lubricate torch O-ring and threads",
      "resolution_link_evidence": [
        {
          "quote": "If the torch O-ring is dry, apply a thin film of silicone lubricant (027055) on the O-ring and the threads.",
          "source_anchor": "ev_cf6f952243a922763f06bf760859",
          "source_page": 101
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If the torch O-ring is dry, apply a thin film of silicone lubricant (027055) on the O-ring and the threads.",
        "source_anchor": "ev_cf6f952243a922763f06bf760859",
        "source_page": 101
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "the O-ring",
        "source_anchor": "ev_cf6f952243a922763f06bf760859",
        "source_page": 101
      }
    ],
    "description": "O-ring on the torch head.",
    "name": "torch O-ring"
  },
  "allowed_source_anchors": [
    "ev_f94a7c0f7a2f974547d32ee34856",
    "ev_cf6f952243a922763f06bf760859"
  ],
  "branch_anchor": "ev_cf6f952243a922763f06bf760859",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If the torch O-ring is dry",
        "source_anchor": "ev_cf6f952243a922763f06bf760859",
        "source_page": 101
      }
    ],
    "description": "The torch O-ring is dry.",
    "material_context": null,
    "name": "Dry torch O-ring"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "if low air pressure is affecting system performance",
          "source_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
          "source_page": 101
        }
      ],
      "code": null,
      "description": "Low air pressure is affecting system performance.",
      "failure_link_evidence": [
        {
          "quote": "If the torch O-ring is dry",
          "source_anchor": "ev_cf6f952243a922763f06bf760859",
          "source_page": 101
        }
      ],
      "kind": "symptom",
      "name": "Low air pressure affecting system performance",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_f94a7c0f7a2f974547d32ee34856",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 20

ID: `dbranch_d78db94374561167b867e273536e48c6201e9dd57db637f3c25fa7907c2c6e5c`. Pagine: [100].

- Neither VBUS nor compressor-enable voltage is present on the power board → Power board fault → Replace the power board

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "replace the power board",
          "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
          "source_page": 100
        }
      ],
      "description": "Replace the power board.",
      "instruction_text": "replace the power board. See Replace the power board on page 135.",
      "name": "Replace the power board",
      "resolution_link_evidence": [
        {
          "quote": "If neither VBUS nor compressor-enable voltage are present on the power board, replace the power board.",
          "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
          "source_page": 100
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If neither VBUS nor compressor-enable voltage are present on the power board, replace the power board.",
        "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
        "source_page": 100
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the power board",
        "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
        "source_page": 100
      }
    ],
    "description": "Power board identified for replacement.",
    "name": "power board"
  },
  "allowed_source_anchors": [
    "ev_4e4a7b4b260c7a2bd5f0604d2f50"
  ],
  "branch_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
  "failure": {
    "claim_evidence": [
      {
        "quote": "replace the power board",
        "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
        "source_page": 100
      }
    ],
    "description": "The prescribed replacement of the power board follows when neither voltage is present on it.",
    "material_context": null,
    "name": "Power board fault"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "If neither VBUS nor compressor-enable voltage are present on the power board",
          "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
          "source_page": 100
        }
      ],
      "code": null,
      "description": "Neither VBUS nor compressor-enable voltage is present on the power board.",
      "failure_link_evidence": [
        {
          "quote": "replace the power board",
          "source_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
          "source_page": 100
        }
      ],
      "kind": "symptom",
      "name": "Neither VBUS nor compressor-enable voltage is present on the power board",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_4e4a7b4b260c7a2bd5f0604d2f50",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 21

ID: `dbranch_e60925134f48cb01d0284b55d72537bdb7cf34d04a8c59db9fc86980061770df`. Pagine: [65].

- No gas flows when you pull the torch trigger → Damaged torch or torch lead → Inspect and replace torch or torch lead if necessary

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the control board start LED \nilluminates when you pull the torch trigger. If \nit does not, perform Test 6 – plasma start on \npage 92.",
          "source_anchor": "ev_a38c61265752a4fa34e731977c3d",
          "source_page": 65
        }
      ],
      "instruction_text": "Make sure the control board start LED illuminates when you pull the torch trigger. If it does not, perform Test 6 – plasma start on page 92."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "Inspect the torch and torch lead, and \nreplace if necessary.",
          "source_anchor": "ev_23fb00a9e36f706b0e3dd253d8fd",
          "source_page": 65
        }
      ],
      "description": "Inspect the torch and torch lead, and replace if necessary.",
      "instruction_text": "Inspect the torch and torch lead, and replace if necessary.",
      "name": "Inspect and replace torch or torch lead if necessary",
      "resolution_link_evidence": [
        {
          "quote": "Damaged torch or torch lead",
          "source_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
          "source_page": 65
        },
        {
          "quote": "Inspect the torch and torch lead, and \nreplace if necessary.",
          "source_anchor": "ev_23fb00a9e36f706b0e3dd253d8fd",
          "source_page": 65
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Damaged torch or torch lead",
        "source_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
        "source_page": 65
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "Damaged torch or torch lead",
        "source_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
        "source_page": 65
      }
    ],
    "description": "Damaged torch or torch lead",
    "name": "Torch or torch lead"
  },
  "allowed_source_anchors": [
    "ev_7e9f962bf0fc31791535f08ba078",
    "ev_d23ba4d4720dab418a268656c59f",
    "ev_f214c6f973945e623d3d4f02b4b1",
    "ev_23fb00a9e36f706b0e3dd253d8fd",
    "ev_a38c61265752a4fa34e731977c3d"
  ],
  "branch_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
  "failure": {
    "claim_evidence": [
      {
        "quote": "The start signal is not reaching the control \nboard due to:",
        "source_anchor": "ev_d23ba4d4720dab418a268656c59f",
        "source_page": 65
      },
      {
        "quote": "Damaged torch or torch lead",
        "source_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
        "source_page": 65
      }
    ],
    "description": "The start signal is not reaching the control board due to a damaged torch or torch lead.",
    "material_context": null,
    "name": "Damaged torch or torch lead"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The power ON LED illuminates, but no fault LEDs illuminate, and no gas \nflows when you pull the torch trigger.",
          "source_anchor": "ev_7e9f962bf0fc31791535f08ba078",
          "source_page": 65
        }
      ],
      "code": null,
      "description": "The power ON LED illuminates, but no fault LEDs illuminate, and no gas flows when you pull the torch trigger.",
      "failure_link_evidence": [
        {
          "quote": "The power ON LED illuminates, but no fault LEDs illuminate, and no gas \nflows when you pull the torch trigger.",
          "source_anchor": "ev_7e9f962bf0fc31791535f08ba078",
          "source_page": 65
        },
        {
          "quote": "The start signal is not reaching the control \nboard due to:",
          "source_anchor": "ev_d23ba4d4720dab418a268656c59f",
          "source_page": 65
        },
        {
          "quote": "Damaged torch or torch lead",
          "source_anchor": "ev_f214c6f973945e623d3d4f02b4b1",
          "source_page": 65
        }
      ],
      "kind": "symptom",
      "name": "No gas flows when you pull the torch trigger",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the control board start LED \nilluminates when you pull the torch trigger. If \nit does not, perform Test 6 – plasma start on \npage 92.",
          "source_anchor": "ev_a38c61265752a4fa34e731977c3d",
          "source_page": 65
        }
      ],
      "instruction_text": "Make sure the control board start LED illuminates when you pull the torch trigger. If it does not, perform Test 6 – plasma start on page 92."
    }
  ],
  "record_anchor": "ev_7e9f962bf0fc31791535f08ba078",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 22

ID: `dbranch_f79ad13d7c4bb5d9c77dd0090e48eec360469e935e7571db7902b65b71b5b78e`. Pagine: [94].

- Torch cap-sensor test fault → Torch plunger does not move smoothly → Replace the torch body

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the torch plunger moves smoothly.",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ],
      "instruction_text": "Make sure the torch plunger moves smoothly."
    }
  ],
  "conditions": []
}
```

Evidenze del record e dei collegamenti:

```json
{
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the torch body",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ],
      "description": "Replace the torch body.",
      "instruction_text": "If the torch plunger does not move smoothly, replace the torch body. See Replace the torch body on page 201.",
      "name": "Replace the torch body",
      "resolution_link_evidence": [
        {
          "quote": "If it does not, replace the torch body.",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If it does not, replace the torch body.",
        "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
        "source_page": 94
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the torch body",
        "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
        "source_page": 94
      }
    ],
    "description": "Torch body to replace if the torch plunger does not move smoothly.",
    "name": "Torch body"
  },
  "allowed_source_anchors": [
    "ev_e9c7df686169090102fb4f45f3ab"
  ],
  "branch_anchor": "ev_e9c7df686169090102fb4f45f3ab",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If it does not",
        "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
        "source_page": 94
      }
    ],
    "description": "The torch plunger does not move smoothly.",
    "material_context": null,
    "name": "Torch plunger does not move smoothly"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the torch plunger moves smoothly.",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ],
      "code": null,
      "description": "The torch plunger does not move smoothly during cap-sensor testing.",
      "failure_link_evidence": [
        {
          "quote": "If it does not, replace the torch body.",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ],
      "kind": "symptom",
      "name": "Torch cap-sensor test fault",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Make sure the torch plunger moves smoothly.",
          "source_anchor": "ev_e9c7df686169090102fb4f45f3ab",
          "source_page": 94
        }
      ],
      "instruction_text": "Make sure the torch plunger moves smoothly."
    }
  ],
  "record_anchor": "ev_e9c7df686169090102fb4f45f3ab",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 23

ID: `dbranch_f7c865936f9c49985706799615035c3daca55d2d075dd6405460a603dc5cb1d4`. Pagine: [93].

- Incorrect torch-start test values → Power board fault indicated by incorrect test values → Replace the power board

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "replace the power board",
          "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
          "source_page": 93
        }
      ],
      "description": "Replace the power board.",
      "instruction_text": "Replace the power board. See Replace the power board on page 135.",
      "name": "Replace the power board",
      "resolution_link_evidence": [
        {
          "quote": "If no, replace the power board.",
          "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
          "source_page": 93
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If no, replace the power board.",
        "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
        "source_page": 93
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "replace the power board",
        "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
        "source_page": 93
      }
    ],
    "description": "Power board replaced when measured values are not correct.",
    "name": "Power board"
  },
  "allowed_source_anchors": [
    "ev_2b470527670cfe12f9f7388f8b7f"
  ],
  "branch_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If no, replace the power board.",
        "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
        "source_page": 93
      }
    ],
    "description": "When the measured values are not correct, the troubleshooting branch directs replacement of the power board.",
    "material_context": null,
    "name": "Power board fault indicated by incorrect test values"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Are the values correct?",
          "source_anchor": "ev_297d962d2f2e7af9e54ef6d6fbc3",
          "source_page": 93
        }
      ],
      "code": null,
      "description": "The pin 16 of J7 measurement values are not correct.",
      "failure_link_evidence": [
        {
          "quote": "If no, replace the power board.",
          "source_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
          "source_page": 93
        }
      ],
      "kind": "symptom",
      "name": "Incorrect torch-start test values",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_2b470527670cfe12f9f7388f8b7f",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 24

ID: `dbranch_fc26ab020b6cceed7db0b1ca6b10dd3c746a5f44bf3b413020ab13c53c927e60`. Pagine: [61].

- Leaks or loose connections at pneumatic connection points → Leak or loose pneumatic connection → Repair or replace components

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
  "actions": [
    {
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_275a9b088354eecd0020e51aae04",
          "source_page": 61
        }
      ],
      "description": "Repair or replace affected components as necessary.",
      "instruction_text": "Repair or replace components as necessary.",
      "name": "Repair or replace components",
      "resolution_link_evidence": [
        {
          "quote": "Check for leaks and loose connections at each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
          "source_anchor": "ev_03198b788f62928494223d241fe0",
          "source_page": 61
        },
        {
          "quote": "Repair or replace components as necessary.",
          "source_anchor": "ev_275a9b088354eecd0020e51aae04",
          "source_page": 61
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Check for leaks and loose connections at each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
        "source_anchor": "ev_03198b788f62928494223d241fe0",
        "source_page": 61
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
        "source_anchor": "ev_03198b788f62928494223d241fe0",
        "source_page": 61
      }
    ],
    "description": "Air connection points at these internal components are checked for leaks and loose connections.",
    "name": "Pneumatic connection points on the internal compressor, air filter, and solenoid valve"
  },
  "allowed_source_anchors": [
    "ev_03198b788f62928494223d241fe0",
    "ev_275a9b088354eecd0020e51aae04"
  ],
  "branch_anchor": "ev_03198b788f62928494223d241fe0",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Check for leaks and loose connections at each pneumatic (air) connection point",
        "source_anchor": "ev_03198b788f62928494223d241fe0",
        "source_page": 61
      }
    ],
    "description": "A leak or loose connection is present at a pneumatic (air) connection point.",
    "material_context": null,
    "name": "Leak or loose pneumatic connection"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Check for leaks and loose connections at each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
          "source_anchor": "ev_03198b788f62928494223d241fe0",
          "source_page": 61
        }
      ],
      "code": null,
      "description": "Check for leaks and loose connections at each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
      "failure_link_evidence": [
        {
          "quote": "Check for leaks and loose connections at each pneumatic (air) connection point on the internal compressor, air filter, and solenoid valve.",
          "source_anchor": "ev_03198b788f62928494223d241fe0",
          "source_page": 61
        }
      ],
      "kind": "symptom",
      "name": "Leaks or loose connections at pneumatic connection points",
      "severity": "Low"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_03198b788f62928494223d241fe0",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 25

ID: `dbranch_fca8380cbfd644745661e08ae9766c5373eca051709d56af98373ecee0473585`. Pagine: [70].

- Internal compressor, temperature, and power ON LEDs blink, and torch cap LED illuminates → Inverter saturated (over-current condition) → Replace power board if error persists

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
  "actions": [
    {
      "action_kind": "replacement",
      "claim_evidence": [
        {
          "quote": "If you continue to see this error, replace the power board. See Replace the power board on page 135.",
          "source_anchor": "ev_3831faec4354524f9e26d695a99d",
          "source_page": 70
        }
      ],
      "description": "If the error continues, replace the power board.",
      "instruction_text": "If you continue to see this error, replace the power board. See Replace the power board on page 135.",
      "name": "Replace power board if error persists",
      "resolution_link_evidence": [
        {
          "quote": "If you continue to see this error, replace the power board.",
          "source_anchor": "ev_3831faec4354524f9e26d695a99d",
          "source_page": 70
        }
      ]
    }
  ],
  "affected_component": null,
  "allowed_source_anchors": [
    "ev_ae01749c40947bfcb624307d6fe2",
    "ev_e5dd1a11596e73a63405c3241028",
    "ev_3831faec4354524f9e26d695a99d"
  ],
  "branch_anchor": "ev_e5dd1a11596e73a63405c3241028",
  "failure": {
    "claim_evidence": [
      {
        "quote": "The inverter is saturated (is in an over-current condition).",
        "source_anchor": "ev_e5dd1a11596e73a63405c3241028",
        "source_page": 70
      }
    ],
    "description": "The inverter is saturated (is in an over-current condition).",
    "material_context": null,
    "name": "Inverter saturated (over-current condition)"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The internal compressor, temperature, and power ON LEDs blink, and the torch cap LED illuminates.",
          "source_anchor": "ev_ae01749c40947bfcb624307d6fe2",
          "source_page": 70
        }
      ],
      "code": null,
      "description": "The internal compressor, temperature, and power ON LEDs blink, and the torch cap LED illuminates.",
      "failure_link_evidence": [
        {
          "quote": "The inverter is saturated (is in an over-current condition).",
          "source_anchor": "ev_e5dd1a11596e73a63405c3241028",
          "source_page": 70
        }
      ],
      "kind": "symptom",
      "name": "Internal compressor, temperature, and power ON LEDs blink, and torch cap LED illuminates",
      "severity": "High"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_ae01749c40947bfcb624307d6fe2",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```
