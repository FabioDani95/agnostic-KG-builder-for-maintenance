# Protocollo di valutazione V3

Stato: **approvato da Fabio il 2026-09-27** (KPI, budget, un solo annotatore); valutazione a
rotazione approvata il 2026-09-28. Riprende [PROTOCOL.md](PROTOCOL.md) e lo rende
operativo per l'architettura V3 ([piano](../../docs/PIANO_V3.md)). Nessun risultato è
contenuto qui: solo come si costruisce il gold, cosa si misura e in che ordine.

## 1. Valutazione a rotazione (decisione di Fabio, 2026-09-28)

Sostituisce le tre fasi fisse (sviluppo, congelamento, test finale). I manuali disponibili
sono praticamente illimitati: ogni manuale viene prima **misurato** e poi **usato per
migliorare** il sistema.

| Passo | Cosa si fa | Regola |
| --- | --- | --- |
| 1. Gold | annotazione a mano del manuale nuovo, con perimetro esaustivo | chiuso prima di qualsiasi esecuzione; nessuno vede output del sistema su quel manuale |
| 2. Primo contatto | 3 esecuzioni con il codice congelato da un tag git | nessuna modifica di codice, prompt o lettore tra il tag e le esecuzioni; si registra il tag usato |
| 3. Sviluppo | analisi degli errori e correzioni strutturali, ciascuna con un test | da qui il manuale è di sviluppo per sempre; i suoi numeri successivi non misurano la generalizzazione |
| 4. Nuovo tag | congelamento della versione corretta | il manuale nuovo successivo ne misura il primo contatto |

**Cosa entra nel paper:**

- **Qualità su manuali nuovi:** solo i numeri di primo contatto (passo 2), ognuno con il tag
  del codice che lo ha prodotto. La serie per versione mostra come cresce la qualità su
  manuali mai visti.
- **Verifica finale:** alla fine, 3–5 manuali tenuti da parte ed eseguiti una sola volta
  con la versione finale, per misurare quella versione su manuali nuovi.
- **Adattamento:** i numeri dopo le correzioni (passo 3) si riportano separati, come misura
  di quanto il sistema migliora su un manuale già visto.
- **Grandezze di esercizio** (costo, tempo, domande a una persona, stabilità tra esecuzioni):
  si possono riportare su tutti i manuali, indicando la versione.

Un manuale usato per correggere il codice non torna mai a misurare la generalizzazione. Il
primo manuale di questa serie è Grizzly G0872 (tag `v3-freeze-2026-09-28`).

## 2. Scelta dei manuali

Dalla [ricognizione dei candidati](../manuals/candidate_troubleshooting_manuals.md),
proposta da confermare:

Obiettivo: 15–20 manuali di produttori e settori diversi, scelti per coprire strutture
diverse: tabelle sintomo/causa/rimedio, codici di allarme, prove di componenti con valori
attesi, procedure con bivi, condizioni di guasto dentro la manutenzione. Nessun produttore
già usato per correggere il codice nei manuali tenuti da parte per la verifica finale.

Per ogni manuale si registrano in `paper/manuals/registry.json`: titolo, versione,
produttore, settore, fonte, SHA-256 del PDF, split (sviluppo/test), pagine del
perimetro, date di esposizione.

## 3. Come si definisce il gold

**Unità.** Un *ramo* è una voce del manuale: una riga di tabella, un problema con i
suoi passi, un codice di allarme. Contiene problema (sintomo, oppure codice più
significato), causa e azioni. Un'*asserzione* è una singola relazione dell'ontologia
tra due di questi elementi (problema → causa, causa → azione, causa → componente).

**Perimetro.** L'annotatore sceglie le pagine diagnostiche leggendo il PDF, senza
vedere la mappa del sistema. Dentro il perimetro l'annotazione è **esaustiva**: ogni
ramo presente va annotato. Il perimetro è registrato nel gold.

