# Confronto gold v2 con gold v1: Graco GTX 2000EX

Il gold v2 è fatto da un'AI (annotatore, verificatore e confronto con v1); manca una revisione umana.
Il gold v1 è manuale (Fabio Daniele, 2026-09-27) e copre solo le pagine 8-9 (tabella Troubleshooting).
Gold v1 letto solo in sola lettura; il PDF (testo e immagine di p8 e p9) ha deciso ogni differenza.

## Conteggi

- Rami v1: 19 (45 claim).
- Confermati: 16.
- Corretti (v2 diverso e supportato dal PDF): 3 (R10, R16, R19).
- Aggiunti a v2 dopo il confronto: 0.
- Non supportati dal PDF: 0 (ma R10 in v1 ha un'azione in più non stampata, vedi tabella).
- Elementi v2 senza controparte v1: 15
  - safety_precaution: 8
  - condition_maintenance: 2
  - procedure (extended): 4
  - routine (context): 1

Il gold v2 non è stato modificato: nessun ramo v1 manca in v2 e nessuna differenza dà ragione a v1.

## Rami v1

| v1 | problema (breve) | v2 | esito | nota |
|---|---|---|---|---|
| R1 | No material output / poca aria alla pompa | B011 | confermato | v1 divide la soluzione in 3 azioni, v2 in 2; stesso contenuto. |
| R2 | No material output / materiale troppo denso | B012 | confermato | |
| R3 | No material output / sfere o sedi danneggiate | B013 | confermato | |
| R4 | No material output / pistola o ugello intasati | B014 | confermato | v2 mette "If necessary" (dalla NOTE) come condizione del lavaggio; v1 lo ha nel testo. |
| R5 | No material output / tubo intasato o piccolo | B015 | confermato | v2 tiene "Flush hose ..., or try a 1-1/4 in. hose" come una azione con "or" (alternative), v1 in due. |
| R6 | Pump stops pumping / pompa in stallo | B016 | confermato | Due celle soluzione unite in un ramo, come v1. |
| R7 | Pump stops pumping / pompa da riparare | B018 | confermato | Rinvio al manuale 308479. |
| R8 | Pulsing or surging / grilletto troppo veloce | B019 | confermato | v1 divide la frase "while moving gun..." in due azioni; v2 una sola, come stampato. |
| R9 | Speed too slow / poca aria alla pompa | B020 | confermato | Come R1. |
| R10 | Speed too slow / materiale troppo denso | B021 | corretto | v1 aggiunge "Thin the material", che a p8 (riga t1.r12) non è stampato: la cella ha solo "Material must be mixed thoroughly...". v2 annota quanto scritto. |
| R11 | Speed too slow / ugello troppo piccolo | B022 | confermato | |
| R12 | Speed too slow / tubo intasato o piccolo | B023 | confermato | Come R5. |
| R13 | Speed too slow / pompa da riparare | B024 | confermato | |
| R14 | Pattern too fine / materiale troppo fluido | B025 | confermato | |
| R15 | Pattern too fine / aria alla pistola troppo alta | B026 | confermato | |
| R16 | Pattern too fine / portata fluido troppo bassa | B027 | corretto | Stesse 3 soluzioni; "See Spray Techniques in Operation Manual 309915" in v2 è un riferimento esterno (`references`), non un'azione di riparazione. |
| R17 | Pattern too coarse / materiale troppo denso | B030 | confermato | |
| R18 | Pattern too coarse / aria alla pistola troppo bassa | B031 | confermato | |
| R19 | Pattern too coarse / portata fluido troppo alta | B032 | corretto | Come R16. |

In v1 la frase "Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6" è
ripetuta come condizione in ogni ramo; in v2 è il ramo di sicurezza B010 (p8).

## Elementi v2 senza controparte v1

v1 annota solo p8-9; questi elementi sono su altre pagine (tranne B010, che v1 tiene come condizione).

- safety_precaution (8): B001, B002, B004 (p2); B006, B007, B008 (p3); B009 (p6); B010 (p8).
- condition_maintenance (2): B003, B005 (p2, controlli giornalieri con "repair or replace" se usurato).
- procedure (4): P002 Hopper Removal, P003 Install Hopper (p6); P004 Pump Removal, P005 Pump Installation (p7).
- routine (1): P001 Pressure Relief (p6).
