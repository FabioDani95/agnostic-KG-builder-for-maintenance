# Confronto prima/dopo della robustezza

Conteggi cumulati su tre esecuzioni, confrontate con lo stesso giudice aggiornato. C → D.

| Manuale | Rami | Asserzioni | Fusioni vietate | Cause orfane | Problemi senza azioni | Jaccard | Domande a persona (r1/r2/r3) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| abb_acs580_01 | 17/57 → 21/57 | 31/114 → 45/114 | 3 → 0 | 16 → 10 | 17 → 16 | 0.0657 → 0.0795 | 0/0/0 → 0/1/0 |
| atlascopco_drb_booster | 127/147 → 85/147 | 175/198 → 115/198 | 0 → 0 | 3 → 0 | 1 → 0 | 0.3643 → 0.133 | 0/0/0 → 0/0/0 |
| graco_gtx_2000ex | 51/57 → 51/57 | 129/135 → 129/135 | 0 → 0 | 0 → 0 | 0 → 0 | 0.5732 → 0.6053 | 0/0/0 → 0/0/0 |
| grundfos_paco_vl | 421/438 → 420/438 | 421/438 → 420/438 | 1 → 0 | 0 → 0 | 70 → 30 | 0.343 → 0.4203 | 0/0/0 → 0/0/0 |
| haas_mill_2023 | 101/135 → 93/135 | 118/171 → 109/171 | 1 → 0 | 12 → 24 | 62 → 71 | 0.0562 → 0.1109 | 0/1/0 → 0/0/0 |
| lincoln_powermig_215mp | 16/66 → 14/66 | 80/141 → 75/141 | 3 → 0 | 3 → 1 | 0 → 0 | 0.1071 → 0.1466 | 0/0/0 → 0/0/0 |

| Manuale | USD costruzione, 3 run C → D | Secondi pipeline, media C → D | Secondi PDF + pipeline, media D |
| --- | --- | --- | --- |
| abb_acs580_01 | 0.1137 → 0.1337 | 90.5 → 112.6 | 291.2 |
| atlascopco_drb_booster | 0.0567 → 0.0490 | 87.8 → 76.4 | 81.2 |
| graco_gtx_2000ex | 0.0278 → 0.0262 | 44.2 → 44.2 | 46.9 |
| grundfos_paco_vl | 0.0537 → 0.0488 | 73.0 → 72.3 | 75.5 |
| haas_mill_2023 | 0.0992 → 0.1230 | 105.6 → 118.0 | 129.6 |
| lincoln_powermig_215mp | 0.0495 → 0.0743 | 77.7 → 82.0 | 89.9 |

Il costo di costruzione esclude la valutazione dei KPI e il lavoro umano. Il tempo PDF non era registrato in C.

Recall macro (media dei sei manuali): {'before': 0.6681, 'after': 0.6169}.

Rami separati per presenza di azioni: {'before': {'with_actions': [260, 396], 'cause_only': [473, 504]}, 'after': {'with_actions': [209, 396], 'cause_only': [475, 504]}}.

Le coppie contrastive sono provvisorie fino alla revisione di Fabio. Nessuno di questi numeri stima la precisione semantica del grafo.
