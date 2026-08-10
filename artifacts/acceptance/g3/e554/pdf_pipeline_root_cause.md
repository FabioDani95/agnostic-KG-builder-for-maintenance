# Analisi strutturata della pipeline PDF G3 - E-554

Data dell'analisi: 2026-08-09  
Commit analizzato: `285be28` (`feat: integrate scoped PDF graph generation`)  
Revisione PDF analizzata: `sgrev_7LZ055k1Xf7rISyDNyE8kw`  
Modello della run: `gpt-5.6-terra`

## Conclusione

Il PDF non e il collo di bottiglia. E-554 ha 54 pagine, testo nativo su tutte
le pagine e circa 90.000 caratteri estraibili. Le pagine 37-39 di
troubleshooting sono leggibili e strutturate. Le pagine con meno di 100
caratteri sono quasi tutte schemi elettrici/pneumatici.

La regressione nasce nell'integrazione `EvidenceUnit -> pagine legacy` e viene
amplificata da scoping e chunking:

1. il repository restituisce le evidenze ordinate per `evidence_id`, cioe un
   hash, non per posizione nel PDF;
2. la proiezione legacy concatena i blocchi nell'ordine ricevuto, distruggendo
   l'ordine di lettura;
3. lo scoping unisce regole, LLM e keyword anche quando le keyword dovrebbero
   essere soltanto un fallback;
4. il keyword scan crea una macro-sezione 12-44 sovrapposta alle sezioni ToC;
5. il chunker tratta ogni sezione come un gruppo indipendente e non deduplica
   le pagine sovrapposte, neppure dentro lo stesso chunk;
6. ogni duplicazione viene moltiplicata da draft, relation pass, semantic
   validation, re-extraction, coverage e resolution completion;
7. il bridge converte poi il risultato legacy nel contratto G3, ma i due
   contratti di identity e provenance non coincidono.

Questa e una regressione di integrazione e di rendering, non una prova che il
nuovo modello sia peggiore.

## Addendum implementativo del 2026-08-09

Le correzioni deterministiche descritte in questo report sono state
implementate dopo l'analisi, senza rilanciare E-554 e senza chiamate API reali:

- il renderer ordina per locator, elimina la duplicazione testuale delle righe
  tabellari e inserisce anchor `EVIDENCE_ID`;
- il chunker partiziona ogni pagina fisica una sola volta conservando tutte le
  sezioni sovrapposte come contesto;
- le keyword sono fallback e non ampliano più cut plan affidabili;
- l'Asset ID esplicito viene preservato e la strict validation verifica
  cardinalità Asset e ownership dei Component;
- le relazioni restituiscono `source_anchor`, verificato insieme alla quote;
  i nodi standalone sono risolti per contenuto invece che per sola pagina;
- il routing per ruolo viene rispettato e incluso nel config hash;
- durata, token, chiamate e costo stimato per stage/modello vengono persistiti
  in `SourceSubgraphRevision.generation_metrics` e mostrati nella UI.

Questo addendum registra l'implementazione, non una nuova evidenza qualitativa
su E-554. Quella richiede una run reale separata e autorizzata. Il contratto
aggiornato è documentato in `docs/PDF_PIPELINE_AND_RUN_KPIS.md`.

## Evidenza quantitativa della run

| Indicatore | Valore |
|---|---:|
| Pagine fisiche | 54 |
| Pagine selezionate | 39 (72,2%) |
| Sezioni del cut plan | 35 |
| Chunk ontology | 17 |
| Occorrenze di pagina nei chunk | 72 |
| Pagine elaborate piu di una volta | 24 |
| Massima molteplicita | pagina 28, 5 volte |
| Testo unico delle 39 pagine nella proiezione | 73.105 caratteri |
| Testo ripetuto nei chunk | 147.406 caratteri |
| Amplificazione da overlap | 2,016x |
| Chiamate LLM preflightate nel trace | 97 |
| Durata | circa 713 s |
| Output G3 | 345 nodi, 288 relazioni, 30 gap |
| Asset nel sottografo | 0 |
| Componenti | 167 |

