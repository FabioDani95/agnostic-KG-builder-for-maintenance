# Campagna V3, fase A: manuali di sviluppo

Data: 2026-09-27. Modello GPT-6 Luna (estrazione `low`, revisore agente `medium`),
cancelli gestiti dall'agente (`--gates agent`), tre esecuzioni V3 per manuale e una v22.
Protocollo: [PROTOCOLLO_V3.md](../../paper/evaluation/PROTOCOLLO_V3.md). Gold annotato a mano
da Fabio Daniele, senza assistenti AI, prima di ogni esecuzione.

Sono **misure di sviluppo**: i tre manuali sono stati usati per correggere il codice e
restano di sviluppo per sempre. Non sono risultati di generalizzazione per il paper.

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

## Trane (test): gold ricollegato

Gli ID del gold Trane sono stati ricollegati e verificati riga per riga
([remap_ids_verified.json](../trane_rtac_chiller/gold/remap_ids_verified.json)). Limite
del lettore osservato, non corretto perché Trane è di test: nelle tabelle diagnostiche il
nome di un codice è spezzato in più segmenti, le colonne sono interlacciate, l'intestazione
"Level" è incollata alla prima riga e alcune parole sono unite ("1Starter 1A"). Non è stato
possibile riprodurre la lettura su cui era stato annotato il foglio: unisce il testo di una
riga visiva tra le colonne e non corrisponde a nessuna modalità di PyMuPDF 1.28 installato.