**Cieco.** Il foglio di annotazione mostra solo il testo del manuale diviso in
segmenti con ID (`p11.t1.r3`). La lettura in segmenti non dipende dal modello, quindi
non rivela nulla degli output. Chi annota non vede grafi né estrazioni.

**Campi di ogni ramo:**

| Campo | Regola |
| --- | --- |
| problema | sintomo osservabile o codice con significato; ID dei segmenti |
| causa | come scritta nel manuale, oppure "non indicata nel manuale"; mai dedotta dal rimedio |
| azioni | una per rimedio, in ordine; tipo: riparazione, controllo, assistenza |
| componente | solo se il manuale dice che quella parte è guasta o da regolare |
| condizioni | "se…", "solo quando…", valori, esiti dei test |
| ID | i segmenti dove ciascun elemento è scritto |

**Chi annota.** In questa campagna c'è **un solo annotatore**. Per ridurre il rischio
di errori non visti: annota prima di qualsiasi esecuzione, ricontrolla a distanza di
almeno un giorno il 20% dei rami scelti a caso, e registra nome, data e minuti. Il
paper dichiarerà il limite: nessuna misura di accordo tra annotatori.

**Strumento.** Tutto passa da `scripts/campaign.py` e dalla cartella
[campaign](../../campaign/README.md): `prepare` scrive il testo del manuale in segmenti
(`gold/TESTO.md`) e il foglio vuoto (`gold/ANNOTAZIONE.md`), `gold` legge il foglio in
`gold/gold.json` e segnala ID inesistenti o azioni senza tipo.

## 4. KPI

| KPI | Definizione | Come si misura | Obiettivo (confermato) |
| --- | --- | --- | --- |
| Recall dei rami | rami del gold con catena problema → causa → azioni ritrovata | posizione + giudice di significato a tre voti | ≥ 90% |
| Recall delle asserzioni | asserzioni del gold ritrovate | come sopra, relazione per relazione | ≥ 90% |
| Precisione dei verdi | relazioni verdi corrette | revisione umana cieca di un campione stratificato | ≥ 90% |
| Correttezza delle prove | verdi le cui citazioni contengono entrambi gli estremi | automatica, sui segmenti del gold | ≥ 95% |
| Copertura della mappa | pagine del perimetro gold lette come diagnostiche | automatica | 100% |
| Lavoro umano | domande arrivate a una persona; minuti di risposta | rapporto di esecuzione; cronometro | ≤ 10 per manuale |
| Stabilità | differenza di recall tra 3 esecuzioni | min e max per manuale | ≤ 5 punti |
| Costo e tempo | USD dal registro, secondi per esecuzione | automatici | riportati, nessuna soglia |

Si riportano valori per manuale, totale (micro) e media dei manuali (macro), con
intervallo al 95% (Wilson per le proporzioni, bootstrap per manuale per le medie).
Esecuzioni fallite e domande senza risposta restano nel denominatore.

## 5. Procedura per ogni manuale

I passi e i comandi sono nel [README della campagna](../../campaign/README.md):
cartella del manuale, PDF e `info.yaml`, testo e foglio, gold scritto **prima** di
qualsiasi esecuzione, 3 esecuzioni V3 con il codice congelato (primo contatto), KPI,
revisione cieca della precisione. Solo dopo seguono l'analisi degli errori e le correzioni
dell'architettura, sempre con regole strutturali e non legate a un produttore, e ogni
correzione con un test.

## Budget

Tetto di **20 USD per l'intera campagna** (esecuzioni e giudice; alzato da 10 a 20 il 2026-09-28 da
Fabio per la valutazione a rotazione), su un
registro separato: `campaign/real_call_budget.jsonl`. Gli script lo
usano per impostazione predefinita; il registro blocca ogni chiamata oltre il tetto.
Misura attuale: 0,02–0,11 USD per esecuzione V3, circa 0,1 USD di giudice per manuale.

## Decisioni aperte

1. Quali manuali tenere da parte per la verifica finale.
