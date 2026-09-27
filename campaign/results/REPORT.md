# Campagna V3, fase A: manuali di sviluppo

Data: 2026-09-27. Modello GPT-6 Luna (estrazione `low`, revisore agente `medium`),
cancelli gestiti dall'agente (`--gates agent`), tre esecuzioni V3 per manuale e una v22.
Protocollo: [PROTOCOLLO_V3.md](../../paper/evaluation/PROTOCOLLO_V3.md). Gold annotato a mano
da Fabio Daniele, senza assistenti AI, prima di ogni esecuzione.

Nessun manuale è mai stato visto dal modello prima di queste esecuzioni. La distinzione che
conta è un'altra: se il **codice** è stato corretto guardando i risultati di quel manuale.

- **Manuali di messa a punto: ABB, Grundfos, Lincoln.** Le due correzioni sono nate dai loro
  errori; i loro numeri dopo le correzioni sono ottimisti.
- **Manuali nuovi per la pipeline: Atlas Copco, Graco GTX, Haas.** Eseguiti per la prima
  volta con il codice già congelato (tag `v3-freeze-2026-09-27`), gold scritto prima, nessuna
  correzione derivata da loro. Queste prime esecuzioni sono una prova su manuali mai visti e
  restano valide anche se il codice cambierà. Limiti: tre manuali, un solo annotatore, e
  Graco è un produttore già presente tra i quattro manuali storici di sviluppo (altro
  prodotto: Check-Mate).

**Decisione di Fabio (2026-09-27, sera):** Trane è eliminato (gold e cartella). Atlas Copco,
Graco GTX e Haas diventano di sviluppo **da ora**: una correzione ricavata dai loro errori
renderà di sviluppo le esecuzioni successive, non queste prime.

### Prima esecuzione su manuali nuovi (codice congelato)

| Gruppo | V3, rami | v22, rami |
| --- | --- | --- |
| Nuovi: Atlas Copco, Graco GTX, Haas | 239/339 = 70,5%, IC95 [0,654; 0,751]; macro 72,0% | 18/113 = 15,9%, IC95 [0,103; 0,238] |
| Messa a punto: ABB, Grundfos, Lincoln | 443/561 = 79,0%, IC95 [0,754; 0,821] | 1/187 = 0,5% |

Tre esecuzioni V3 per manuale nel denominatore, compresa Haas r2 fallita per la mappa.

## Quadro complessivo: sei manuali, codice del tag `v3-freeze-2026-09-27`

Tre esecuzioni V3 e una v22 per manuale ([kpi_B.md](kpi_B.md)). Rami ritrovati:

| Manuale | Rami gold | V3 r1, r2, r3 | v22 | Asserzioni V3 | Mappa (pagine gold lette) |
| --- | --- | --- | --- | --- | --- |
| Grundfos Paco (matrice sintomo/causa) | 146 | 139, 137, 140 | 0 | 137–140/146 | 1/1 |
| Atlas Copco DrB (tabella) | 49 | 44, 42, 43 | 0 | 58–60/66 | 2/2 |
| Graco GTX (tabella) | 19 | 15, 13, 18 | 10 | 39–44/45 | 2/2 |
| Haas mill (procedure e allarmi) | 45 | 32, **1**, 31 | 8 | 3–38/57 | 8, **2**, 8/9 |
| Lincoln POWER MIG (tabella con colonna unita) | 22 | 1, 5, 7 | 1 | 12–29/47 | 3/3 |
| ABB ACS580 (406 pagine, righe sparse) | 19 | 6, 6, 2 | 0 | 6–12/38 | 4–5/11 |
| Totale micro | 900 (3 esecuzioni) | 682 | 19/300 | | |

Recall micro dei rami: V3 682/900 = 75,8%, IC95 Wilson [0,729; 0,785]; v22 19/300 = 6,3%,
IC95 [0,041; 0,097]. Domande arrivate a una persona: 0–1 per esecuzione. Costo V3
0,006–0,028 USD per esecuzione. Spesa del registro dopo questo giro: 1,231 USD su 10.

Letture principali:

- **Le tabelle diagnostiche funzionano** (Grundfos, Atlas Copco, Graco): 70–95% dei rami,
  stabili entro 2–5 rami tra esecuzioni.
- **Il problema più grave è la mappa.** Haas r2 non ha etichettato come diagnostiche le
  pagine 141–146 (tutta la sezione troubleshooting) e ritrova 1 ramo su 45 contro 31–32 delle
  altre esecuzioni; ABB legge 4–5 pagine gold su 11. È anche la prima causa di instabilità.
