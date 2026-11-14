# Gold v2: grizzly_g0872 (Grizzly G0872 CNC laser cutter/engraver)

## Che cos'è

Questo è il gold v2 del manuale Grizzly G0872 (80 pagine PDF; pagina stampata = pagina PDF - 2).
È fatto interamente da un'AI. Annotatori, verificatori e aggiudicatore sono claude-opus-5-5 (Claude Opus 5.5);
il coordinamento è di claude-fable-5-2 (Claude Fable 5.2). **Nessuna revisione umana**, per ora.

Come è stato prodotto:

1. Quattro annotatori AI, uno per intervallo di pagine (1-27, 28-50, 51-63, 64-80), hanno letto testo e immagini
   di ogni pagina e scritto gli item secondo la guida di annotazione.
2. Quattro verificatori AI indipendenti hanno ricontrollato sul PDF gli item core ed extended e l'inventario dei
   parts list.
3. Un secondo annotatore AI ha annotato da zero il 25% delle pagine diagnostiche (solo core ed extended).
4. Un aggiudicatore AI ha deciso ogni proposta sul PDF, unito i duplicati tra intervalli, completato inventario,
   entità e domande. Il registro delle decisioni è fuori dal repository (scratch di lavoro).

Totale finale: 245 rami, 28 procedure (7 di riparazione, 21 routine), 279 componenti, 4 codici, 28 domande.

## Decisioni

- Le liste di passi di installazione, uso e manutenzione periodica sono `routine`. Le loro frasi condizionali
  ("replace as required", "if contaminated") sono rami `condition_maintenance` separati.
- I riquadri di sicurezza generici senza un guasto della macchina sono `safety_precaution`, anche se hanno la
  forma "se X allora Y": EXPERIENCING DIFFICULTIES (p13, p15), materiali che prendono fuoco (p14), dubbio sulla
  messa a terra (p17).
- I requisiti di installazione sono `routine`: circuito non conforme (p16), climi desertici (p23), ispezione
  delle parti mobili prima e dopo l'uso (p43).
- Restano item diagnostici i riquadri con un guasto osservabile e un rimedio: DAMAGED PARTS (p13, B026),
  filtrazione o scarico malfunzionante (p15, B040), WIRE/COMPONENT DAMAGE (p64, B243, riclassificato da safety a
  condition_maintenance per coerenza con B026).
- I quattro codici (Frame Slop, Name Over Lap, XSlop Over, YSlop Over) erano annotati due volte: dal glossario
  (p9) e dalle pagine operative (p35, p40). Il glossario dà solo il significato, già contenuto nell'item
  operativo. Tenuto un item per codice (B098, B108, B109, B110) con le evidenze di entrambe le pagine; rimossi
  B002-B005.
- Il riquadro "DO NOT start machine until all preceding setup instructions..." è uguale a p26 e p28: un solo
  item (B086), rimosso B092.
