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

## Livello 1: prima e dopo (2026-09-27, sera)

Correzioni del commit `5f94c6a`, scelte con Fabio dopo l'analisi delle perdite: mappa letta due
volte con pagine confermate che il cancello non può togliere; relazioni con nomi giudicati
diversi dalle due letture separate invece che fuse; rimedio della cella unita proposto per ogni
riga che la ripete e tenuto solo se il verificatore lo conferma; cause dedotte da un controllo
ammesse ma marcate "non scritte nel manuale" (opzione b di Fabio), con il giudice dei KPI che le
mostra senza nome dove il gold non nomina la causa. Prima: `runs_B` (codice del tag
`v3-freeze-2026-09-27`, [kpi_B.md](kpi_B.md)); dopo: `runs` ([kpi_C.md](kpi_C.md)). La v22 non è
stata rieseguita.

| Manuale | Rami gold | Prima (r1, r2, r3) | Dopo (r1, r2, r3) | Asserzioni prima | Asserzioni dopo | Mappa prima | Mappa dopo | Cause dedotte dopo | v22 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Atlas Copco | 49 | 44, 42, 43 | 43, 41, 44 | 58–60/66 | 57–60/66 | 2/2 | 2/2 | 0 | 0 |
| Graco GTX | 19 | 15, 13, 18 | 17, 17, 17 | 39–44/45 | 43/45 | 2/2 | 2/2 | 0 | 10 |
| Haas | 45 | 32, 1, 31 | 35, 28, 35 | 3–38/57 | 33–41/57 | 2–8/9 | 6–8/9 | 4–11 | 8 |
| ABB | 19 | 6, 6, 2 | 7, 4, 7 | 6–12/38 | 6–16/38 | 4–5/11 | 3–7/11 | 2–8 | 0 |
| Grundfos | 146 | 139, 137, 140 | 141, 143, 140 | 137–140/146 | 140–143/146 | 1/1 | 1/1 | 0–1 | 0 |
| Lincoln | 22 | 1, 5, 7 | 5, 3, 5 | 12–29/47 | 24–29/47 | 3/3 | 3/3 | 9–17 | 1 |

| Rami, tre esecuzioni per manuale | Prima | Dopo |
| --- | --- | --- |
| Tutti i sei manuali | 682/900 = 75,8% [0,729; 0,785] | 732/900 = 81,3% [0,787; 0,837] |
| Atlas Copco, Graco, Haas | 239/339 = 70,5% [0,654; 0,751] | 277/339 = 81,7% [0,772; 0,855] |
| ABB, Grundfos, Lincoln | 443/561 = 79,0% [0,754; 0,821] | 455/561 = 81,1% [0,777; 0,841] |

IC95 Wilson. Domande arrivate a una persona dopo: 0–1 per esecuzione. Costo V3 dopo: 0,028–0,114
USD per manuale per tre esecuzioni (la mappa letta due volte costa poco). Spesa del registro dopo
il giro e i KPI: 2,196 USD su 10.

Attenzione nella lettura:

- **Da ora anche Atlas Copco, Graco e Haas sono di messa a punto**: il livello 1 è nato anche
  dai loro errori. I numeri "dopo" sono di sviluppo; restano valide come prova su manuali nuovi
  solo le prime esecuzioni (prima, 70,5%).
- **Il giudice cambia di 0–4 rami** tra una valutazione e l'altra delle stesse esecuzioni:
  Atlas Copco e Grundfos sono invariati entro il rumore.
- **Il guadagno viene soprattutto da Haas** (esecuzione peggiore da 1 a 28 rami), da Graco
  (stabile a 17/19) e da Lincoln sulle asserzioni.

Limiti rimasti:

- **Mappa di Haas r2**: solo una delle due letture ha segnato le pp. 141–142 come diagnostiche e
  il revisore agente le ha tolte; la protezione vale solo per le pagine confermate da entrambe.
