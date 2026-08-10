# Validazione E2E PDF G3 — E-554 con GPT-5.6 Luna

Data: 2026-08-09  
Workspace: `ws_ebXgqKWDDgsjKdrGbFDiQQ`  
Fonte: `src_S0wngbguWAy0g87w9MhKkQ`  
Revisione nuova: `sgrev_OR8HyabEt7ntt0Z00LZEoA`

## Verdetto sintetico

**È stata consumata una sola generazione reale, completata integralmente. G3 resta bloccato e non deve procedere al merge.**

Le correzioni infrastrutturali principali funzionano: il nuovo hash invalida Terra, l’Asset canonico è unico e byte-identico al workspace, le pagine non sono duplicate nei chunk, le keyword non espandono il cut plan, gli anchor canonici e i KPI sono persistiti, le 8 catene golden sono presenti e i 3 pairing vietati sono assenti. Il risultato non è però approvabile: 14 gap, 250 item nella review queue, 2 relazioni con quote non grounded, near-duplicate chiari, 399 nodi e 195 Component su 30 pagine. La UI mantiene la contraddizione sul filtro delle lacune e presenta un ulteriore difetto tabella/filtro.

## Integrità del test

- Worktree sporco preservato; nessun reset o checkout.
- SHA-256 del PDF verificato: `a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0`.
- 62 test offline mirati passati in `KG_LLM_MODE=mock`, con chiave vuota nel processo di test.
- Server riavviato dal codice corrente, senza hot reload.
- Modalità effettiva della run: `real`; chiave presente ma mai stampata.
- Routing: scoping `gpt-5.6-luna`/`low`; ontologia e finalizzazione `gpt-5.6-luna`/`medium`.
- Hash Luna: `a56332c8…b871e6`; hash Terra storico: `38eab2e6…ffe437`.
- Nuovo workspace creato dalla UI; nessuna revisione preesistente per la nuova fonte.
- Il pulsante di generazione è stato premuto una volta sola alle 19:33:10Z.
- Nessun CSV processato, nessuna decisione presa, nessun merge avviato.
- Stato finale dopo reload: `reviewing`; decisioni persistite: 0; merge barrier: `waiting_for_approval`.

## Terra precedente vs Luna corrente

| Metrica | Terra precedente | Luna corrente | Delta / nota |
|---|---:|---:|---|
| Pagine totali | 54 | 54 | invariato |
| Pagine selezionate | 39 | 30 | -9 (-23,1%) |
| Sezioni | 35 | 32 | -3 |
| Chunk | 17 | 19 | **+2** |
| Occorrenze di pagina duplicate | 24 pagine duplicate; 72 occorrenze | 0; 30 occorrenze uniche | corretto |
| Chiamate LLM | 97 osservate | 96 persistite | -1 |
| Durata | ~713 s | 444,69 s | -268,31 s (-37,6%) |
| Prompt token | ~869.981 stimati | 668.862 esatti | -23,1% vs stima |
| Cached prompt token | non disponibile | 54.119 | nessun confronto esatto |
| Completion token | non disponibile | 163.700 | nessun confronto esatto |
| Token totali | non disponibile | 832.562 | nessun confronto esatto |
| Costo | $3,19–$6,42 stimati; centrale $4,92 | **$0,320466 persistiti** | -93,5% vs centrale; 15,35× meno |
| Equivalente Luna a parità di token | $0,319–$0,642 | $0,320466 | al margine inferiore della fascia |
| Nodi | 345 | 399 | +54 (+15,7%) |
| Relazioni | 288 | 369 | +81 (+28,1%) |
| Evidenze uniche | 518 | 346 | -172 (-33,2%) |
| Gap | 30 | 14 | -16 (-53,3%) |
| Asset | 0 | **1** | root cause corretta |
| Component | 167 | 195 | +28 (+16,8%) |
| Symptom | 27 | 46 | +19 (+70,4%) |
| FailureMode | 74 | 68 | -6 |
| CorrectiveAction | 76 | 89 | +13 (+17,1%) |
| ErrorCode | 1 | 0 | -1 |
| Strict validation | pass | pass | invariato |
| Approval eligible | no | no | ancora bloccato |
| Catene minime | 8/8 | 8/8 | mantenute |
| Pairing vietati | 0/3 | 0/3 | mantenuti assenti |
| Duplicati normalizzati esatti | 2 gruppi | 0 gruppi | miglioramento |
| Review queue | storico esatto non disponibile | 250 | non confrontabile |