Il draft iniziale rappresenta soltanto circa il 12,7% degli input token
stimati. Il resto viene consumato da relation pass, validazione, re-extraction,
coverage e resolution. La validazione semantica da sola pesa circa il 34%.

## P0 - Ordine di lettura corrotto dalla proiezione G3

Il vecchio percorso lavorava sul testo restituito da PyMuPDF. Il bridge G3
parte invece dalle evidenze persistite:

- `EvidenceRepository.list_evidence()` ordina per `e.source_id,
  e.evidence_id`;
- `evidence_units_to_legacy_pages()` concatena le quote nell'ordine ricevuto;
- `evidence_id` e derivato da un hash, quindi l'ordine intrapagina e
  pseudo-casuale.

Misura sul manuale:

- 54/54 pagine hanno piu blocchi nativi;
- 51/54 risultano non monotone dopo la proiezione;
- inversion ratio medio: 0,553;
- pagina 37: blocchi `14, 11, 17, 10, 15, 18, 9, ...` invece di
  `0, 1, 2, ...`.

Su pagine a due colonne come 37-39 questo separa heading, descrizione, cause e
azioni e li ricombina con blocchi adiacenti. E una causa diretta di pairing
spurio. Nel sottografo reale compare infatti la relazione vietata dalla golden
legacy:

`Laser cutting path is too wide -> Laser fume extractor has reduced or no vacuum`.

Compaiono anche associazioni palesemente contaminate come
`Y-motor belt is worn -> Fume Extractor Shroud`.

Le 143 EvidenceUnit di tabella aggiungono un secondo problema: una riga puo
essere presente sia nel blocco nativo sia come `table_row`. La proiezione
deduplica soltanto stringhe identiche, non contenuto sovrapposto. Sulle pagine
selezionate il payload e gia l'8,8% piu grande del testo nativo prima del
chunking.

## P0 - Chunking con pagine duplicate

`_split_pages_by_section()` crea un gruppo di pagine per ogni sezione e poi
usa `current_pages.extend(group_pages)` senza una chiave per pagina.

Con sezioni sovrapposte il problema non e solo cross-chunk:

- pagina 13 compare due volte nello stesso chunk 8;
- pagina 19 compare due volte nello stesso chunk 9;
- pagina 24 compare due volte nello stesso chunk 10;
- pagina 25 compare due volte e pagina 28 tre volte nello stesso chunk 11;
- pagina 28 ricompare anche in altri chunk, per un totale di cinque passaggi.

Il limite `max_pages_per_chunk: 5` conta le occorrenze duplicate, non le pagine
uniche. Crea quindi piu chunk e piu chiamate pur processando meno informazione.

## P0 - Scoping orientato alla recall indiscriminata

E-554 ha una ToC chiara a pagina 2. Il cut plan ha comunque unito:

- 32 sezioni selezionate deterministicamente dalla ToC;
- 23 sezioni LLM;
- 4 macro-sezioni keyword.

Il keyword scan considera `service`, `maintenance`, `inspection`,
`calibration`, `parts list`, schemi e operazioni di replacement. Inoltre
raggruppa match separati da un solo buco. Nel manuale questo produce
`Keyword match (pp. 12-44)`.

`merge_sections()` mantiene l'intera macro-sezione se contiene anche una sola
pagina ancora scoperta; non sottrae le pagine gia coperte dalle sezioni ToC.
La macro-sezione e quindi conservata intera e sovrapposta a tutte le sezioni
dettagliate.

Il risultato e coerente con il prompt attuale, che chiede di estrarre tutti i
componenti e tutte le azioni dalle sezioni ricevute. Non e pero coerente con
la baseline diagnostica, che considera preventive maintenance e cross-pairing
come contaminazione.

## P0 - Identity Asset incompatibile

Il workspace usa l'ID opaco:

`asset_sp-MAerxQGspR0owUlNh-A`.

`extract_asset_identity()` applica `_normalize_asset_id()` e lo trasforma in:

`asset_sp_maerxqgspr0owulnh_a`.

Il core normalizza tutti gli Asset verso questo ID legacy. L'adapter G3
confronta poi l'ID con quello opaco byte-per-byte, rileva mismatch e scarta il
nodo Asset invece di rimapparlo. Per questo il sottografo ha zero Asset.

La strict validation restituisce comunque `passed: true` perche valida solo i
nodi presenti e non verifica la cardinalita globale `esattamente 1 Asset`.
L'approvazione viene bloccata soltanto dal knowledge gap. Questo non soddisfa
`AC-ONT-003` e rende il semaforo di validazione fuorviante.

## P1 - Contratto di provenance non allineato

Il core legacy emette spesso una pagina senza una quote claim-level. Il bridge
G3 richiede invece un locator canonico preciso. La conversione tenta di
ritrovare la quote con containment o overlap token >= 0,8; quando la quote e
vuota collega tutte le evidenze della pagina e apre un gap.

Esito reale:

- 19 `pdf_evidence_quote_missing`;
- 1 quote non risolvibile;
- 1 nodo senza provenance risolvibile;
- 1 relazione senza provenance risolvibile;
- 1 endpoint omesso.

Il bridge sta quindi facendo un round trip fragile:

`EvidenceUnit -> testo senza ID -> output pagina/quote -> fuzzy remap a EvidenceUnit`.

La soluzione robusta e rendere gli anchor delle EvidenceUnit parte del payload
semantico, con alias compatti e deterministici, e richiedere quegli anchor in
output. Il quote matching deve restare un controllo, non il meccanismo primario
di identita.

## P1 - Osservabilita persa nel bridge

`draft_ontology_workflow()` calcola token, cache, chiamate, retry, durata e
costo e li registra in `store["run_metrics"]`. `PdfSourceSubgraphBuilder`
crea pero uno `store` locale e, dopo `_to_revision()`, lo elimina senza
persistere le metriche nella revisione o in un Run G3.

Per questa run sono recuperabili esattamente soltanto i token di scoping. Il
resto e stato ricostruito dal trace terminale. Questa e una regressione
funzionale rispetto alla pipeline legacy e viola il requisito di accounting
di `AC-PERF-002`.

## P1 - Routing dei modelli bypassato

Il bridge passa `settings.MODEL_NAME` sia allo scoping sia all'ontology. Non
legge il routing per ruolo di `config.yaml`. Nella run lo scoping ha quindi
usato Terra nonostante `agents.scoping.model` sia Luna.

Questo non spiega l'ordine corrotto o i duplicati, ma aumenta costo e rende il
comportamento diverso da quello dichiarato in configurazione. Prima di un A/B
fra modelli va corretta questa divergenza.

## Prezzo della run

Prezzi ufficiali GPT-5.6 Terra al 2026-08-09: $2/M input, $0,20/M cached
input, $12/M output.

- Scoping esatto: 9.840 input + 2.936 output = 12.776 token,
  **$0,054912**.
- Input totale ricostruito: circa **869.981 token**, equivalente a
  **$1,739962** se tutto uncached.
- Completion token effettivi e cached input del core non sono persistiti.
- Dai rapporti completion/prompt delle precedenti run reali versionate, una
  stima euristica del totale e **$3,19-$6,42**, valore centrale circa
  **$4,92**.
- Il tetto teorico, se ogni chiamata avesse consumato tutto il proprio output
  budget, e **$10,631962**. Non e una stima realistica, soltanto un upper bound.

Il totale pagato esatto non e dimostrabile con gli artifact correnti. Il file
`pdf_pipeline_cost_reconstruction.json` conserva formule, dati e limiti della
ricostruzione.

## Perche i benchmark precedenti sembravano migliori

La codebase documenta buone run reali su PDF sorgente piu lunghi:

- FANUC, PDF sorgente 114 pagine: 63k-100k token, $0,38-$0,46;
- ABB, PDF sorgente 80 pagine: circa 160k token, $0,88;
- Whirlpool, PDF sorgente 64 pagine: 215k-225k token, $1,14-$1,37.