- **ABB**: la mappa legge ancora 3–7 pagine gold su 11.
- **Lincoln**: 11 asserzioni per esecuzione restano perse. Il manuale scrive due volte
  "contattare l'assistenza" (subito, oppure "se il problema persiste"); la V3 le tiene come
  un'azione sola con la condizione sulla relazione, e il giudice dei KPI non vede le condizioni.
- Perdite dopo il livello 1, stesse categorie: 173 estratte ma diverse o incomplete, 56 per la
  mappa, 13 nulla estratto (erano 211, 86 e 16).

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

## Robustezza fasi 1–2: confronto C → D e verifica sui PDF (2026-09-27)

**Esito: implementazione completata, criteri di qualità non tutti raggiunti.** Le fusioni
che violano vincoli espliciti scendono da 8 a 0, ma il recall passa da 733/900 a
684/900 (81,4% → 76,0%), le cause orfane da 34 a 35 e restano errori di significato.
Non è un grafo validato per fornire autonomamente istruzioni di manutenzione.

F1–F7 e M1–M3 sono implementati con prove automatiche. I 18 nuovi run D usano il
codice congelato `8abec90`, tre per ciascuno dei sei manuali, con GPT-6 Luna e lo
stesso profilo della campagna. Gli originali sono in `runs_C/`, verificati contro
gli hash iniziali; i nuovi sono in `runs/`. Il giudice aggiornato, a tre voti,
rivaluta sia C sia D: [prima](kpi_C_context.json), [dopo](kpi_D.json),
[manifest](robustness_manifest.json). I 732/900 del precedente giudizio restano
in `kpi_C.json`; non vengono trasferiti al nuovo valutatore. Non sono confronti
su manuali mai visti: tutti e sei sono ormai di sviluppo.

### Misure prima e dopo

I conteggi seguenti sommano tre esecuzioni. Zero violazioni significa rispetto
dei vincoli `different` e numerici, non assenza di fusioni semanticamente errate.

| Manuale | Rami | Asserzioni | Fusioni vietate | Cause orfane | Problemi senza azioni | Jaccard | Domande a persona (r1/r2/r3) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ABB ACS580 | 17/57 → 21/57 | 31/114 → 45/114 | 3 → 0 | 16 → 10 | 17 → 16 | 0.0657 → 0.0795 | 0/0/0 → 0/1/0 |
| Atlas Copco | 127/147 → 85/147 | 175/198 → 115/198 | 0 → 0 | 3 → 0 | 1 → 0 | 0.3643 → 0.133 | 0/0/0 → 0/0/0 |
| Graco GTX | 51/57 → 51/57 | 129/135 → 129/135 | 0 → 0 | 0 → 0 | 0 → 0 | 0.5732 → 0.6053 | 0/0/0 → 0/0/0 |
| Grundfos Paco | 421/438 → 420/438 | 421/438 → 420/438 | 1 → 0 | 0 → 0 | 70 → 30 | 0.343 → 0.4203 | 0/0/0 → 0/0/0 |
| Haas Mill | 101/135 → 93/135 | 118/171 → 109/171 | 1 → 0 | 12 → 24 | 62 → 71 | 0.0562 → 0.1109 | 0/1/0 → 0/0/0 |
| Lincoln POWER MIG | 16/66 → 14/66 | 80/141 → 75/141 | 3 → 0 | 3 → 1 | 0 → 0 | 0.1071 → 0.1466 | 0/0/0 → 0/0/0 |

| Manuale | USD costruzione, 3 run C → D | Secondi pipeline, media C → D | Secondi PDF + pipeline, media D |
| --- | --- | --- | --- |
| ABB ACS580 | 0.1137 → 0.1337 | 90.5 → 112.6 | 291.2 |
| Atlas Copco | 0.0567 → 0.0490 | 87.8 → 76.4 | 81.2 |
| Graco GTX | 0.0278 → 0.0262 | 44.2 → 44.2 | 46.9 |
| Grundfos Paco | 0.0537 → 0.0488 | 73.0 → 72.3 | 75.5 |
| Haas Mill | 0.0992 → 0.1230 | 105.6 → 118.0 | 129.6 |
| Lincoln POWER MIG | 0.0495 → 0.0743 | 77.7 → 82.0 | 89.9 |

