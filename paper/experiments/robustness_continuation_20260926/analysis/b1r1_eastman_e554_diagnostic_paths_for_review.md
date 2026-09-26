# Catene estratte da verificare

Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.

## Ramo 1

ID: `dbranch_01f44924cb203a39a9e42a505ff3e34dd3df4279ae88f32309c13ce9b80131f8`. Pagine: [39].

- Laser cutting path is too wide → Damage to brass laser nozzle → Replace nozzle

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage to brass laser nozzle.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage to brass laser nozzle."
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
          "quote": "Replace nozzle if any damage is present.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ],
      "description": "Replace the brass laser nozzle if damage is present.",
      "instruction_text": "Replace nozzle if any damage is present.",
      "name": "Replace nozzle",
      "resolution_link_evidence": [
        {
          "quote": "Check for damage to brass laser nozzle. Replace nozzle if any damage is present.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Check for damage to brass laser nozzle. Replace nozzle if any damage is present.",
        "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "brass laser nozzle",
        "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
        "source_page": 39
      }
    ],
    "description": "Brass laser nozzle checked for damage and replaced if damaged.",
    "name": "brass laser nozzle"
  },
  "allowed_source_anchors": [
    "ev_b7ffa9e31a9f32dcde87b819f11d",
    "ev_6d1f15fff63937eb68d2772a5ff7"
  ],
  "branch_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Check for damage to brass laser nozzle.",
        "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
        "source_page": 39
      }
    ],
    "description": "The brass laser nozzle is damaged.",
    "material_context": null,
    "name": "Damage to brass laser nozzle"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Problem: Laser cutting path is too wide",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        },
        {
          "quote": "The laser cutting path increases to an undesirable width.",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting path increases to an undesirable width.",
      "failure_link_evidence": [
        {
          "quote": "Problem: Laser cutting path is too wide",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        },
        {
          "quote": "Check for damage to brass laser nozzle.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Laser cutting path is too wide",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage to brass laser nozzle.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage to brass laser nozzle."
    }
  ],
  "record_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 2

ID: `dbranch_07c4f8ea09ec8c9475002fefc5f64af1bf59a8389f5183a6bbe9b7d0a6ce43c3`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty mirror → Clean or replace mirrors

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors."
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
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Clean or replace mirrors as required.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "description": "Clean or replace mirrors as required.",
      "instruction_text": "Clean or replace mirrors as required.",
      "name": "Clean or replace mirrors",
      "resolution_link_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damaged or dirty Mirror. Check for damage, burn mark or dirt on the beam deflecting mirrors. Clean or replace mirrors as required.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Damaged or dirty Mirror. Check for damage, burn mark or dirt on the beam deflecting mirrors.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "beam deflecting mirrors.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "description": "Mirrors that deflect the laser beam.",
    "name": "beam deflecting mirrors"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_b5d4d85f89b332aa8057124c0fa0"
  ],
  "branch_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damaged or dirty Mirror.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "description": "Damaged, burned, or dirty beam-deflecting mirrors.",
    "material_context": null,
    "name": "Damaged or dirty mirror"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Damaged or dirty Mirror.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "High"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 3

