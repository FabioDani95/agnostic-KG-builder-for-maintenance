# Handoff — singolo rerun reale E-554 con profilo Luna

Copia il prompt seguente in una nuova chat Codex aperta sullo stesso workspace.

---

Lavora nella repository:

`/Users/fabiodaniele/Coding/Maintenance_Graph_Generator/agnostic-KG-builder-for-maintenance`

Devi eseguire un test di accettazione end-to-end controllato della pipeline PDF
G3 sul manuale:

`/Users/fabiodaniele/Downloads/E-554.pdf`

## Autorizzazione e limite di spesa

Sei esplicitamente autorizzato a usare la `OPENAI_API_KEY` già presente in
`.env` per **una sola generazione reale del sottografo PDF**. Una generazione
comprende tutte le chiamate interne, gli eventuali retry automatici già previsti
dalla pipeline e le fasi di finalizzazione.

- Non stampare, copiare o esporre la chiave.
- Non cliccare/invocare “Genera” o “Rigenera” più di una volta.
- Non effettuare una seconda run se la prima fallisce, è incompleta o produce
  qualità insufficiente: raccogli log e stato, diagnostica e fermati.
- Non processare il CSV e non avviare il merge: questo test riguarda soltanto il
  sottografo PDF.
- Non approvare né rifiutare il sottografo; fermati nello stato di revisione.
- Non modificare o sovrascrivere gli artefatti della baseline.

## Configurazione che deve essere verificata prima della chiamata reale

Il worktree contiene modifiche intenzionali non ancora committate: preservale e
non fare reset/checkout. Prima della run verifica senza chiamate API che
`config.yaml` contenga esattamente:

- scoping: `gpt-5.6-luna`, `reasoning_effort: low`;
- ontology draft/finalizzazione: `gpt-5.6-luna`,
  `reasoning_effort: medium`.

Verifica inoltre che `KG_LLM_MODE` non sia `mock`, che la chiave esista senza
mostrarne il valore e che il server carichi il codice/configurazione corrente.
L'`input_config_hash` include ora modello ed effort, quindi non deve riusare la
vecchia revisione Terra. Se una di queste condizioni non è vera, correggi solo
il problema di preflight e non consumare la run finché il profilo non è certo.

## Contesto del difetto e baseline

La vecchia run reale usava `gpt-5.6-terra` e ha prodotto:

- 54 pagine totali, 39 selezionate;
- 35 sezioni, 17 chunk, 97 chiamate LLM osservate;
- circa 713 secondi;
- 345 nodi, 288 relazioni, 518 riferimenti di evidenza e 30 gap;
- 0 Asset a causa di un mismatch con l'identità canonica;
- costo storico stimato `$3.19–$6.42`, valore centrale `$4.92`;
- tutte le 8 catene minime presenti e 0/3 abbinamenti vietati.

La root cause era nell'integrazione, non nel PDF: ordine delle EvidenceUnit
corrotto, pagine duplicate tra sezioni/chunk, keyword scan espansivo, Asset
ricercato/rinormalizzato dal PDF, provenance fuzzy e metriche non persistite.
Questi difetti sono stati corretti. Nel percorso workspace l'Asset è ora quello
definito dall'utente: il modello non deve cercarlo né emetterlo; il sistema lo
inietta e deriva `HAS_COMPONENT`/`GENERATES_ERROR`.

Leggi prima del test:

- `docs/PDF_PIPELINE_AND_RUN_KPIS.md`
- `artifacts/acceptance/g3/e554/pdf_pipeline_root_cause.md`
- `artifacts/acceptance/g3/e554/pdf_pipeline_cost_reconstruction.json`
- `artifacts/acceptance/g3/e554/report.md`
- `artifacts/acceptance/g3/e554/result.json`
- `artifacts/acceptance/g3/e554/gold.json`

SHA-256 atteso del manuale:
`a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0`.

## Percorso E2E richiesto

1. Esegui preflight e test offline mirati; non usare API OpenAI in questa fase.
2. Avvia o riavvia in sicurezza il server locale con la configurazione corrente.
3. Usa una vera interazione browser/UI, non soltanto chiamate HTTP dirette.
4. Crea preferibilmente un nuovo workspace pulito e definisci come Asset
   canonico:
   - nome: `Eastman Eagle S3L`;
   - brand: `Eastman`;
   - modello: `Eagle S3L`;
   - tipo: `automated cutting machine`.
5. Carica E-554 dalla UI, verifica la fonte e avvia **una volta sola** la
   generazione PDF.
6. Attendi il completamento mantenendo traccia di progress, log e stato UI.
7. Apri la revisione del sottografo e prova ricerca, filtri, tab delle lacune,
   leggibilità della mappa e card KPI. Non prendere una decisione.
8. Verifica via API/repository locale i dati persistiti della revisione senza
   alterarla.

Se il workspace pulito non è praticabile per un difetto preflight puramente UI,
puoi usare il workspace storico `ws_KDXOoS3tgJcUSGP-NfuzSA`, ma devi dimostrare
che è stata creata una nuova revisione con il nuovo config hash e non servita la
vecchia revisione `sgrev_7LZ055k1Xf7rISyDNyE8kw`.

## Misure e confronto obbligatori

Raccogli almeno:

- pagine e sezioni selezionate; presenza delle pagine 37–39;
- numero di chunk, retry e chiamate per operazione;
- durata, prompt/cached/output/total token, modello, reasoning effort e costo
  stimato totale/per stage/per modello;
- conteggi nodi per tipo, relazioni, evidenze e knowledge gap per codice;
- esattamente un Asset, con ID identico a quello del workspace;
- copertura delle 8 catene minime e presenza dei 3 pairing vietati usando
  `gold.json`;
- duplicati esatti e chiari near-duplicate;
- quote/anchor risolvibili e qualità semantica delle attribuzioni;
- strict validation, eligibility e dimensione della review queue;
- bug funzionali e osservazioni UI/UX riproducibili con screenshot quando utili.

Confronta ogni metrica disponibile con la baseline Terra. Se una metrica nuova
non ha un valore storico esatto, dichiaralo; non inventare valori. A parità di
token Luna costa un decimo di Terra, quindi la vecchia fascia corrisponderebbe a
circa `$0.32–$0.64`. Verifica il costo realmente persistito anziché assumere che
la riduzione sia stata raggiunta.

## Output richiesto

Crea una nuova directory, senza sovrascrivere la baseline:

`artifacts/acceptance/g3/e554/luna_validation/`

Salva almeno:

- `result.json`: output e KPI macchina leggibili;
- `report.md`: confronto strutturato old Terra vs new Luna e verdetto;
- eventuali screenshot/log essenziali con nomi chiari.

Nel verdetto separa:

1. correttezza della pipeline e regressioni;
2. qualità semantica del sottografo;
3. qualità UI/UX della revisione;
4. costo e tempo;
5. decisione consigliata: G3 accettabile oppure ancora bloccato, con ragioni.

Non procedere al merge dei sottografi. Alla fine riporta chiaramente che è stata
consumata una sola run reale e se il risultato è stato ottenuto integralmente o
se il test si è fermato su un difetto.

---
