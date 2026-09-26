# Misure della campagna di sviluppo

Generato da `scripts/analyze_extraction_experiment.py`. Il matching storico è un probe lessicale: non misura precisione o recall semantici validati. Un record pubblicabile non equivale a un ramo corretto completo.

| Run | Stato | Secondi | Chiamate | USD prudenziali | Nodi/relazioni | Rami nel grafo | Review | Probe storico autonomo |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| b1_eastman_e554 | failed | 1.081 | 0 | 0.000000 | / |  |  | — |
| b1r1_danfoss_apf | completed | 118.033 | 16 | 0.016786 | 36/35 | 0 | 24 | 0/8 |
| b1r1_eastman_e554 | completed | 283.807 | 21 | 0.030475 | 163/172 | 11 | 54 | 5/8 |
| b1r1_graco_check_mate_200 | completed | 115.842 | 15 | 0.016380 | 48/47 | 0 | 16 | 0/18 |
| b1r1_hypertherm_powermax30_air | completed | 793.881 | 63 | 0.088205 | 194/198 | 25 | 89 | — |
| c10_full_eastman_e554 | failed | 0.974 | 0 | 0.000000 | / |  |  | — |
| c10r1_full_eastman_e554 | failed | 1.147 | 0 | 0.000000 | / |  |  | — |
| c10r2_full_eastman_e554 | completed | 341.593 | 32 | 0.039695 | 186/191 | 14 | 78 | 6/8 |
| c11_full_danfoss_apf | completed | 110.729 | 18 | 0.015815 | 49/60 | 8 | 26 | 5/8 |
| c11_full_eastman_e554 | completed | 1013.237 | 33 | 0.052932 | 157/159 | 9 | 75 | 5/8 |
| c11_full_graco_check_mate_200 | completed | 161.615 | 24 | 0.021662 | 78/84 | 19 | 64 | 17/18 |
| c11_full_hypertherm_powermax30_air | completed | 1615.165 | 79 | 0.122362 | 164/168 | 17 | 151 | — |
| c1_danfoss_apf | completed | 131.946 | 18 | 0.016186 | 43/49 | 7 | 91 | 5/8 |
| c1_eastman_e554 | completed | 367.894 | 29 | 0.035074 | 164/171 | 12 | 96 | 7/8 |
| c1_graco_check_mate_200 | completed | 170.293 | 21 | 0.019456 | 102/108 | 27 | 47 | 15/18 |
| c1_hypertherm_powermax30_air | completed | 954.577 | 81 | 0.469812 | 169/170 | 16 | 132 | — |
| c2_danfoss_apf | completed | 147.18 | 21 | 0.016995 | 40/43 | 5 | 29 | 5/8 |
| c2_eastman_e554 | completed | 392.863 | 29 | 0.038416 | 164/167 | 12 | 78 | 4/8 |
| c2_graco_check_mate_200 | completed | 170.338 | 21 | 0.019478 | 85/84 | 20 | 40 | 17/18 |
| c2_hypertherm_powermax30_air | completed | 804.52 | 63 | 0.079695 | 139/139 | 10 | 117 | — |
| c7_hypertherm_powermax30_air | completed | 603.94 | 68 | 0.082306 | 153/154 | 17 | 111 | — |

Confronti su pacchetti (stessa fonte e codice P1, singola esecuzione per profilo):

| Run | Pagine | Pubblicabili | Irrisolti | USD |
|---|---|---:|---:|---:|
| c10p_eastman_low | 37,38,39 | 0 | 12 | 0.004329 |
| c10p_eastman_medium | 37,38,39 | 1 | 12 | 0.006396 |
| c10p_tables_low | 67,68,69 | 0 | 9 | 0.003117 |
| c10p_tables_medium | 67,68,69 | 0 | 10 | 0.004486 |
| c10p_test9_low_r1 | 96,97,98,99,100 | 4 | 2 | 0.002658 |
| c10p_test9_low_r2 | 96,97,98,99,100 | 3 | 2 | 0.003092 |
| c10p_test9_medium_r1 | 96,97,98,99,100 | 3 | 3 | 0.003945 |
| c10p_test9_medium_r2 | 96,97,98,99,100 | 0 | 6 | 0.003626 |
| c9p_test9_low_r1 | 96,97,98,99,100 | 0 | 6 | 0.003245 |
| c9p_test9_medium_r1 | 96,97,98,99,100 | 0 | 6 | 0.005673 |
| p1_danfoss_apf_luna_low8 | 64 | 5 | 3 | 0.001533 |
| p1_danfoss_apf_luna_none24 | 64 | 3 | 11 | 0.001689 |
| p1_danfoss_apf_sol_medium24 | 64 | 0 | 8 | 0.051866 |
| p1_danfoss_luna_low24 | 64 |  |  | 0.000000 |
| p1_eastman_e554_luna_low24 | 37,38,39 | 0 | 14 | 0.004157 |
| p1_eastman_e554_luna_low8 | 37,38,39 | 0 | 11 | 0.004598 |
| p1_eastman_e554_luna_none24 | 37,38,39 | 0 | 12 | 0.005308 |
| p1_eastman_e554_sol_medium24 | 37,38,39 | 0 | 23 | 0.126849 |
| p1_graco_check_mate_200_luna_low24 | 11 | 5 | 14 | 0.003421 |
| p1_graco_check_mate_200_luna_low8 | 11 | 3 | 16 | 0.003951 |
| p1_graco_check_mate_200_luna_none24 | 11 | 0 | 19 | 0.003319 |
| p1_graco_check_mate_200_sol_medium24 | 11 | 5 | 14 | 0.099078 |
| p1_hypertherm_powermax30_air_luna_low24 | 76,77 | 1 | 10 | 0.002432 |
| p1_hypertherm_powermax30_air_luna_low8 | 76,77 | 2 | 10 | 0.003020 |
| p1_hypertherm_powermax30_air_luna_none24 | 76,77 | 3 | 9 | 0.003344 |
| p1_hypertherm_powermax30_air_sol_medium24 | 76,77 | 2 | 8 | 0.098268 |
| p1r1_danfoss_luna_low24 | 64 |  |  | 0.000000 |
| p1r2_danfoss_luna_low24 | 64 | 5 | 3 | 0.001690 |