ID: `dbranch_0f96656779e05d59052cb1ebb1030c08ee3423d4e96ad3ed6a4fa3ac745c7929`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty lens → Clean or replace lens

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or dirt on the focusing lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or dirt on the focusing lens."
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
      "action_kind": "cleaning_or_replacement",
      "claim_evidence": [
        {
          "quote": "Clean or replace lens as required.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "description": "Clean or replace the focusing lens as required.",
      "instruction_text": "Clean or replace lens as required.",
      "name": "Clean or replace lens",
      "resolution_link_evidence": [
        {
          "quote": "Check for damage or dirt on the focusing lens. Clean or replace lens as required.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Check for damage or dirt on the focusing lens. Clean or replace lens as required.",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "the focusing lens",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "description": "The focusing lens may be damaged or dirty.",
    "name": "focusing lens"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_c4a2878086674ae265f7203c7b7e"
  ],
  "branch_anchor": "ev_c4a2878086674ae265f7203c7b7e",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damaged or dirty lens.",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "description": "The focusing lens is damaged or dirty.",
    "material_context": null,
    "name": "Damaged or dirty lens"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damaged or dirty lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or dirt on the focusing lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or dirt on the focusing lens."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 4

ID: `dbranch_24758efc57802ed1ec1e52f20f236a95ab1bc7c54cefa0a145f35b5caccd6609`. Pagine: [37].

- Machine Stop during Cut Due to Unintentional pause → Intermittent pause circuit → Adjust pause plunger activation pressure

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check stop disc activation.",
          "source_anchor": "ev_081695295bc5450ab1a01f5ec0eb",
          "source_page": 37
        }
      ],
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure. Remove gantry side cover. Check the pause plunger."
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
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "source_anchor": "ev_081695295bc5450ab1a01f5ec0eb",
          "source_page": 37
        }
      ],
      "description": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
      "instruction_text": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
      "name": "Adjust pause plunger activation pressure",
      "resolution_link_evidence": [
        {
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "source_anchor": "ev_a595f77c91ac64594b89551c661a",
          "source_page": 37
        },
        {
          "quote": "Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.",
          "source_anchor": "ev_081695295bc5450ab1a01f5ec0eb",
          "source_page": 37
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "usually in thestop discs.",
        "source_anchor": "ev_a595f77c91ac64594b89551c661a",
        "source_page": 37
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "usually in thestop discs.",
        "source_anchor": "ev_a595f77c91ac64594b89551c661a",
        "source_page": 37
      }
    ],
    "description": "Stop discs in the pause circuit.",
    "name": "stop discs"
  },
  "allowed_source_anchors": [
    "ev_a595f77c91ac64594b89551c661a",
    "ev_081695295bc5450ab1a01f5ec0eb"
  ],
  "branch_anchor": "ev_a595f77c91ac64594b89551c661a",
  "failure": {
    "claim_evidence": [
      {
        "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
        "source_anchor": "ev_a595f77c91ac64594b89551c661a",
        "source_page": 37
      }
    ],
    "description": "Intermittent pause circuit, usually in the stop discs.",
    "material_context": null,
    "name": "Intermittent pause circuit"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The machine stops in middle of cut and displays message",
          "source_anchor": "ev_a595f77c91ac64594b89551c661a",
          "source_page": 37
        }
      ],
      "code": null,
      "description": "The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen.",
      "failure_link_evidence": [
        {
          "quote": "This is typically caused by an intermittent pause circuit, usually in thestop discs.",
          "source_anchor": "ev_a595f77c91ac64594b89551c661a",
          "source_page": 37
        }
      ],
      "kind": "symptom",
      "name": "Machine Stop during Cut Due to Unintentional pause",
      "severity": "High"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check stop disc activation.",
          "source_anchor": "ev_081695295bc5450ab1a01f5ec0eb",
          "source_page": 37
        }
      ],
      "instruction_text": "Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure. Remove gantry side cover. Check the pause plunger."
    }
  ],
  "record_anchor": "ev_a595f77c91ac64594b89551c661a",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 5

ID: `dbranch_336655119c2dbd0646c954b34ad1eceadb6d358a45e690bf1a5e238e530add6b`. Pagine: [39].