- **Lincoln**: la cella unita "se il problema persiste, contattare l'assistenza" non viene
  collegata a tutte le righe; un ramo completo richiede anche quell'azione.
- **Prove sul gold** più basse su Haas (0,70–0,75): relazioni giuste citate in segmenti
  diversi da quelli del gold (procedure lunghe).
- **Rumore del giudice:** rivalutando le stesse esecuzioni A2, alcuni valori cambiano di
  0–4 rami (ABB r2 8→6, Lincoln r1 2→1, r2 4→5). Le differenze tra esecuzioni inferiori a
  qualche ramo non vanno interpretate.
- Graco r2 ha impiegato 233 s invece di circa 40 per un ricontrollo lento del fornitore
  (184 s nella verifica), senza effetti sul risultato.

Possibili correzioni ancora strutturali, non applicate: doppia lettura della mappa con
unione delle pagine diagnostiche (una chiamata in più, colpisce direttamente Haas r2 e
ABB); propagazione esplicita delle celle unite di una colonna di rimedio a tutte le righe.

## Dove si perdono i rami (sei manuali, 18 esecuzioni V3)

Ogni asserzione del gold non ritrovata, classificata dai grafi e dai rapporti delle
esecuzioni (categorie assegnate in ordine: mappa, nulla estratto, poi confronto tra gold e archi vicini). Sono 313 perdite su
1.179 asserzioni-esecuzione.

| Causa della perdita | Perdite | Dove |
| --- | --- | --- |
| Mappa: la pagina non viene letta | 86 (27%) | Haas r2 (46), ABB (36) |
| Estratto ma diverso: fusioni di cause simili, rimedio di un'altra riga, azione diversa | 82 (26%) | ABB, Haas, Atlas Copco, Graco |
| Causa non scritta nel manuale, ma la V3 ne scrive una | 64 (20%) | Lincoln (36), ABB (22) |
| Cella unita "se persiste, contattare l'assistenza" non collegata a ogni riga | 35 (11%) | Lincoln |
| Incrocio sintomo-causa della matrice mancante | 23 (7%) | Grundfos |
| Pagina letta ma nulla estratto nei segmenti del gold | 16 (5%) | Haas, ABB |
| Nel gold la causa ripete il problema | 7 (2%) | Haas |

Casi verificati a mano:

- **Fusione di cause diverse.** Atlas Copco: "la valvola della linea di bilanciamento non si
  chiude" diventa "non si apre"; "gioco troppo piccolo per deformazione" diventa "...per
  contaminazione". Il giudice delle fusioni aveva risposto "diversi"; la regola che unisce i
  nomi scelti dalle due letture per la stessa relazione li unisce comunque
  ([merger.py](../../backend/kg_v3/merger.py), `assemble`).
- **Rimedi di righe diverse sulla stessa causa.** Graco: "Material too thick" è un solo nodo
  con i rimedi di tre righe diverse; il contesto del sintomo si perde.
- **Cause dedotte.** Lincoln: "Make sure correct voltage is applied" diventa la causa
  "Incorrect input voltage" anche dopo la correzione 2, verde perché le due letture e il
  verificatore concordano: lo stesso modello sbaglia allo stesso modo nei tre testimoni.
- **Errori del testo del PDF.** Atlas Copco p. 44: "alfunction: ump does not tain its pumping
  eed", lettere perse nello strato di testo.

## Manuali

| Manuale | Pagine | Pagine gold | Rami con causa o azione | Asserzioni | Rami solo codice |
| --- | --- | --- | --- | --- | --- |
| ABB ACS580-01 (convertitore) | 406 | 11 | 19 | 38 | 12 |
| Grundfos Paco VL (pompa) | 22 | 1 | 146 | 146 | 1 |
| Lincoln POWER MIG 215 MP (saldatrice) | 36 | 3 | 22 | 47 | 0 |

## Recall dei rami per iterazione (tre esecuzioni V3)

Un ramo conta solo se tutte le sue asserzioni sono ritrovate (posizione e giudice di
significato a tre voti, [kg_v3_kpi.py](../../scripts/kg_v3_kpi.py)).

| Manuale | v22 | A0 codice iniziale | A1 dopo correzione 1 | A2 dopo correzione 2 |
| --- | --- | --- | --- | --- |
| ABB (19) | 0 | 7, 4, 6 | 7, 6, 4 | 7, 8, 2 |
| Grundfos (146) | 0 | 141, 54, 65 | 141, 142, 141 | 139, 136, 141 |
| Lincoln (22) | 1 | 2, 3, 1 | 3, 1, 3 | 2, 4, 7 |
| Totale micro (561 su tre esecuzioni) | 1/187 | 283 | 448 | 446 |

