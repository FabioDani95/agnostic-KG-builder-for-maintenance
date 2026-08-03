# Handoff — hardening del motore di creazione del grafo

## Stato attuale

Data: `2026-08-03`

Decisione Product Owner: **gate umano G3 ancora aperto**
Stato: **G3 non accettato; nessun sottografo è stato approvato o unito**

La prima campagna di hardening CSV è implementata e verificata. Non è però
una autorizzazione al merge cross-source, alla pubblicazione o al passaggio
alla fase G4. Ogni sottografo resta source-scoped nello stato `reviewing` fino
a una decisione esplicita del Product Owner.

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

## Limiti deliberati da non mascherare

1. Il consolidamento corrente non è semantico o fuzzy. `Low pressure` e
   `Pressione bassa` restano nodi distinti; anche una differenza lessicale
   significativa non viene corretta automaticamente.
2. Il mapping CSV e la generazione G3 sono deterministici: nessun LLM viene
   chiamato durante parsing, mapping, pairing o deduplica.
3. L'assenza di un campo lingua esplicito può lasciare la qualifica linguistica
   a `unknown`; il testo originale resta comunque integro e navigabile.
4. La UI G3 è funzionale per revisione e provenienza, ma non è la UI finale:
   le card attuali non sono il modello visivo approvato per un grafo denso.

## Prossima sequenza, senza aggirare il gate

1. Estendere la matrice CSV con altri settori, export reali e casi negativi.
2. Definire un layer di canonicalizzazione multilingua per ruolo ontologico.
   Il default deve essere un dizionario/configurazione revisionabile.
3. Valutare un LLM soltanto come generatore di **candidate merge** o di
   diagnostica di qualità: non può mutare il grafo, unire nodi o chiudere gap
   senza evidenza, spiegazione e decisione umana tracciata.
4. Ridisegnare `Elaborazione` come explorer del grafo: canvas centrale,
   pannello dettaglio/evidenza su richiesta, filtri per tipo e gap, densità
   controllata e nessuna cascata di card decorative.
5. Ripetere gli stessi contratti e controlli sul percorso PDF condiviso.

## Condizioni per un nuovo gate Product Owner

Il test G3 può essere riproposto soltanto quando:

- la campagna CSV concordata è verde e riproducibile;
- ogni gap è esplicito, tracciabile e non approvabile;
- la canonicalizzazione multilingua ha policy e test propri, se adottata;
- il validatore strict è eseguito dalla API;
- il redesign dell'explorer rende la revisione leggibile su grafi reali;
- la campagna PDF usa lo stesso contratto evidence → sottografo → validazione.
