# Handoff — hardening del motore di creazione del grafo

## Stato attuale

Data: `2026-08-04`

Decisione Product Owner: **revisione umana ancora aperta**
Stato: **nessun sottografo è stato approvato o unito**

La campagna di hardening CSV è implementata e verificata. Non è però una
autorizzazione al merge cross-source, alla pubblicazione o al passaggio alla
fase successiva. Ogni sottografo resta source-scoped nello stato `reviewing`
fino a una decisione esplicita del Product Owner.

Il report operativo e i risultati riproducibili della campagna sono in
[CSV Hardening Campaign](CSV_HARDENING_CAMPAIGN.md).

## Cosa è ora garantito per CSV/XLSX/JSON/JSONL

- Gli adapter strutturati producono una `RawUnit` e una `EvidenceUnit` per ogni
  riga valida; le righe non vengono cancellate per deduplica.
- CSV con UTF-8/BOM, UTF-16/32, CP1252, delimitatori comuni, quote, multilinea,
  intestazioni duplicate e righe di forma errata hanno un esito esplicito.
- Le virgolette CSV standard escape (`""`) sono lette senza creare colonne
  fantasma anche quando `csv.Sniffer` restituisce un dialect incompleto.
- Gli header sono normalizzati e confrontati con alias di ruolo versionati;
  un header diagnostico sconosciuto apre una sola decisione HITL alla volta.
- **Una cella piena di una colonna mappata è un solo claim.** Il generatore non
  spezza più su `|`: quel carattere è testo, non un separatore.
- **Un ruolo semantico appartiene a una sola colonna.** Gli alias possono
  proporre lo stesso ruolo a più colonne; la prima lo tiene, le altre restano
  attributi — contenuto leggibile, nessun elemento generato.
- Il mapping è correggibile dall'operatore
  (`POST /api/g2/profiles/{id}/columns`): assegnare un ruolo già preso lo
  rilascia da chi lo aveva.
- Ogni mappatura effettiva ha fingerprint; una sua revisione genera nuova
  evidenza immutabile e invalida in modo sicuro il sottografo precedente.
- Nodi e relazioni sono consolidati soltanto per identità deterministica:
  tipo ontologico + label normalizzata per i nodi, tipo + endpoint per gli
  archi. Le evidenze di tutte le occorrenze restano collegate.
- Il generatore non crea prodotti cartesiani: una riga con piu sintomi e piu
  cause/azioni non accoppiabili diventa un `knowledge gap` e blocca
  l'approvazione.
- Il validatore controlla proprietà richieste/extra, domain/range, endpoint,
  ID, provenienza e mapping irrisolti sul payload reale.

## Identità di una lettura

Tre costanti distinte, ognuna con il suo dominio. Confonderle ha rotto la
preparazione una volta, e la lezione è codificata nei commenti:

| costante | identifica | dove vive |
|---|---|---|
| `ADAPTER_VERSION` | il parse dei byte: codifica, delimitatore, righe, colonne | timbrata in ogni `RawUnit` **immutabile** |
| `EVIDENCE_DERIVATION_VERSION` | come dal record si ricava il significato | dentro `mapping_fingerprint` |
| `GENERATOR_VERSION` | come dalle evidenze si costruisce il grafo | dentro `input_config_hash` |

Alzare `ADAPTER_VERSION` per esprimere un cambio di *significato* rende ogni
riga già registrata impossibile da ri-registrare e fa fallire l'intera
preparazione. Il guardrail delle `RawUnit` confronta ora il **contenuto**
(posizione, hash dei byte, flag) e non l'etichetta del lettore: una fonte letta
da un adapter più vecchio resta rileggibile, e la riga conserva la versione di
chi l'ha prodotta come provenienza.

## Limiti deliberati da non mascherare

1. Il consolidamento corrente non è semantico o fuzzy. `Low pressure` e
   `Pressione bassa` restano nodi distinti; anche una differenza lessicale
   significativa non viene corretta automaticamente.
2. Il mapping CSV e la generazione sono deterministici: nessun LLM viene
   chiamato durante parsing, mapping, pairing o deduplica.
3. L'assenza di un campo lingua esplicito può lasciare la qualifica linguistica
   a `unknown`; il testo originale resta comunque integro e navigabile.
4. Le correzioni manuali di mapping non sopravvivono a un cambio di
   `ADAPTER_VERSION`: il file viene riprofilato e le domande sulle colonne
   tornano da capo. Le risposte restano nel ledger e potrebbero essere
   riapplicate, ma oggi non lo sono.
5. Le celle che contengono `|` restano un solo elemento con il carattere dentro
   l'etichetta. È un problema del dato, ed è giusto che si veda: la pulizia
   avanzata del testo è fuori dal perimetro attuale.

## Prossima sequenza, senza aggirare la revisione

1. Estendere la matrice CSV con altri settori, export reali e casi negativi.
2. Definire un layer di canonicalizzazione multilingua per ruolo ontologico.
   Il default deve essere un dizionario/configurazione revisionabile.
3. Riapplicare le risposte dell'operatore sul mapping dopo un aggiornamento
   dell'adapter, chiedendo solo le colonne effettivamente nuove.
4. Valutare un LLM soltanto come generatore di **candidate merge** o di
   diagnostica di qualità: non può mutare il grafo, unire nodi o chiudere gap
   senza evidenza, spiegazione e decisione umana tracciata.
5. Ripetere gli stessi contratti e controlli sul percorso PDF condiviso.

## Condizioni per una nuova revisione Product Owner

Il test può essere riproposto soltanto quando:

- la campagna CSV concordata è verde e riproducibile;
- ogni gap è esplicito, tracciabile e non approvabile;
- la canonicalizzazione multilingua ha policy e test propri, se adottata;
- il validatore strict è eseguito dalla API;
- l'explorer rende la revisione leggibile su grafi reali;
- la campagna PDF usa lo stesso contratto evidence → sottografo → validazione.