Ma il protocollo golden non passa il PDF intero. Usa fixture Markdown compatte
con cover, indice, pagine diagnostiche selezionate e pochi distractor. FANUC,
per esempio, usa 10 pagine del manuale da 114 pagine. Questi numeri misurano
principalmente il core semantico su un input gia curato; non misurano il nuovo
round trip G1 EvidenceUnit -> bridge G3 su tutte le pagine.

Quindi sono validi come baseline del core, ma non sono un confronto
end-to-end omogeneo con la run E-554.

## Ordine di correzione prima di chiudere G3

### Blocco A - Correzioni deterministiche, senza nuova spesa LLM

1. Rendere il semantic rendering stabile per pagina e locator:
   `page -> block_index`, poi `table_index -> row_index`, poi OCR region.
2. Rappresentare il contenuto di tabella una sola volta nel payload semantico.
3. Normalizzare il cut plan in una partizione di pagine uniche prima del
   chunking; una pagina fisica puo apparire al massimo una volta per pass.
4. Separare `keyword recall hints` da `semantic sections`; le keyword non
   devono diventare una macro-sezione sovrapposta quando ToC/rule/LLM sono
   disponibili.
5. Preservare l'Asset ID opaco senza normalizzazione legacy e rimappare tutti
   gli endpoint prima della validazione.
6. Estendere strict validation con cardinalita Asset e `HAS_COMPONENT`.

### Blocco B - Provenance e accounting

1. Annotare ogni blocco inviato al modello con un anchor compatto e
   deterministico che risolva a una EvidenceUnit.
2. Richiedere anchor espliciti per nodi e relazioni; quote e pagina diventano
   verifiche secondarie.
3. Persistire `run_metrics`, call lifecycle, config e model routing nel Run G3
   e nella revisione.
4. Usare Luna per scoping/critica economica e Terra per extraction/validation,
   come dichiara la configurazione, salvo esito contrario degli eval.

### Blocco C - Calibrazione qualitativa

1. Congelare E-554 come fixture full-PDF, distinta dall'excerpt golden.
2. Eseguire prima mock/replay sul rendering e sul cut plan.
3. Eseguire almeno due run reali identiche sul commit corretto.
4. Valutare la golden legacy completa, inclusi i cinque forbidden chains,
   non soltanto il sottoinsieme 8/3 usato nella prima acceptance campaign.
5. Soltanto dopo approvare il PDF e procedere al merge cross-source.

## Gate proposti per il rerun E-554

- ordine locator monotono su 54/54 pagine;
- zero pagina duplicata fra o dentro chunk;
- pagine 37, 38 e 39 sempre incluse;
- pagine schematiche 40-50 escluse dal text LLM salvo retrieval mirato;
- esattamente un Asset con ID byte-identico al workspace;
- zero forbidden chain della fixture Eagle;
- zero gap bloccante e 100% anchor provenance risolvibili;
- zero endpoint mancante e zero near-duplicate evidente nel campione audit;
- ledger completo di prompt, cached prompt, completion, chiamate, retry e costo;
- budget iniziale: <= 250k token totali, <= 35 chiamate e <= $1,50 per run
  Terra-equivalente; le soglie vanno poi congelate dopo due run corrette.

## Test di regressione mancanti

1. Proiezione con EvidenceUnit salvate in ordine hash e assert dell'ordine
   `block_index` ricostruito.
2. Sezioni sovrapposte e assert che ogni `page_number` compaia una sola volta.
3. Asset opaco con maiuscole e trattini preservato byte-per-byte.
4. Tabelle: nessuna riga duplicata fra blocco e struttura tabellare.
5. E-554 full-PDF: scoping, forbidden chains, Asset, provenance e budget.
6. Persistenza delle metriche dopo riavvio del server.

## Decisione

G3 deve restare **non accettato**. Il prossimo lavoro corretto non e un nuovo
test end-to-end a pagamento e non e il merge: e il Blocco A, seguito da
replay deterministico, Blocco B e solo infine il rerun reale E-554.
