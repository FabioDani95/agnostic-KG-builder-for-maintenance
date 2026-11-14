# Gold v2 – LG LMH2235ST (manuale di servizio forno a microonde, 49 pagine)

## Che cos'è

Questo gold v2 è fatto da un'AI. Annotatori, verificatori e aggiudicatore sono AI (Claude Opus 5.5,
`claude-opus-5-5`), coordinati da Claude Fable 5.2 (`claude-fable-5-2`). Nessuna revisione umana finora.

Come è stato prodotto:
- quattro annotatori AI per intervalli di pagine (1-10, 11-23, 24-33, 34-49), poi unione con ID finali B###/P###;
- verifica indipendente AI in due intervalli (p1-23, p24-49), solo sugli elementi core ed extended;
- un secondo annotatore AI ha rifatto da zero il 25% delle pagine diagnostiche (p4, 15, 16, 22, 25, 31, 37, 39), solo core ed extended;
- aggiudicazione AI di ogni proposta sul PDF (testo e immagine, flowchart ingranditi a 170 dpi).
Il registro delle decisioni è in `adjudication.json` (cartella di lavoro dello scratchpad).

Risultato: 115 rami (117 dopo il confronto con v1), 17 procedure, 208 componenti, 3 codici, 28 domande; 16 elementi ambigui.

## Decisioni

- Flowchart (p14-23): un ramo per ogni percorso che arriva a una casella d'azione. Se due percorsi arrivano
  alla stessa casella con verifiche diverse, sono due rami. Per questo B045 è stato diviso (B113, B114) e
  B051-B053 sono stati divisi (B115-B117).
- I grafici sono annotati come stampati, senza correzioni. I rami che dipendono da errori del grafico sono `ambiguous`.
- "PCB no problem" e "Alternate explanation" senza azione di riparazione: i due "Alternate explanation" restano
  (B054, B065, con la Note come causa); "PCB no problem" non è un ramo.
- Lo SWITCH CHART di p4 (sezione Specifications) è una tabella di riferimento, non un test: rimosso (B012).
  Le stesse misure sono i test veri di p29 (B085-B087).
- P007 (tabella del test di continuità di p29) rimossa: duplicava B085-B087.
- P005 (misura della potenza d'uscita, p26) è routine: misura con formula, senza valore atteso né rimedio.
  Quindi p26 non è più diagnostica.
- P003 non è stata completata con il RECORD KEEPING di p25: quel testo è già la procedura routine P004.
- P006: l'introduzione di ADJUSTMENT PROCEDURES (p27.b5-b6) è nelle `conditions`; resta anche il ramo di sicurezza B082.
- Doppione tra pagine: il riquadro "Symptom: Dead / Check: Open/Short" sui termostati è uguale a p13 e p14.
  Resta un solo ramo (B037) con entrambe le pagine; B047 rimosso.
- Inventario: 20 componenti uniti con alias quando il manuale rende chiara l'identità (sigla dello schema,
  nome del troubleshooting, del test, dello smontaggio): ad esempio H.V. capacitor/high voltage capacitor,
  V.M./vent motor/ventilation motor, O.L./cavity lamp/oven lamp, MGT relay/relay 2, oven lamp relay/RY1,
  micom controller assembly/circuit board/PCB, magnetron seal/magnetron gasket, wave guide/waveguide.
- Esplosi p40-48: stampano solo numeri di posizione. Le voci restano "part NNNN", senza nomi inventati.
- Riferimenti: "section 9-1, 9-2" → P006; "section 10" → B095 (capacitor) e B096 (diode); "POWER OUTPUT
  MEASUREMENT on page 8" → P005; "ADJUSTMENT PROCEDURES on page 7-12" → P006 (PDF p27-28).

## Casi difficili

- p17 casella 5 "Replace the keypad?": è scritta come domanda e ha solo l'uscita No. B052/B116 la leggono come
  azione "sostituire il keypad"; B053/B117 seguono l'uscita No verso "Replace the PCB". Tutti ambigui.
- p19-20: il passo 5 "Power Off" di p20 non ha frecce in ingresso. Le caselle di p19 ("PCB no problem",
  "Replace the PCB") sono terminali. Il gold segue la numerazione (2 Yes → 5): B057-B064 ambigui.
- p21: passo 11 con YES/NO invertiti ("out of range?" No → sostituire il diodo); passo 12 senza uscita No.
- p23: il passo di RY1 è numerato "4" una seconda volta; "Replace the turntable motor" dopo la domanda sulla lampada.
- p25: limiti di fuga con parole mancanti (vedi sotto). B075 è ambiguo.

## Dubbi aperti

- Collegamento reale da p19 al passo 5 di p20: potrebbe partire anche dopo "Replace the PCB" (passo 4); non è stampato.
- "keypad" (p16-17) e "touch key board" (p33) sono probabilmente la stessa parte, ma il manuale non lo dice: non uniti.
- p23 passo 3 (lampada spenta → sostituire il motore del piatto) sembra un errore del manuale; annotato come stampato.
- Gli esiti di p13 (Basic Check Summary) non hanno valori attesi scritti.

## Errori o contraddizioni del manuale