Asserzioni ritrovate in A2: ABB 10, 19, 6 su 38; Grundfos 139, 136, 141 su 146; Lincoln
14, 20, 29 su 47 (in A1: 9, 6, 12). Recall micro dei rami A2: V3 446/561, IC95 Wilson
[0,760; 0,826]; v22 1/187, IC95 [0,001; 0,030]. Nessun manuale raggiunge l'obiettivo
del 90% su tutte le esecuzioni; la stabilità (≤ 5 punti) è raggiunta solo da Grundfos in A1
e A2. Domande arrivate a una persona: 0–1 per esecuzione. Costo V3: 0,008–0,037 USD per
esecuzione, 50–90 secondi di pipeline più la lettura del PDF.

Tabelle complete: [kpi_A0.md](kpi_A0.md), [kpi_A1.md](kpi_A1.md), [kpi_A2.md](kpi_A2.md).
Esecuzioni: `campaign/<manuale>/runs_A0`, `runs_A1`, `runs` (A2, codice congelato).

## Correzioni (strutturali, ciascuna con un test)

1. **Il revisore vede tutti i segmenti citati** (`7b5b09b`). Le domande mostravano al più
   8 estratti. Una riga di Grundfos con molte cause ne cita di più: il revisore agente
   rifiutava cause confermate dal verificatore perché non le vedeva. Effetto: Grundfos da
   141/54/65 a 141/142/141.
2. **Nessuna causa ricavata rovesciando un controllo o un rimedio** (`736d9f6`, regola
   nelle istruzioni di estrazione e di verifica). Su Lincoln "Check for proper size cable
   liner" diventava la causa "Incorrect cable liner size". Effetto: asserzioni Lincoln da
   9/6/12 a 14/20/29 su 47. Grundfos scende di 0–6 rami, entro una variazione non ancora
   distinguibile dal rumore su tre esecuzioni.

## Errori rimasti (risultati negativi)

- **ABB, mappa.** La diagnostica è fatta di poche righe sparse in 406 pagine (LED e avvisi
  nei capitoli dei moduli opzionali, pp. 374–396). La mappa copre 3–8 delle 11 pagine gold
  e varia tra esecuzioni. Non corretto: una regola per queste pagine rischia di adattarsi
  al solo manuale.
- **Lincoln, azione della colonna unita.** 11 delle 18 asserzioni mancanti nella migliore
  esecuzione sono "se il problema persiste, contattare l'assistenza", cella unita valida per
  tutte le righe; la V3 la collega solo ad alcune.
- **Grundfos, matrice sintomo/causa.** Restano sempre gli stessi 2–5 incroci (R69, R75,
  R84): errore stabile di lettura degli asterischi.
- **Lincoln, cause dedotte.** La correzione 2 riduce ma non elimina il fenomeno: è un
  giudizio del modello, non una regola applicata dal codice.
- **v22.** Quasi nulla su questi manuali (1 ramo su 187 per esecuzione).

## Esecuzioni fallite e ripetute

La v22 su ABB è fallita due volte con HTTP 413 prima di ogni chiamata (PDF di 55 MB oltre i
limiti di upload e di richiesta dell'app). Lo script della baseline ora alza i due limiti;
la terza esecuzione è completata (481 s). Nessuna esecuzione V3 è fallita.

## Costo

Registro [real_call_budget.jsonl](../real_call_budget.jsonl): 0,876 USD su 10 dopo A2,
comprese esecuzioni V3, v22 e giudice dei KPI.

## Precisione

Foglio cieco in [precision/REVISIONE_PRECISIONE.md](precision/REVISIONE_PRECISIONE.md),
48 voci da V3 r1 e v22 di A0 mescolate. Da compilare da Fabio; poi `campaign.py precision
--score`. La precisione non è ancora misurata.

## Trane: gold ricollegato, poi eliminato

Per decisione di Fabio la cartella di Trane è stata eliminata dopo questo lavoro; resta la
cronologia in git (commit `af2b7a0`).

Gli ID del gold Trane sono stati ricollegati e verificati riga per riga
([remap_ids_verified.json](../trane_rtac_chiller/gold/remap_ids_verified.json)). Limite
del lettore osservato, non corretto perché Trane è di test: nelle tabelle diagnostiche il
nome di un codice è spezzato in più segmenti, le colonne sono interlacciate, l'intestazione
"Level" è incollata alla prima riga e alcune parole sono unite ("1Starter 1A"). Non è stato
possibile riprodurre la lettura su cui era stato annotato il foglio: unisce il testo di una
riga visiva tra le colonne e non corrisponde a nessuna modalità di PyMuPDF 1.28 installato.