- Loss of laser cutting power → Damage or debris in laser nozzle → Clean or replace laser nozzle

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or debris in laser nozzle."
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
      "action_kind": "cleaning_or_replacement",
      "claim_evidence": [
        {
          "quote": "Clean or replace laser nozzle as required.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "description": "Clean or replace the laser nozzle as required.",
      "instruction_text": "Clean or replace laser nozzle as required.",
      "name": "Clean or replace laser nozzle",
      "resolution_link_evidence": [
        {
          "quote": "Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "laser nozzle",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "description": "The laser nozzle may be damaged or contain debris.",
    "name": "laser nozzle"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_2fa59a389deb088d889cc1c93021"
  ],
  "branch_anchor": "ev_2fa59a389deb088d889cc1c93021",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damage or debris in laser nozzle.",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "description": "The laser nozzle is damaged or contains debris.",
    "material_context": null,
    "name": "Damage or debris in laser nozzle"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or debris in laser nozzle."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 6

ID: `dbranch_415324d8b802171056357a19328adebe8c8d0b4c67634e2dbc8720b098a565cf`. Pagine: [39].

- Laser cutting path is too wide → Bent tube or nozzle → Adjust mirrors

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for brass laser nozzle alignment.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        },
        {
          "quote": "To verify, perform a test pulse on a piece of card board.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        },
        {
          "quote": "If the dot has a ring or partial ring around it",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "instruction_text": "Check brass laser nozzle alignment. Perform a test pulse on a piece of card board; a dot with a ring or partial ring indicates the nuzzle is bent or the mirrors may need adjustment."
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
          "quote": "the mirrors may need to be adjusted.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "description": "The mirrors may need adjustment if the test pulse shows a ring or partial ring.",
      "instruction_text": "the mirrors may need to be adjusted.",
      "name": "Adjust mirrors",
      "resolution_link_evidence": [
        {
          "quote": "If the dot has a ring or partial ring around it, the nuzzle is bent or the mirrors may need to be adjusted.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If the tube or nozzle is bent,  the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
        "source_anchor": "ev_3161767650d403954070248e58a9",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "If the tube or nozzle is bent",
        "source_anchor": "ev_3161767650d403954070248e58a9",
        "source_page": 39
      }
    ],
    "description": "The tube or nozzle may be bent, affecting beam reflection and cutting path.",
    "name": "brass laser nozzle"
  },
  "allowed_source_anchors": [
    "ev_b7ffa9e31a9f32dcde87b819f11d",
    "ev_3161767650d403954070248e58a9"
  ],
  "branch_anchor": "ev_3161767650d403954070248e58a9",
  "failure": {
    "claim_evidence": [
      {
        "quote": "If the tube or nozzle is bent,  the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
        "source_anchor": "ev_3161767650d403954070248e58a9",
        "source_page": 39
      }
    ],
    "description": "A bent tube or nozzle causes the laser beam to reflect off the inside wall of the nozzle, resulting in a wide path.",
    "material_context": null,
    "name": "Bent tube or nozzle"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Problem: Laser cutting path is too wide",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        },
        {
          "quote": "The laser cutting path increases to an undesirable width.",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting path increases to an undesirable width.",
      "failure_link_evidence": [
        {
          "quote": "Problem: Laser cutting path is too wide",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        },
        {
          "quote": "If the tube or nozzle is bent,  the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Laser cutting path is too wide",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for brass laser nozzle alignment.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        },
        {
          "quote": "To verify, perform a test pulse on a piece of card board.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        },
        {
          "quote": "If the dot has a ring or partial ring around it",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "instruction_text": "Check brass laser nozzle alignment. Perform a test pulse on a piece of card board; a dot with a ring or partial ring indicates the nuzzle is bent or the mirrors may need adjustment."
    }
  ],
  "record_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 7

ID: `dbranch_4eaa3d9e04142c5957d31e29b80f6935268cf0fa4675b78a9f2f4bc7f9aeb995`. Pagine: [39].

- Laser cutting path is too wide → Damaged or bent brass laser nozzle → Replace damaged nozzle

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "To verify, perform a test pulse on a piece of card board.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for brass laser nozzle alignment. Perform a test pulse on a piece of card board to verify."
    },
    {
      "claim_evidence": [
        {
          "quote": "Check laser power and cutting speed.",
          "source_anchor": "ev_2c83db99f292156e3cac0c547789",
          "source_page": 39
        }
      ],
      "instruction_text": "Check laser power and cutting speed. Settings may vary when changing materials. Testing will yield best results."
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
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Replace nozzle if any damage is present.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ],
      "description": "Replace nozzle if any damage is present.",
      "instruction_text": "Replace nozzle if any damage is present.",
      "name": "Replace damaged nozzle",
      "resolution_link_evidence": [
        {
          "quote": "Check for damage to brass laser nozzle. Replace nozzle if any damage is present.",
          "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "If the tube or nozzle is bent, the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
        "source_anchor": "ev_3161767650d403954070248e58a9",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "brass laser nozzle.",
        "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
        "source_page": 39
      }
    ],
    "description": "Brass laser nozzle whose damage or bending can cause a wide laser path.",
    "name": "brass laser nozzle"
  },
  "allowed_source_anchors": [
    "ev_b7ffa9e31a9f32dcde87b819f11d",
    "ev_6d1f15fff63937eb68d2772a5ff7",
    "ev_3161767650d403954070248e58a9",
    "ev_2c83db99f292156e3cac0c547789"
  ],
  "branch_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Check for damage to brass laser nozzle.",
        "source_anchor": "ev_6d1f15fff63937eb68d2772a5ff7",
        "source_page": 39
      },
      {
        "quote": "If the tube or nozzle is bent, the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
        "source_anchor": "ev_3161767650d403954070248e58a9",
        "source_page": 39
      }
    ],
    "description": "A damaged nozzle should be replaced; a bent tube or nozzle causes the laser beam to reflect off the inside wall of the nozzle, causing a wide path.",
    "material_context": null,
    "name": "Damaged or bent brass laser nozzle"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The laser cutting path increases to an undesirable width.",
          "source_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting path increases to an undesirable width.",
      "failure_link_evidence": [
        {
          "quote": "If the tube or nozzle is bent, the laser beam will reflect off the inside wall of the nozzle causing a wide path.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Laser cutting path is too wide",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "To verify, perform a test pulse on a piece of card board.",
          "source_anchor": "ev_3161767650d403954070248e58a9",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for brass laser nozzle alignment. Perform a test pulse on a piece of card board to verify."
    },
    {
      "claim_evidence": [
        {
          "quote": "Check laser power and cutting speed.",
          "source_anchor": "ev_2c83db99f292156e3cac0c547789",
          "source_page": 39
        }
      ],
      "instruction_text": "Check laser power and cutting speed. Settings may vary when changing materials. Testing will yield best results."
    }
  ],
  "record_anchor": "ev_b7ffa9e31a9f32dcde87b819f11d",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 8

ID: `dbranch_5841a25afc1fed608b585ca843b7895dff6712b291fbc5ed36219a39285a4bb1`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty lens → Clean or replace lens

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or dirt on the focusing lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or dirt on the focusing lens."
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
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Clean or replace lens as required.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "description": "Clean or replace lens as required.",
      "instruction_text": "Clean or replace lens as required.",
      "name": "Clean or replace lens",
      "resolution_link_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damaged or dirty lens. Check for damage or dirt on the focusing lens. Clean or replace lens as required.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Damaged or dirty lens. Check for damage or dirt on the focusing lens.",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "focusing lens.",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "description": "Focusing lens in the laser optical path.",
    "name": "focusing lens"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_c4a2878086674ae265f7203c7b7e",
    "ev_b5d4d85f89b332aa8057124c0fa0",
    "ev_2fa59a389deb088d889cc1c93021"
  ],
  "branch_anchor": "ev_c4a2878086674ae265f7203c7b7e",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damaged or dirty lens.",
        "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
        "source_page": 39
      }
    ],
    "description": "Damaged or dirty focusing lens.",
    "material_context": null,
    "name": "Damaged or dirty lens"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Damaged or dirty lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "High"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or dirt on the focusing lens.",
          "source_anchor": "ev_c4a2878086674ae265f7203c7b7e",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or dirt on the focusing lens."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 9