Il costo di costruzione esclude la valutazione dei KPI e il lavoro umano. Il tempo PDF non era registrato in C.


| Manuale | Rami C, r1/r2/r3 | Rami D, r1/r2/r3 | Denominatore per run |
| --- | --- | --- | --- |
| ABB ACS580 | 7, 4, 6 | 8, 7, 6 | 19 |
| Atlas Copco | 42, 41, 44 | 42, 43, 0 | 49 |
| Graco GTX | 17, 17, 17 | 18, 18, 15 | 19 |
| Grundfos Paco | 142, 142, 137 | 142, 141, 137 | 146 |
| Haas Mill | 36, 28, 37 | 32, 33, 28 | 45 |
| Lincoln POWER MIG | 8, 2, 6 | 6, 4, 4 | 22 |

Recall macro, con uguale peso ai sei manuali: **66,8% → 61,7%**. Separando i tipi
di gold, i rami con azioni passano da **260/396 (65,7%) a 209/396 (52,8%)**; quelli
con sole cause da **473/504 a 475/504**. Grundfos pesa 146 dei 300 rami per singola
esecuzione e la sua sezione non prescrive rimedi. Il totale micro descrive quindi
male, da solo, la qualità dei percorsi operativi. Questa scomposizione riusa gli
stessi giudizi, senza nuove chiamate e senza cambiare il gold.

Le tre repliche non sono 900 osservazioni indipendenti. Gli intervalli di Wilson
conservati nei KPI non certificano generalizzazione a nuovi produttori. Jaccard
misura nomi normalizzati: risente delle parafrasi e può essere alto anche per
errori ripetuti. I problemi senza azioni di Grundfos sono coerenti con la fonte;
la metrica non distingue automaticamente lacune reali e assenze documentali.
I sei duplicati nominali di Lincoln sono tre ErrorCode con nomi uguali e codici
diversi in ciascun run: un altro motivo per non trattare ogni segnalazione come
errore semantico.

### Correzioni verificate e limiti rimasti

- **Identità.** Il replay offline degli stati C elimina tutte le 8 violazioni
  misurate senza nuove chiamate. I nomi dedotti di Lincoln — interruttore non ON,
  guaina/punta ostruita, selettore spool gun errato — restano identità distinte
  quando presenti nei nuovi run. Vincoli `different` e numerici valgono anche
  attraverso unioni transitive e codici identici. [Replay](merge_replay_final_summary.json),
  [esempi](lincoln_identity_replay_examples.json).
- **Geometria.** Verificati gli ID invariati su tutti e sei i PDF. ABB
  `p232.t1.r5` non eredita più il testo del LED rosso; Lincoln `p28.t1.r4`
  conserva la vera cella unita. [Audit del lettore](reader_final_audit.json).
- **Numeri.** L'applicazione offline a Grundfos C/r2 elimina i 40 falsi ErrorCode
  dell'elenco. Nei tre nuovi run non rimangono ErrorCode numerici; il riferimento
  alla voce 41 è segnalato e non inventato. Le voci 17 e 18 (prevalenza maggiore e
  minore di quella nominale) restano distinte.
- **Graco, pp. 8–9.** Il prerequisito di scaricare la pressione è presente su
  tutti i 24/21/27 archi di azione esportati nei tre run, anche nella continuazione
  a pagina 9. È un miglioramento verificato sul contesto, senza aumento del
  recall aggregato.
- **ABB, p. 232.** Rimane una fusione errata: in D/r1 il LED blu *blinking*
  (disponibile per pairing) e *flickering* (trasferimento dati) sono sinonimi per
  il giudice. Il vincolo F1 non può correggere un verdetto `same` sbagliato.
  Stati Bluetooth normali sono inoltre rappresentati come FailureMode.