- p25: "Leakage with the outer panels removed than 5 mW/cm2" (manca "less").
- p25 RECORD KEEPING (2): "Should the microwave energy leakage not be more than 1 mW/cm2" (probabilmente "more than").
  Entrambi annotati come stampati.
- p19-21: frecce mancanti tra p19 e p20, YES/NO invertiti al passo 11, passo 12 senza uscita No.
- p23: numero di passo "4" ripetuto.
- p17: casella 5 scritta come domanda.
- p4 "Bottom TCO 145/0" contro p9 "BOTTOM THERMOSTAT 150°C/0°C".
- Valori del trasformatore diversi: flowchart p20 primario 0.2-0.5 ohm e secondario 50-120 ohm; test p30 0.3-0.5 e 65-120 ohm.
- p11 rimanda alla POWER OUTPUT MEASUREMENT "on page 8" (è a PDF p26); p36 "page 7-12" = PDF p27; p34 "HOW TO
  REMOVE THE FPC CONNECTOR on the next page" non esiste; p28 intestazione "SPECIFICATIONS" residua.

## Verifica indipendente

- Elementi controllati: 79 (43 in p1-23, 36 in p24-49), solo core ed extended.
- ok: 59. Correzioni proposte: 19 (17 accettate, 1 accettata modificata: P006, 1 respinta: P003).
- Rimozioni proposte: 1 (P007, accettata). Mancanti proposti: 5 rami di flowchart, tutti accettati (B113-B117).
- Correzioni della mappa pagine: 5 (p15, 17, 21, 23 riscritte con gli ID finali; p26 non diagnostica).
- Respinta: l'aggiunta del RECORD KEEPING a P003, perché è già P004.
- Decisioni dell'aggiudicatore: B047 unito a B037; B012 rimosso (dal confronto col secondo annotatore); 20 unioni di componenti.
- Gli elementi di contesto (safety_precaution, routine: 52) sono annotati una sola volta e non sono verificati
  in modo indipendente. Nel gold: `"verification": {"independent_scopes": ["core", "extended"]}`.

## Accordo tra annotatori

- Pagine: 4, 15, 16, 22, 25, 31, 37, 39 (seme 20261113), solo elementi core ed extended, sul gold prima dell'aggiudicazione.
- Trovati da entrambi: 16 (p15: 4; p22: 4; p25: 1; p31: 4; p37: 2; p39: 1).
- Solo nel gold: 3 (B012 switch chart p4, P003 procedura di misura p25, B107 controllo fughe dopo il magnetron p37).
  I 5 rami Keypad Failure citano p16 solo per il titolo; il secondo annotatore non li ha annotati lì: non contati.
- Solo nel secondo annotatore: 2 (p15: percorsi 3 Yes "Check PCB" e 5 Yes verso "Replace the PCB").
- Classificati in modo diverso: 0.
- Differenze di contenuto nei rami trovati da entrambi: 2 (B045 fondeva tre percorsi; B075 contro due test separati b25-1/b25-2).
  Differenze solo di nome o di impaginazione (latch board/primary latch board, capacitor/high voltage capacitor,
  NOTES dentro l'ultimo passo) non contate.
- Decisioni sul PDF: i due percorsi in più di p15 accettati (B113, B114); B012 rimosso; P003 e B107 restano;
  B075 resta un solo test; p16 resta diagnostica.

## Limiti

- Tutto è fatto da AI (Claude Opus 5.5, coordinamento Claude Fable 5.2); nessuna revisione umana.
- safety_precaution e routine non sono verificati in modo indipendente.
- Le immagini dei flowchart hanno errori: alcune letture sono interpretazioni, marcate `ambiguous`.
- Gli esploso p40-48 non hanno nomi né codici: l'inventario lì contiene solo numeri di posizione.
- Il secondo annotatore copre il 25% delle pagine diagnostiche.

## Confronto con il gold v1

Confronto fatto da un'AI dopo la chiusura del gold v2; dettaglio in `CONFRONTO_V1.md`. Gold v1 non modificato.

- Rami v1: 74. Confermati 47, corretti 25 (v2 diverso e sostenuto dal PDF), aggiunti a v2 2, non supportati dal PDF 0.
- I corretti sono quasi tutti di granularità: un ramo per percorso di flowchart (No Display, Keypad, No Heat,
  Turntable, Turns on automatically), liste di passi come `procedures` (P002-P006), riquadri di sicurezza divisi
  per paragrafo. Gli esiti "PCB no problem" di v1 (R34, R48, R53) in v2 sono ispezioni dentro i percorsi.
- Differenza di contenuto: p21 passo 11 (diodo AT). Il PDF stampa "out of range? No -> Replace the high voltage
  Diode"; v2 (B063, ambiguous) segue la stampa, v1 la correggeva. Nessuna modifica.
- Aggiunti: B118 (p11, "Never operate the unit when it is empty", bicchiere d'acqua, piatto caldo) e B119 (p11,
  foglio di alluminio), entrambi `safety_precaution` con `added_after_v1_comparison: true`. p11 resta non diagnostica.
- Elementi v2 senza controparte v1: 46 (safety_precaution 28, procedure 11, diagnostic_test 3, routine 2,
  fault 2), quasi tutti su pagine che v1 non annotava.
- Totale dopo il confronto: 117 rami, 17 procedure.