ID: `dbranch_80cca144968667c84ffd6f7c22e914825db08c5cdcd80bd2c82d181a820b5eef`. Pagine: [13].

- Electronic controls may malfunction → High levels of RF emissions → Keep RF-emitting equipment at least 70 feet away

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
          "quote": "this equipment be kept at least 70 feet away from the Eastman cutting system",
          "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
          "source_page": 13
        }
      ],
      "description": "Keep RF welders or other equipment that emits RF at least 70 feet away from the Eastman cutting system.",
      "instruction_text": "this equipment be kept at least 70 feet away from the Eastman cutting system",
      "name": "Keep RF-emitting equipment at least 70 feet away",
      "resolution_link_evidence": [
        {
          "quote": "High levels of RF emissions may cause the electronic controls in the system to malfunction.",
          "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
          "source_page": 13
        },
        {
          "quote": "this equipment be kept at least 70 feet away from the Eastman cutting system",
          "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
          "source_page": 13
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "High levels of RF emissions may cause the electronic controls in the system to malfunction.",
        "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
        "source_page": 13
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "electronic controls in the system",
        "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
        "source_page": 13
      }
    ],
    "description": "Electronic controls in the system may malfunction due to high levels of RF emissions.",
    "name": "Electronic controls"
  },
  "allowed_source_anchors": [
    "ev_5d853636fd0ed3c66e6b8f3b694a"
  ],
  "branch_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
  "failure": {
    "claim_evidence": [
      {
        "quote": "High levels of RF emissions",
        "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
        "source_page": 13
      }
    ],
    "description": "RF emissions from RF welders or other equipment may interfere with the system when equipment is not kept at least 70 feet away.",
    "material_context": null,
    "name": "High levels of RF emissions"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "may cause the electronic controls in the system to malfunction",
          "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
          "source_page": 13
        }
      ],
      "code": null,
      "description": "High levels of RF emissions may cause the electronic controls in the system to malfunction.",
      "failure_link_evidence": [
        {
          "quote": "High levels of RF emissions may cause the electronic controls in the system to malfunction.",
          "source_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
          "source_page": 13
        }
      ],
      "kind": "symptom",
      "name": "Electronic controls may malfunction",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [],
  "record_anchor": "ev_5d853636fd0ed3c66e6b8f3b694a",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 10

