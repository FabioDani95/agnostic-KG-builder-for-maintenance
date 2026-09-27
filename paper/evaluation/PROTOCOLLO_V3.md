# Protocollo di valutazione V3

Stato: **approvato da Fabio il 2026-09-27** (KPI, budget, un solo annotatore). Riprende [PROTOCOL.md](PROTOCOL.md) e lo rende
operativo per l'architettura V3 ([piano](../../docs/PIANO_V3.md)). Nessun risultato è
contenuto qui: solo come si costruisce il gold, cosa si misura e in che ordine.

## 1. Le tre fasi

| Fase | Manuali | Cosa si fa | Regola |
| --- | --- | --- | --- |
| A. Sviluppo esteso | i 4 attuali più 2–3 nuovi | gold, esecuzioni, analisi degli errori, miglioramenti dell'architettura | un manuale usato per cambiare il codice resta di sviluppo per sempre |
| B. Congelamento | nessuno | tag git del codice, configurazione e prompt; nessuna modifica dopo | una correzione dopo il congelamento riapre la fase A |
| C. Test finale | 6–8 manuali mai visti | gold consolidato prima delle esecuzioni, 3 esecuzioni per manuale, v22 come confronto | nessuno guarda gli output del test prima che il gold sia chiuso |

La fase C è la "prova vera" dell'architettura pulita: è l'unica i cui numeri possono
andare nel paper come risultato di generalizzazione.

## 2. Scelta dei manuali

Dalla ricognizione dei candidati (`paper/manuals/candidate_troubleshooting_manuals.md`),
proposta da confermare:

- **Sviluppo esteso (A):** 2–3 manuali con strutture che i 4 attuali non coprono bene,
  per esempio un manuale a codici di allarme (ABB ACS580 o GSK AE-80), una tabella con
  codici causa (Grundfos Paco) e un manuale di propulsione con grafici sintomo-guasto
  (Yanmar JH-CR).
- **Test (C):** 6–8 manuali di produttori e settori diversi, mai aperti durante lo
  sviluppo, con un equilibrio tra tabelle (Genie, Atlas Copco, Graco GTX, SEW-EURODRIVE),
  prosa e procedure (Lincoln, Trane, TMC, Haas).

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
qualsiasi esecuzione, 3 esecuzioni V3 e una v22, KPI, revisione cieca della precisione.
Solo in fase A seguono l'analisi degli errori e le correzioni dell'architettura, sempre
con regole strutturali e non legate a un produttore, e ogni correzione con un test.

## Budget

Tetto di **10 USD per l'intera campagna** (fasi A e C, esecuzioni, v22 e giudice), su un
registro separato: `campaign/real_call_budget.jsonl`. Gli script lo
usano per impostazione predefinita; il registro blocca ogni chiamata oltre il tetto.
Stima: circa 0,15 USD per un'esecuzione V3 di un manuale di 200 pagine, fino a 0,12 USD
per la v22, pochi centesimi per il giudice.

## Decisioni aperte

1. Quali manuali in sviluppo esteso e quali nel test.