Il costo Terra resta una ricostruzione, non una fattura. Anche il nuovo costo è una stima di listino, ma questa volta è persistita dalla revisione e deriva dai token restituiti dall’API.

## Chiamate e finalizzazione

| Operazione | Terra | Luna |
|---|---:|---:|
| Scoping | 2 | 2 |
| Ontology draft | 17 | 19 |
| Relation extraction | 22 | 18 |
| Semantic validation | 29 | 29 |
| Re-extraction riflessiva | 12 | 10 |
| Coverage completion | 1 | 1 |
| Resolution completion | 14 | 17 |
| **Totale** | **97** | **96** |

Per Luna, scoping, chunk, retry, coverage e resolution sono ricavabili dai campi persistiti. Il conteggio relation extraction è il residuo esatto del totale dopo le cardinalità deterministiche; la revisione persiste solo aggregati per stage/modello, non bucket token/costo per singola operazione. Non sono stati osservati retry di trasporto; `retry_count=10` indica i dieci tentativi semantici di re-extraction previsti dal reflective loop. `parse_repair_count=0`.

Costi e token per stage:

| Stage | Modello / effort | Chiamate | Prompt | Cached | Output | Totale | Costo |
|---|---|---:|---:|---:|---:|---:|---:|
| Scoping | Luna / low | 2 | 8.219 | 0 | 2.503 | 10.722 | $0,004647 |
| Ontology + finalizzazione | Luna / medium | 94 | 660.643 | 54.119 | 161.197 | 821.840 | $0,315819 |
| **Totale** | Luna | **96** | **668.862** | **54.119** | **163.700** | **832.562** | **$0,320466** |

## 1. Correttezza della pipeline e regressioni

Esito: **pass con regressioni**.

Funziona:

- esattamente un Asset, ID `asset_mF-1RBkvmra24woUH3T6iQ`, identico al workspace;
- hash di configurazione nuovo e revisione nuova, senza riuso Terra;
- 30 pagine fisiche in 19 chunk, ciascuna presente una sola volta;
- pagine 37, 38 e 39 incluse;
- cut plan affidabile mantenuto senza keyword expansion;
- 346/346 evidenze canoniche risolvibili;
- strict validation passata con 1.864/1.864 proprietà richieste e zero errori domain/range, endpoint, invariant o ID duplicati;
- KPI completi persistiti e identici dopo reload/API/repository.

Regressioni o limiti:

- le pagine schematiche 40–50 sono state reinserite dal ripristino delle “component pages”, in contrasto con il gate proposto di escluderle salvo retrieval mirato;
- i chunk aumentano da 17 a 19 nonostante le pagine scendano da 39 a 30;
- il volume cresce a 399 nodi e 369 relazioni; l’eliminazione dell’overlap non ha ridotto la sovraestrazione;
- la revisione non persiste la review queue completa né bucket per operazione, solo aggregati per stage/modello;
- l’Asset iniettato eredita 319 evidenze incidenti: è corretto come identità ma molto rumoroso come superficie di provenance.

## 2. Qualità semantica del sottografo

Esito: **bloccata**.

Aspetti positivi:

- 8/8 catene golden presenti sulle pagine 37–39;
- 0/3 pairing vietati;
- 172/174 relazioni grounded (98,85%); causal grounding ratio 98,46%; nessuna relazione causale senza quote;
- i gap di quote mancanti scendono da 19 a 1;
- zero gruppi duplicati dopo normalizzazione esatta.

Problemi bloccanti:

- 14 gap, uno per ciascuno di 14 codici distinti;
- 250 elementi nella review queue: 48 open, 165 review, 37 advisory;
- 118 issue semantiche, 37 issue schema, 72 issue grafo e 370 relazioni suggerite registrate prima dell’adapter;
- due quote di relazione non grounded e quattro nodi segnalati;
- esempi di attribuzione debole: `AFFECTS` del pressure transducer basato solo sulla posizione; escalation al service non dichiarata dalla quote; una `RESOLVED_BY` sugli ottici non espressa dall’evidenza; quote round-knife non trovata; un `AFFECTS` a pagina 24 senza quote;
- nessun ErrorCode, contro uno nella baseline;
- near-duplicate chiari: `Linear Rail/Linear Rails`, `Gear Rack/Gear Racks`, `Fume Extractor/Laser Fume Extractor`, `Brass laser beam nozzle/Brass laser nozzle`, le due azioni pause-plunger, le due azioni vacuum-pressure, le due escalation al service e le due varianti safety-label;
- 195 Component e l’inclusione di diagrammi/maintenance indicano ancora sovraestrazione.

## 3. Qualità UI/UX della revisione

Esito: **bloccata**.

Funziona:

- ricerca `Touch screen`: 8 nodi e 3 relazioni visibili, 391 elementi nascosti;
- filtro Asset: un solo nodo;
- filtro `MAY_INDICATE`: 59 relazioni;
- zoom, adatta e ridisponi rispondono correttamente;
- card KPI leggibile e coerente con i dati persistiti;
- tab “Cosa manca 14” mostra tutte le lacune;
- lo stato resta `reviewing` e il pulsante di conferma è disabilitato.

Difetti riproducibili:

1. La tab mostra 14 lacune, ma “Solo con lacune” è disabilitato e dichiara che nessun elemento ha lacune o difetti.
2. La ricerca resta disponibile nella tab “Cosa manca”, ma `Touch screen` lascia visibili tutte e 14 le card: il controllo non filtra la vista.
3. Da “Elementi” o “Collegamenti”, cambiare un filtro sostituisce la tabella con la mappa senza cambiare la tab selezionata; ricliccare la tab ripristina la tabella.
4. La mappa a 399 nodi è troppo densa per revisione manuale; diventa utilizzabile solo dopo un filtro forte.

Screenshot principali:

- `review_full_map.png`: densità della mappa completa.
- `review_gaps_list.png`: card KPI, tab Cosa manca, filtro lacune disabilitato e gap visibili.
- `source_ready.png`: fonte caricata e persistita.

## 4. Costo e tempo

Esito: **pass**.

- Durata persistita: 444,69 s, circa 7 min 25 s; miglioramento del 37,6% rispetto ai ~713 s Terra.
- Costo persistito: $0,320466, al margine inferiore della fascia Luna equivalente della vecchia run ($0,319–$0,642).
- Riduzione rispetto al valore centrale Terra ricostruito: 93,5%, circa 15,35×.
- Il beneficio viene quasi interamente dal prezzo Luna: le chiamate restano 96 vs 97 e i token totali sono ancora 832.562.
- La riduzione economica è reale nel ledger persistito, ma non dimostra efficienza algoritmica sufficiente.

## 5. Decisione consigliata

**G3 ancora bloccato; non approvare la revisione e non procedere al merge.**

Prima dell’accettazione servono almeno:

1. eliminare o rendere retrieval-only le pagine 40–50 e ridurre chunk/call volume;
2. consolidare near-duplicate cross-chunk e contenere la crescita dei Component;
3. risolvere i 14 gap e portare il grounding relazionale al 100%;
4. ridurre la review queue a una dimensione operabile;
5. correggere filtro lacune, ricerca nella tab “Cosa manca” e incoerenza tabella/mappa dopo i filtri;
6. persistere il dettaglio per operazione e la review queue, se richiesti come KPI di accettazione.

La run Luna dimostra che identity, cache invalidation, page de-duplication, golden coverage e accounting sono stati corretti. Non dimostra ancora che il sottografo sia semanticamente affidabile o revisionabile a costi umani accettabili.