- **Atlas, p. 43.** Per il disco paraspruzzi che tocca la carcassa/tubo, la fonte
  prescrive assistenza, mentre il ramo vicino prescrive anche arresto immediato.
  In D/r1 il nuovo controllo non dà la prova strutturale alla coppia incrociata e
  il revisore la rifiuta, malgrado il verificatore l'avesse approvata. Resta però
  assente anche l'azione corretta di sola assistenza. Il problema ha altre azioni,
  perciò la sola navigabilità problema→azione non rileva questa lacuna di causa.
- **Haas, pp. 144 e 160.** Il divieto di spegnere il robot è perso nel grafo r1,
  benché presente in una proposta: dopo la separazione delle cause, quella
  proposta perde i testimoni e viene esclusa senza una nuova revisione. In r2
  manca l'azione sulle batterie; in r3 il divieto è correttamente un `warning`.
  Beep e LED rosso sono `expected` in r2/r3; r1 non produce relazioni per la
  procedura selezionata. R3 ordina erroneamente G04 dopo il contatto con lo stilo,
  mentre il PDF mette tutti i comandi MDI prima. La lettura delle colonne e la
  propagazione dei testimoni restano punti deboli.
- **Disaccordo col KPI.** Haas D/r3 conserva il divieto come avvertenza sull'azione,
  ma `R37.2` risulta mancante perché il gold lo rappresenta come azione separata.
  È un falso negativo osservato in questo controllo mirato; i punteggi congelati
  non sono stati corretti a mano. Anche il valutatore deve essere verificato
  rispetto a rappresentazioni equivalenti.

Questi riscontri derivano dall'ispezione delle pagine PDF complete e degli archi,
con traccia in [source_checks_D.json](source_checks_D.json) e
[qualitative_review_D.json](qualitative_review_D.json). Sono controlli mirati,
esposti alle predizioni, **non una stima cieca della precisione**.

### Regressione Atlas e correzione successiva, separata dal confronto

Atlas D/r3 genera 118 e 121 entità nelle due letture, ma nessuna relazione.
Le note di ambiguità citano tutte le righe e impediscono la rilettura di copertura;
il gate automatico restituisce ugualmente `approved`. Il run resta nel totale
D con **0/49 rami**. Non è rumore del giudice: è un fallimento di estrazione.
Le due repliche non vuote recuperano 42 e 43/49, ma non si può eliminare la terza
per presentare un risultato migliore.

La correzione successiva `bec1e7c`, con test prima falliti e poi superati, consente
una sola rilettura quando non esiste alcuna relazione, contabilizza anche i suoi
fallimenti e marca `incomplete` un risultato con unità vuote/letture fallite o
nessun arco esportabile. Le note diventano visibili nel rapporto. Un'unità vuota
può anche essere una selezione impropria della mappa: la segnalazione chiede una
verifica, non asserisce che la fonte contenga necessariamente un guasto.
Il controllo offline trova unità senza proposte in 7 dei 18 run D
([audit](run_completeness_audit_D.json)); i loro stati storici non sono riscritti.

Un esperimento controllato riutilizza **esattamente le due risposte Atlas vuote**
e la mappa originale, poi riesegue recupero, verifica, unione e revisione con
chiamate nuove. Produce 147 proposte, 124 relazioni verdi e **34/49 rami** al
medesimo valutatore: [manifest e input](empty_extraction_probe/manifest.json),
[KPI](empty_extraction_probe/kpi.json), codice `bec1e7c`. Costo incrementale di
costruzione 0,018347 USD, giudice 0,025444 USD. È una prova del recupero del difetto,
non una nuova replica indipendente e non una dimostrazione di stabilità del
codice finale sui sei manuali. Non viene sostituito a D/r3 nei KPI né nel campione.