- Inventario: unite 36 voci dello stesso pezzo con nomi diversi tra testo e parts list (es. "amp meter" ->
  "ammeter", "digital readout" -> "control panel", "z-axis timing belt" -> "z-axis belt", "high voltage power
  supply" -> "laser tube power supply"). Il nome canonico è quello del testo, il part number quello del parts
  list. Le cinghie X e Y hanno lo stesso part number (X/Y-AXIS TIMING BELT).
- Part number: per laser tube, water chiller, air pump, exhaust fan e honeycomb table vale il codice del parts
  list (P0872xxx). I codici T30342, T30337, T30335, T30336, T30334 di p41 sono codici di catalogo degli accessori.

## Casi difficili

- B235 (allineamento, angolo inferiore destro): aggiunti "Repeat Step 27" e il serraggio dei controdadi
  (step 31), dopo il confronto con il secondo annotatore.
- B074 (bolle d'aria nel tubo, p23): il manuale scrive solo lo scopo "to release air bubbles"; tenuto
  condition_maintenance senza la condizione "se non sono uscite".
- B141 (testa che si ferma se spostata a mano): causa elettrica (carica del motore passo-passo) scritta nel manuale.
- Le verifiche dentro Installing Laser Tube (p57-58) non dicono cosa fare se l'esito è negativo: restano solo
  passi della procedura P025 (rimossi B223, B228).

## Dubbi aperti

- B058, B062, B063 (merce danneggiata o mancante al disimballo) restano fault; si potrebbero considerare routine.
- Alcune voci del testo non sono legate con certezza al parts list e restano separate: x-axis/y-axis limit switch
  (due modelli nel parts list senza asse), front loading door e locking left loading door (LOADING DOOR SIDE e
  BOTTOM), computer board (forse il controller), brass thumbscrews (forse knurled thumb screw), removable panel
  (forse access panel), power cord (ref 310) (non si sa di quale accessorio).
- La misura di terra <= 5 Ohm (p17) è dentro la routine B051 e non è un diagnostic_test: il manuale non dice cosa
  fare se il valore è diverso.

## Errori o contraddizioni del manuale

- p56 step 24: "cap screws removed in Step 3 on Page 54" rimanda alla pagina sbagliata (lo Step 3 è a pagina
  stampata 52 = PDF 54; pagina 54 stampata = PDF 56).
- p52 "Inspect/adjust table parallelism (Page 52)": la pagina indicata ha solo la nota sulla cinghia Z (squadra
  della tavola).
- p59 step 10 "Highlight MaxPower 1" nel menu Min Power: probabile refuso.
- Titolo del rimando "Laser Optics Removal/Installation" (p48) diverso dal titolo reale a p63 ("Remove and Replace
  Mirrors/Focus Lens").
- "Frame Slop" (p9) e "Frame slop" (p40); p41 scrive "Air Pumo".

## Verifica indipendente

Verificati solo gli item core ed extended (113 item) e l'inventario dei parts list (160 voci con part number).
Gli item context (safety_precaution, routine) sono stati annotati una sola volta e **non sono stati verificati in
modo indipendente**.

- ok: 92; da correggere: 17 (tutte accettate); da rimuovere: 4 (tutte accettate: B150, B151, B223, B228);
  mancanti proposti: 1 (respinto).
- Correzioni di pagina (diagnostica sì/no): 5, 4 accettate e 1 modificata (p17 resta diagnostica per B055).
- Correzioni d'inventario: 8, tutte accettate (5 part number, 2 part_of, 1 alias in collisione).
- 7 item core/extended riclassificati context (B028, B032, B046, B054 safety; B047, B073, B139 routine).
- Respinto: m17-1 (resistenza di terra come diagnostic_test), perché è già nella routine B051 e il manuale non dà
  un rimedio per un valore sbagliato.

## Accordo tra annotatori

Pagine (seme 20261113): 9, 13, 15, 16, 23, 27, 49, 55, 62, 63. Confronto solo su item core ed extended, sul gold
prima dell'aggiudicazione.

- Item gold: 26; item del secondo annotatore: 17.
- Trovati da entrambi: 17 (4 codici p9, guarnizioni p15, 4 test del Test Run p27, 5 controlli chiller/pompa
  aria p49, allineamento p62, 2 procedure p63).
- Solo gold: 9. Quattro (B028, B046, B047, B073) sono stati poi riclassificati context dal verificatore, in
  accordo col secondo annotatore. Due (P024, P026) sono procedure che iniziano fuori dalle pagine del campione.
  Tre (B026, B040, B074) sono stati tenuti dopo controllo sul PDF.
- Solo secondo annotatore: 0. Classificati diversamente tra gli item comuni: 0.
- Differenze di contenuto tra gli item comuni: 2 (B044 condizione "if defective"; B235 azioni mancanti), decise a
  favore del secondo annotatore. Altre 9 differenze erano solo di formulazione (gold tenuto, testo stampato).

## Limiti

- Gold fatto da un'AI, senza revisione umana.
- Gli item safety_precaution e routine (174) non hanno avuto verifica indipendente né secondo annotatore.
- L'accordo tra annotatori copre 10 pagine e solo core/extended.
- Pagine con solo OCR (p18, p38, p54, p63) e etichette lette dalle immagini (p66-67, p74) hanno segmenti meno
  precisi.

## Confronto con il gold v1

- Dettagli in `CONFRONTO_V1.md`. Confronto fatto da AI, dopo la chiusura del gold v2.
- Rami v1: 66. Confermati 56, corretti 10 (R1, R3, R4, R6, R10, R11, R19, R20, R52, R66), aggiunti a v2 0,
  non supportati dal PDF 0.
- R1, R3, R4, R11: v2 tiene un ramo per codice (B108-B110) con l'azione di p40 "repeat Steps 1–6" e i passi in
  P013; v1 aveva i codici senza azione e un ramo unico con i passi come azioni.
- R6, R10, R19, R20: v2 divide in più rami (asse x/y; due cause stampate; ripetere la pulizia / sostituire).
- R52: v2 (B198) annota la cella stampata "Workpiece material beyond machine capability", assente in v1.
- R66: v2 (B238) è safety_precaution con i due atti stampati in più.
- Differenze solo di divisione delle azioni ("A or B", "Inspect/replace"): contate come confermate.
- Elementi v2 senza controparte v1: 202 (109 safety_precaution, 63 routine, 12 fault, 10 condition_maintenance,
  6 procedure, 2 diagnostic_test).
- Nessuna modifica al gold v2.