C3–C6 usano le stesse risposte C2 mediante replay offline a richiesta identica. Zero rete e zero nuova spesa: C3 isola normalizzazione/export, C4 aggiunge i controlli sulle ispezioni, C5 distingue le celle di sola ispezione interamente verificate, C6 separa completezza di elaborazione e completezza dell’estrazione. Non sono repliche LLM indipendenti e il loro tempo non è il tempo di estrazione.

| Replay | Nodi/relazioni | Rami nel grafo | Compilati persi nel grafo | Review | Probe storico autonomo | Ispezioni/condizioni conservate |
|---|---:|---:|---:|---:|---:|---:|
| c3r1_danfoss_apf (fonte: c2_danfoss_apf) | 40/43 | 5 | 0 | 29 | 5/8 | 6/0 |
| c3r1_eastman_e554 (fonte: c2_eastman_e554) | 164/167 | 12 | 0 | 78 | 4/8 | 48/30 |
| c3r1_graco_check_mate_200 (fonte: c2_graco_check_mate_200) | 86/88 | 22 | 0 | 40 | 17/18 | 2/0 |
| c3r1_hypertherm_powermax30_air (fonte: c2_hypertherm_powermax30_air) | 139/139 | 10 | 0 | 117 | — | 24/35 |
| c4r1_danfoss_apf (fonte: c2_danfoss_apf) | 40/43 | 5 | 0 | 29 | 5/8 | 6/0 |
| c4r1_eastman_e554 (fonte: c2_eastman_e554) | 153/157 | 9 | 0 | 80 | 4/8 | 48/29 |
| c4r1_graco_check_mate_200 (fonte: c2_graco_check_mate_200) | 86/88 | 22 | 0 | 40 | 17/18 | 2/0 |
| c4r1_hypertherm_powermax30_air (fonte: c2_hypertherm_powermax30_air) | 139/139 | 10 | 0 | 117 | — | 24/35 |
| c5r1_danfoss_apf (fonte: c2_danfoss_apf) | 40/43 | 5 | 0 | 28 | 5/8 | 6/0 |
| c5r1_eastman_e554 (fonte: c2_eastman_e554) | 153/157 | 9 | 0 | 80 | 4/8 | 48/29 |
| c5r1_graco_check_mate_200 (fonte: c2_graco_check_mate_200) | 86/88 | 22 | 0 | 39 | 17/18 | 2/0 |
| c5r1_hypertherm_powermax30_air (fonte: c2_hypertherm_powermax30_air) | 139/139 | 10 | 0 | 117 | — | 24/35 |
| c6r1_danfoss_apf (fonte: c2_danfoss_apf) | 40/43 | 5 | 0 | 28 | 5/8 | 6/0 |
| c6r1_eastman_e554 (fonte: c2_eastman_e554) | 153/157 | 9 | 0 | 80 | 4/8 | 48/29 |
| c6r1_graco_check_mate_200 (fonte: c2_graco_check_mate_200) | 86/88 | 22 | 0 | 39 | 17/18 | 2/0 |
| c6r1_hypertherm_powermax30_air (fonte: c2_hypertherm_powermax30_air) | 139/139 | 10 | 0 | 117 | — | 24/35 |
| c8r1_danfoss_apf (fonte: c2_danfoss_apf) | 40/43 | 5 | 0 | 28 | 5/8 | 6/0 |
| c8r1_eastman_e554 (fonte: c2_eastman_e554) | 153/157 | 9 | 0 | 80 | 4/8 | 48/29 |
| c8r1_graco_check_mate_200 (fonte: c2_graco_check_mate_200) | 86/88 | 22 | 0 | 39 | 17/18 | 2/0 |
| c8r1_hypertherm_powermax30_air (fonte: c7_hypertherm_powermax30_air) | 153/154 | 17 | 0 | 111 | — | 28/29 |

Budget cumulativo (stima prudenziale, non fattura):

```json
{
  "cap_usd": 20,
  "calls_reserved": 678,
  "calls_finalized": 678,
  "charged_usd": 1.636820045,
  "observed_estimated_usd": 1.20521167,
  "unknown_usage_calls": 30,
  "all_reservations_within_cap": true,
  "no_envelope_breaches": true,
  "active_calls": []
}
```

B1 e C2 eseguono i manuali in sequenza; C1 ne esegue fino a due insieme. Ogni manuale usa concorrenza interna per chunk. I tempi sono monotonic elapsed del runner; non dedurre velocità causali da singole repliche o dagli orologi UTC, che hanno mostrato discontinuità nell'ambiente.

La corrispondenza letterale delle evidenze è controllata contro le EvidenceUnit SQLite originali. Non certifica il significato della relazione. Il gold storico non è stato modificato; Hypertherm non dispone ancora di gold tecnico. Le predizioni e i moduli di scoring restano separati dalla produzione.