### Accettazione

- Fusioni vietate: **raggiunto, 0 violazioni in 18 run**; non equivale a zero fusioni sbagliate.
- Numeri di elenco scambiati per ErrorCode: **nessuno nei tre Grundfos nuovi**.
- Domande a persona: **0–1 per run, entro 10 anche sommando le tre repliche per manuale**;
  questo conta le domande offerte, non minuti umani o qualità della revisione.
  L’unica domanda rimasta (ABB/r2) riguarda la mappa delle pagine, dopo una risposta
  agente troncata: una sola domanda può comportare molto lavoro.
- Navigabilità: **parziale**. Problemi senza azioni 150→117, ma cause orfane
  34→35; Haas peggiora 12→24. Zero su Atlas r3 dipende dal grafo vuoto.
- Recall: **non raggiunto per Atlas**. Haas varia 36/28/37→32/33/28: -8 rami
  cumulati, con -9 nella terza replica; non va nascosto come semplice rumore.
  Le perdite riguardano soprattutto gli avvisi di p. 142 (R12–R15, R17 e R18), alcune
  istruzioni p. 144–145 e il caso di rappresentazione R37.2. Separazione più
  prudente, selezione/estrazione e giudizi semantici contribuiscono; senza
  ablation non si attribuisce causalmente tutta la variazione a un singolo fix.
- Contesto e precisione: **non validati globalmente**; i controesempi sopra
  impediscono di dichiarare risolta la fedeltà operativa.

### Costo, revisione e prossime prove

Spesa aggiuntiva contabilizzata **1,113197 USD**, entro i **5 USD** autorizzati.
Il registro passa da 2,204403 a **3,317600 USD**, senza prenotazioni attive.
La costruzione dei 18 grafi costa circa 0,455122 USD; i giudici prima/dopo circa
0,307426 e 0,306892 USD. Il resto è il recupero controllato. Valori dei report
arrotondati; il [registro di chiusura](robustness_budget_close.json) usa il costo
contabilizzato effettivo per il tetto. I tempi per manuale comprendono ora anche
la lettura del PDF; su ABB questa spiega gran parte del tempo totale. Nessuna
misura di minuti umani è stata inventata.

**Fabio deve rivedere le 61 coppie candidate** in `campaign/*/gold/contrastive.json`
(`keep`/`drop`). I risultati contrastivi attuali sono provvisori e riusano i
medesimi candidati/voti dei KPI, quindi non aggiungono chiamate. Le coppie
separate con azioni proprie non escludono ulteriori archi sbagliati.

Preparato il nuovo [foglio cieco 2](precision/REVISIONE_PRECISIONE_2.md): **108 voci**,
con **20** tratte esclusivamente da pagine fuori dal gold. La provenienza è solo
nella chiave separata; tutti i giudizi sono `?`. Il foglio originale è preservato.
Fabio compila i fogli e registra il tempo; non aprire le chiavi prima. Lo strato
esterno è sovracampionato: un totale non pesato descrive il campione, non tutta
la popolazione degli archi. La precisione resta non misurata.

Le [note su metriche e letteratura](../../docs/NOTE_VALUTAZIONE_ROBUSTEZZA.md)
propongono un audit in entrambe le direzioni (manuale→grafo e grafo→manuale),
prove di esclusione dei rimedi e mutazioni controllate di ordine/condizioni,
e costo per ramo verificato corretto includendo la revisione umana. RAGChecker,
KGCQual e FinReflectKG-EvalBench sono riferimenti metodologici, senza trasferire
qui i loro numeri o rivendicare novità già dimostrata.

Verifica finale del codice: **116 test superati**, Ruff verde. Nessuna modifica
agli ID, ai gold esistenti o alle risposte umane; [verifica di conservazione](preservation_audit_D.json).
La correzione successiva al freeze è identificata separatamente: il confronto
completo D non viene attribuito al codice finale senza una nuova campagna.
