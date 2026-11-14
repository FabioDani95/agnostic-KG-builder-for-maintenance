# Gold v2: graco_gtx_2000ex (GTX 2000EX, Repair and Parts 313385F, 18 pagine)

## Che cos'è

Questo è il gold v2 del manuale. È fatto da un'AI.
Annotatori, verificatore e aggiudicatore sono Claude Opus 5.5 (claude-opus-5-5).
Il coordinamento è di Claude Fable 5.2 (claude-fable-5-2).
Nessuna persona lo ha ancora rivisto.

Come è stato prodotto:

- un annotatore AI ha letto tutte le pagine (p1-18) su testo e immagine;
- un verificatore AI indipendente ha ricontrollato ogni elemento sul PDF;
- un secondo annotatore AI ha annotato da zero il 25% delle pagine diagnostiche (p2 e p6);
- un aggiudicatore AI ha deciso ogni proposta guardando il PDF.

Le decisioni sono in `adjudication.json` (cartella di lavoro, fuori da Git).

## Decisioni

- Tabella guasti (p8-9): un ramo per causa. Se una causa ha più celle soluzione, è un solo ramo
  con più azioni nell'ordine stampato ("Stalled pump", "Fluid delivery too low", "Fluid delivery too high").
- "Material must be mixed thoroughly ..." è un'istruzione: azione `repair` con il risultato atteso in `expected`.
- I due controlli giornalieri dentro i box di p2 ("Check equipment daily", "Check hoses, tubes, and couplings daily")
  sono `condition_maintenance`: hanno una condizione di guasto (parti usurate o danneggiate).
- Il NOTICE sul gelo (p3) e la NOTE prima di togliere la tramoggia (p6) sono `safety_precaution`.
- Pressure Relief (p6) è `routine`. Rimozione/installazione di tramoggia e pompa (p6-7) sono `procedure`.
- Distinte parti (p13, p15): tutte le parti sono nell'inventario dei componenti, tranne viti e dadi generici.

## Casi difficili

- "Stalled pump": il manuale non dice se "Contact an authorized Graco service center" è un'alternativa
  o il passo da fare se il riavvio non basta. Le azioni sono nell'ordine stampato, senza condizione.
- Righe uguali con problemi diversi (B011/B020, B018/B024): sono percorsi diversi della tabella e restano separate.
- "Material too thick" sotto "Speed of application too slow" non dice "Thin the material": annotato come scritto.

## Dubbi aperti

- La classe dei controlli giornalieri di p2 (condition_maintenance o safety_precaution) è discutibile.
- "material line" (p3) è stato letto come il tubo del materiale (texture hose).
- "air lines" (p7) è stato associato al tubo aria 15C968; potrebbero essere più tubi.

## Errori o contraddizioni del manuale

- Il manuale pompa è 309915 a p1, ma 308479 a p8 e p16.
- p9 chiama 309915 "Operation Manual"; a p1 il manuale operativo è 313384.
- p5 cita il manuale pistola 308878, ma la nota sotto e p1 dicono 310616.
- p6 usa le lettere G (hopper) e H (coupler); nella lista di p5 sono B e C.
- "gun air valve (23)" (p6) non corrisponde alla voce 23 della distinta di p13.
- "See Grounding instructions" (p2) non ha una destinazione in questo manuale.
- p15: "air side plate" e "fluid side plate" hanno lo stesso codice 188607.

## Verifica indipendente

- Scope verificati: core, extended e context (tutte le categorie).
- Elementi controllati: 39 (34 rami e 5 procedure).
- Ok: 28. Corretti: 6 (B012, B016, B025, B027, B030, B032). Rimossi: 5 (B017, B028, B029, B033, B034).
  Aggiunti: 0 (il verificatore non ha trovato elementi mancanti).
- Tutte le proposte sono state accettate dopo controllo sul PDF. Accettate anche le 3 correzioni della mappa pagine.
- Nessuna proposta respinta.
- Nessun duplicato tra intervalli: un solo annotatore ha coperto tutto il manuale.

## Accordo tra annotatori

- Pagine: 2 e 6 (seme 20261113, 25% delle pagine diagnostiche).
- Confronto con il gold prima dell'aggiudicazione (9 elementi del gold, 8 del secondo annotatore).
- Trovati da entrambi: 8 (5 rami di p2, 3 procedure di p6).
- Solo nel gold: 1 (B009, la NOTE prima di togliere la tramoggia; il secondo annotatore l'ha messa dentro la procedura).
- Solo nel secondo annotatore: 0.
- Classificati in modo diverso: 0.
- Differenze di contenuto: 6 elementi su 8.
  - Sostanziali: 2. B002: manca l'azione "request MSDS forms" (accettata, aggiunta). P002: NOTE come passo
    (modificata: messa in `conditions` di P002, B009 resta).
  - Minori: 4 (B001, B003, B004, B005): solo nomi di componenti generici o una condizione stampata. Gold invariato.

## Limiti

- Tutto è fatto da AI; manca una revisione umana.
- Un solo verificatore e un solo secondo annotatore, su 2 pagine: l'accordo misurato è piccolo.
- Il manuale ha solo 2 pagine di tabella guasti: nessun codice d'errore, nessun test di componente, nessun diagramma.
- Le procedure di riparazione della pompa sono in un altro manuale (308479/309915) e qui mancano.

## Confronto con il gold v1

- Dettagli in `CONFRONTO_V1.md`. Confronto fatto da AI, dopo la chiusura del gold v2.
- Rami v1: 19. Confermati 16, corretti 3 (R10, R16, R19), aggiunti a v2 0, non supportati dal PDF 0.
- R10: v1 aggiunge "Thin the material", non stampato a p8 nella riga "Speed of application too slow / Material too
  thick"; v2 (B021) resta com'è.
- R16, R19: v1 ha "See Spray Techniques in Operation Manual 309915" come azione; v2 (B027, B032) lo tiene come
  riferimento esterno.
- Differenze solo di divisione delle azioni (R1, R4, R5, R8, R9, R12): stesso contenuto, contate come confermate.
- Elementi v2 senza controparte v1: 15 (8 safety_precaution, 2 condition_maintenance, 4 procedure, 1 routine).
- Nessuna modifica al gold v2.