ID: `dbranch_9bebaa65c0c40cf51b881da72d719841bbf7cdabec9acd770a16bd44ba80006f`. Pagine: [39].

- Loss of laser cutting power → Damaged or dirty mirror → Clean or replace mirrors

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors."
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
      "action_kind": "cleaning_or_replacement",
      "claim_evidence": [
        {
          "quote": "Clean or replace mirrors as required.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "description": "Clean or replace the mirrors as required.",
      "instruction_text": "Clean or replace mirrors as required.",
      "name": "Clean or replace mirrors",
      "resolution_link_evidence": [
        {
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors. Clean or replace mirrors as required.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors. Clean or replace mirrors as required.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "beam deflecting mirrors",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "description": "The mirrors may have damage, burn marks, or dirt.",
    "name": "beam deflecting mirrors"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_b5d4d85f89b332aa8057124c0fa0"
  ],
  "branch_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damaged or dirty Mirror.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      },
      {
        "quote": "damage, burn mark or dirt on the beam deflecting mirrors.",
        "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
        "source_page": 39
      }
    ],
    "description": "A beam-deflecting mirror is damaged, has a burn mark, or is dirty.",
    "material_context": null,
    "name": "Damaged or dirty mirror"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Problem: Loss of laser cutting power",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damaged or dirty Mirror.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "Medium"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage, burn mark or dirt on the beam deflecting mirrors.",
          "source_anchor": "ev_b5d4d85f89b332aa8057124c0fa0",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage, burn mark or dirt on the beam deflecting mirrors."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```

## Ramo 11

ID: `dbranch_a0b3786bd6492f3be8465d045a43c1ef51bf7b152e31facdf313147fe4989ba5`. Pagine: [39].

- Loss of laser cutting power → Damage or debris in laser nozzle → Clean or replace laser nozzle

Ispezioni e condizioni:

```json
{
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or debris in laser nozzle."
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
      "action_kind": null,
      "claim_evidence": [
        {
          "quote": "Clean or replace laser nozzle as required.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "description": "Clean or replace laser nozzle as required.",
      "instruction_text": "Clean or replace laser nozzle as required.",
      "name": "Clean or replace laser nozzle",
      "resolution_link_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        },
        {
          "quote": "Damage or debris in laser nozzle. Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ]
    }
  ],
  "affected_component": {
    "affects_link_evidence": [
      {
        "quote": "Damage or debris in laser nozzle.",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "category": null,
    "claim_evidence": [
      {
        "quote": "laser nozzle.",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "description": "Laser nozzle that may be damaged or contain debris.",
    "name": "laser nozzle"
  },
  "allowed_source_anchors": [
    "ev_9b8be4f034c9c0a1691251414b6c",
    "ev_2fa59a389deb088d889cc1c93021"
  ],
  "branch_anchor": "ev_2fa59a389deb088d889cc1c93021",
  "failure": {
    "claim_evidence": [
      {
        "quote": "Damage or debris in laser nozzle.",
        "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
        "source_page": 39
      }
    ],
    "description": "Damage or debris in the laser nozzle.",
    "material_context": null,
    "name": "Damage or debris in laser nozzle"
  },
  "indicators": [
    {
      "claim_evidence": [
        {
          "quote": "The laser cutting power decreases causing non-cut edges.",
          "source_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
          "source_page": 39
        }
      ],
      "code": null,
      "description": "The laser cutting power decreases causing non-cut edges.",
      "failure_link_evidence": [
        {
          "quote": "Damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "kind": "symptom",
      "name": "Loss of laser cutting power",
      "severity": "High"
    }
  ],
  "inspection_steps": [
    {
      "claim_evidence": [
        {
          "quote": "Check for damage or debris in laser nozzle.",
          "source_anchor": "ev_2fa59a389deb088d889cc1c93021",
          "source_page": 39
        }
      ],
      "instruction_text": "Check for damage or debris in laser nozzle."
    }
  ],
  "record_anchor": "ev_9b8be4f034c9c0a1691251414b6c",
  "record_window_id": "",
  "resolution_status": "action_stated"
}
```
