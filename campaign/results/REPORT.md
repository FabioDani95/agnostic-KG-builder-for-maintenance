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

## Iterazione F: pagine calde, diagrammi e prova letta nel contesto (2026-09-28)

Brief: [PROMPT_ITERAZIONE_F.md](../../docs/PROMPT_ITERAZIONE_F.md). Prima = esecuzioni E per i sei
manuali (`runs_E/`) e primo contatto per Grizzly e LG (`runs_first_contact/`, tag
`v3-freeze-2026-09-28`); dopo = esecuzioni F (`runs/`), **stesso valutatore**. Da ora anche Grizzly e
LG sono manuali di sviluppo: le correzioni sono nate dai loro errori, quindi i loro numeri "dopo"
non misurano la generalizzazione (restano validi i numeri di primo contatto).

### Diagnosi offline, prima di spendere

Con le esecuzioni salvate e l'archivio del giudice (ogni coppia giudicata ritrovata senza chiamate):

- **Grizzly:** il 60–80% delle perdite è su pagine mai lette. La mappa vede solo un riassunto di
  480 caratteri per pagina, e il cancello della mappa (agente) **toglieva** pagine gold che una
  lettura aveva tenuto: Grizzly pp. 50, 60–62; ABB pp. 374, 380, 391; LG p. 27.
- **LG:** le unità di lettura si spezzavano a ogni cambio del nome di sezione, e la mappa dà nomi di
  sezione pagina per pagina: il diagramma "No Heat / No Cook" diventava tre unità (titolo a p. 18,
  passi 1–7 a pp. 19–20, passi 8–12 a p. 21). I passi di p. 21 non vedevano il sintomo: tutte cause
  orfane (rami R40–R44 mai ritrovati). Il verificatore vedeva solo i segmenti citati.
- **Regressione di token dell'iterazione E:** non viene dall'estrazione ma dal giudice delle fusioni
  (fino a 105 mila token per chiamata, 654 mila per un'esecuzione di Lincoln) e dal verificatore
  (710 mila token nella stessa esecuzione).

### Cosa è cambiato (un commit e un test per ciascuna)

1. **Unità per diagramma, non per nome di sezione** (`f702c73`). Le pagine diagnostiche consecutive si
   leggono insieme e si tagliano solo per dimensione; una sezione, come una tabella, inizia
   un'unità nuova se ci sta intera; il taglio cade all'inizio di una pagina. Un'unità tagliata dopo
   legge come contesto i primi segmenti delle tre pagine precedenti (i titoli). LG passa da circa 20
   a 6–8 unità e le pp. 15–21 (tre diagrammi interi) stanno in una sola.
2. **Scansione del testo intero per le pagine calde** (`e87e614`). Una lettura di tutto il manuale, a
   blocchi di circa 24 mila caratteri, restituisce i segmenti che contengono conoscenza diagnostica
   ("ispeziona per ostruzioni e pulisci", allarmi, codici, test con valori attesi). Una pagina conta
   solo con prove sulla sua pagina; si legge e il cancello non può toglierla. Prova reale
   ([scan_probe.json](iteration_F/scan_probe.json)): pagine gold trovate 19/20 Grizzly, 10/11 ABB,
   9/9 Haas, 21/24 LG (le tre mancanti sono lette dalla mappa); 0,004–0,061 USD per manuale. Un primo
   prompt segnalava anche le avvertenze di sicurezza generiche (26 pagine in più su Grizzly):
   escluse, 18 in più.
3. **Il verificatore legge il passaggio** (`2b192ca`, principio 3b). La verifica è raggruppata per
   unità: il verificatore riceve l'unità intera con il contesto, poi gli enunciati con gli ID citati,
   e giudica se il manuale, letto come lo legge un tecnico (titoli, colonne, passi numerati, esiti
   sì/no), dice la relazione e se i segmenti citati sono quelli giusti. Unire parti di voci diverse
   resta "non sostenuto". Il testimone della stessa riga resta.
4. **Immagini delle pagine a diagramma** (`9fd77d1`). Una pagina con almeno 8 segmenti di testo fuori
   dalle tabelle, metà dei quali sotto i 40 caratteri, è una pagina di layout (regola sulla sola
   lunghezza, nessuna parola). Estrazione e verifica ricevono l'immagine (al massimo 6 per chiamata)
   e ogni segmento porta la sua posizione `@x,y` in percentuale: il modello segue frecce e riquadri e
   cita comunque gli ID. Il `TESTO.md` non cambia.
5. **Regole per bivi e test** (`ec98792`, `62e90ae`). Ogni esito di un bivio che prescrive
   un'azione è un record: problema del diagramma (dal titolo, un solo problema per diagramma),
   causa rivelata dall'esito (non scritta), test come controllo, azione come riparazione, esito come
   condizione. Un test con valore normale è un controllo con contesto `expected`; un test di
   componente senza sintomo ha il problema "Suspected <componente> fault". Una causa sotto un titolo
   che nomina la sua situazione è collegata a quel problema.
6. **Che cosa afferma un collegamento a una causa non nominata** (`052e1f5`). Nella prima prova su LG
   il verificatore con il passaggio accettava i rimedi dei bivi ma rifiutava quasi tutti i
   collegamenti problema → causa non scritta ("No heat / no cook" → "Faulty high voltage
   transformer"): l'enunciato non diceva che cosa verificare. Ora dice che la voce del problema
   (riga, elenco, o diagramma che parte dal problema) porta a quel controllo, esito o rimedio. Sulle
   stesse estrazioni salvate: "non sostenuto" da 113 a 90, verdi da 421 a 436.
7. **Una causa dedotta che ripete il problema diventa non nominata** (`bafa713`). Prima valeva solo per
   le cause dichiarate scritte. Su Grizzly "Exhaust ducting leaks" → causa "Exhaust ducting leaks"
   restava e revisore e verificatore bocciavano il ramo intero.
8. **Token e tempo** (`978f5f5`, `963e8fc`). Il giudice delle fusioni scrive il contesto di ogni nome
   una volta per chiamata, con al più 3 segmenti dove il nome è scritto: offline sullo stato salvato
   l'ingresso scende al 44–77% (Lincoln r1 da 3,08 a 1,35 milioni di caratteri). Il revisore agente
   risponde a 8 domande alla volta invece di 4.
9. **Foglio cieco dei collegamenti nuovi** (`0b49383`): `campaign.py precision --sheet 3
   --links-before runs_E,runs_first_contact`.

### Prima e dopo (tre esecuzioni per manuale, stesso valutatore)

Prima: [kpi_E.json](kpi_E.json), [kpi_test_grizzly.json](kpi_test_grizzly.json),
[kpi_first_contact_lg.json](kpi_first_contact_lg.json) e i rispettivi `quality_*`. Dopo:
[kpi_F.json](kpi_F.json) (giudicato un manuale alla volta, parti in `kpi_F_parts/`),
[quality_F.json](quality_F.json). Costo per esecuzione dal registro, tempo della pipeline senza la
lettura del PDF; per costo e tempo "dopo" contano solo le esecuzioni non riprese (vedi sotto).

| Manuale | Rami gold | Rami prima (r1, r2, r3) | **Rami dopo (r1, r2, r3)** | Asserzioni prima → dopo | Pagine gold lette prima → dopo | Cause orfane prima → dopo | Fusioni vietate dopo | Domande a persona dopo | USD per esecuzione prima → dopo | Secondi per esecuzione prima → dopo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Atlas Copco | 49 | 44, 41, 44 | **non giudicato** | 57–60 → n/d /66 | 2 → 2 /2 | 0 → 6–12 | 0 | 2–3 | 0,035 → 0,116 | 132 → 344 |
| Graco GTX | 19 | 19, 17, 15 | **19, 17, 16** | 41–45 → 41–45 /45 | 2 → 2 /2 | 0 → 0–2 | 0 | 0 | 0,023 → 0,022 | 80 → 113 |
| Haas | 45 | 35, 36, 35 | **36, 35, 37** | 41 → 42–49 /57 | 8 → 9 /9 | 2–6 → 1–8 | 0 | 0–1 | 0,059 → 0,145 | 173 → 322 |
| ABB (406 pagine) | 19 | 5, 8, 6 | **9, 11, 7** | 8–19 → 18–21 /38 | 7–8 → 11 /11 | 7–12 → 12–16 | 0 | 1–3 | 0,072 → 0,249 | 216 → 489 |
| Grundfos | 146 | 140, 138, 138 | **non giudicato** | 138–140 → n/d /146 | 1 → 1 /1 | 0 → 5–11 | 0 | 6–10 | 0,022 → 0,081 | 94 → 264 |
| Lincoln | 22 | 5, 4, 6 | **14, 14, 2** | 17–25 → 18–37 /47 | 3 → 3 /3 | 0–12 → 6–12 | 0 | 0 | 0,112 → 0,142 | 181 → 250 |
| Grizzly | 62 | 29, 32, 30 | **32, 32, 34** | 86–88 → 85–107 /160 | 6–8 → 18 /20 | 1–5 → 36–54 | 0 | 0–4 | 0,082 → 0,231 | 206 → 472 |
| LG | 74 | 25, 22, 22 | **27, 26, 22** | 44–68 → 64–90 /234 | 21–22 → 24 /24 | 37–50 → 10–16 | 0 | 8–10 | 0,155 → 0,163 | 391 → 362 |

Rami, tre esecuzioni, sui sei manuali giudicati: **351/723 = 48,5% [0,449; 0,522] → 390/723 = 53,9%
[0,503; 0,575]** (IC95 Wilson). Graco, Haas, ABB e Lincoln: 191/315 → 217/315 (60,6% → 68,9%);
Grizzly 91/186 → 98/186; LG 69/222 → 75/222. Il giudice cambia di 0–4 rami tra valutazioni
delle stesse esecuzioni: oltre il rumore solo ABB (+8 su tre esecuzioni), Lincoln (+15, ma r3 cade a
2) e l'insieme di Grizzly e LG nelle zone mirate (sotto). Atlas Copco e Grundfos non sono giudicati:
il tetto di spesa non bastava (vedi "Costo").

Zone di Grizzly e LG (rami per esecuzione, prima → dopo):

| Manuale | Zona | Rami gold | Prima (r1, r2, r3) | Dopo (r1, r2, r3) |
| --- | --- | --- | --- | --- |
| Grizzly | tabelle di troubleshooting, pp. 51–52 | 34 | 29, 32, 29 | 25, 23, 32 |
| Grizzly | conoscenza sparsa (codici p. 9, allarme p. 32, amperometro p. 37, manutenzione pp. 42–64) | 28 | 0, 0, 1 | **7, 9, 2** |
| LG | precauzioni pp. 2, 11 | 8 | 0, 1, 1 | 1, 1, 0 |
| LG | autodiagnosi e codici p. 12 | 8 | 3, 3, 3 | 3, 3, 3 |
| LG | controlli di base p. 13 | 5 | 5, 5, 5 | 5, 5, 5 |
| LG | diagrammi di flusso pp. 14–24 | 35 | 13, 13, 12 | **17**, 11, 13 |
| LG | test dei componenti pp. 25–33 | 18 | 4, 0, 1 | 1, **6**, 1 |

Una zona è decisa dalle pagine citate dal ramo nel gold (Grizzly: tabelle se tutte in pp. 51–52).
Rami ritrovati in almeno un'esecuzione F e mai prima: Grizzly R6, R7, R10, R13, R15, R16, R17, R27,
R57, R63 (nessun ramo perso del tutto); LG R4, R5, R34, R40–R44, R53, R60, R69, R70, R71, R74 (persi:
R1, R27, R35, R47, R48, R63, R67, R73).

### Esempi verificati sul PDF

- **LG p. 21, passi 8–11 del diagramma "No Heat / No Cook"** (mai ritrovati prima: erano un'unità a
  sé senza sintomo). Il grafo r1 ha "No heat / no cook" → "connettore del condensatore ad alta
  tensione scollegato" → "ricollega o ripara il connettore" (esito "Yes" del passo 8) e "No heat /
  no cook" → "resistenza del condensatore fuori intervallo" → controllo "misura la resistenza" e
  riparazione "sostituisci il condensatore" (passo 9, "Yes"), con l'esito come condizione `if`,
  citando il titolo p18.b1 e i riquadri di p. 21. Sull'immagine della pagina il passo 11 stampa
  "No → Replace the high voltage Diode" (probabile errore del manuale): il grafo, come il gold,
  segue la logica ("se fuori intervallo, sostituisci").
- **Grizzly p. 37, passo 26** (pagina di uso, mai letta prima): "An ammeter indication exceeding the
  mA rating may be caused by impending laser tube failure, or electrical faults" diventa
  "indicazione dell'amperometro oltre il valore" → "guasto imminente del tubo laser" e → "guasto
  elettrico", con il controllo del passo 26.
- **Grizzly p. 46, passi 4 e 6** (manutenzione delle cinghie): "Verify that left and right belts
  have same deflection, or binding may occur" e "If any belts have cracks or damaged teeth, replace"
  diventano rami con controllo e sostituzione, la seconda con la condizione "se le cinghie hanno
  crepe o denti danneggiati".

### Collegamenti verdi nuovi e precisione

Nell'esecuzione r1 i collegamenti verdi che nessun collegamento verde dell'esecuzione precedente
dice (stesso tipo, nomi simili ai due estremi; stima per nome, quindi le parafrasi contano come
nuove) sono: ABB 111, Atlas 158, Graco 8, Grizzly 301, Grundfos 92, Haas 185, LG 142, Lincoln 83.
Molti vengono dalle pagine in più trovate dalla scansione (ABB 44 pagine lette, Haas 47, Atlas 17,
contro 2–11 del perimetro gold): sono fuori dal gold e la loro precisione **non è misurata**. Foglio
cieco nuovo per Fabio: [REVISIONE_PRECISIONE_3.md](precision/REVISIONE_PRECISIONE_3.md), 72 voci (per
manuale 6 collegamenti nuovi e 3 già presenti come controllo, mescolati; la chiave dice quali). Da
compilare, poi `campaign.py precision --sheet 3 --score`.

### Costo e tempo

Costo per esecuzione salito di 2–3,5 volte su sei manuali: la voce principale è l'estrazione delle
pagine in più, poi la scansione (ABB 0,049 USD, Haas 0,015, gli altri 0,003–0,004). ABB, 406 pagine,
0,23–0,27 USD e 7,8–8,4 minuti per esecuzione (riferimento del brief: 0,25 USD e 10 minuti); Grizzly
0,23 USD e circa 8 minuti per 80 pagine, sopra le attese per le sue dimensioni. Il giudice delle
fusioni e il verificatore non esplodono più: Lincoln r1 da 654 mila a 298 mila token per le fusioni
e da 710 mila a 239 mila per la verifica; su LG le fusioni scendono da 270 a 214 mila, la verifica
sale da 110 a 205 mila token (passaggio intero e immagini).

Spesa: 7,075 → 12,813 USD, cioè 5,74 USD in questa iterazione contro i 5 del brief. Fabio ha alzato
il tetto a 12,5 e poi a 13,0 USD durante il lavoro (proiezioni reali dopo il primo giro). Voci: sonde
e prove di sviluppo circa 1,05 (scansione 0,09, due giri di prova su LG e uno su Grizzly con i
giudizi, sonda di estrazione 0,02); 24 esecuzioni 3,84 (comprese le riprese); giudice 0,85 su 18
esecuzioni. Il giudice di Atlas Copco e Grundfos (circa 0,5 USD stimati a 0,0011 USD per chiamata)
non è stato eseguito per restare entro 13,0.

### Esecuzioni fallite e riprese

- **Difetto del registro con le immagini** (`81ddd4b`). Il gateway prenotava il costo massimo di una
  chiamata contando un token per byte della richiesta, anche per l'immagine in base64: una chiamata
  con sei pagine di diagramma risultava 541 mila token (0,15 USD). Con la spesa oltre 9 USD, poche
  chiamate in parallelo superavano il tetto e il registro le respingeva (`BudgetExceededError`, non
  archiviate). Colpite: LG r2 e r3, Grizzly r3 (verifiche e fusioni respinte) e Grundfos r3 (14
  letture di estrazione fallite, esecuzione `incomplete`). Corretto con una quota fissa di 6.000
  token per immagine; le quattro esecuzioni sono state **riprese dallo stato salvato**, rifacendo
  verifica, fusione e cancelli (e l'estrazione delle unità fallite), con lo stesso codice di
  estrazione. Le versioni fallite restano in `runs_F_budget_failed/`. Nella ripresa ho cancellato per
  errore i cinque file di stato delle letture fallite prima di copiarli; il loro esito resta nel
  rapporto e nel grafo delle versioni fallite.
- Atlas Copco r2: tre timeout della mappa, riprovati con successo. LG r3 ripreso: una risposta
  dell'agente mancata, passata al revisore successivo.
- Il giudice di Graco si è fermato circa mezz'ora con il Mac in sospensione (il limite di tempo per
  chiamata usa un orologio monotono) ed è ripartito da solo.

### Limiti rimasti e risultati negativi

- **Tabelle di Grizzly peggiori in due esecuzioni su tre** (25 e 23 contro 29–32). L'unità delle
  tabelle ora contiene anche p. 53, una pagina di manutenzione trovata dalla scansione; le righe
  producono meno azioni distinte (56–80 contro 87–108) e mancano voci degli elenchi nelle celle
  ("Inspect/replace water chiller system"). Non si separa offline l'effetto dell'unità più lunga da
  quello delle regole nuove. Correzione possibile: una tabella diagnostica che sta da sola non si
  unisce a pagine aggiunte dalla sola scansione.
- **Cause orfane in aumento fuori da LG** (Grizzly 36–54, Atlas 6–12, Grundfos 5–11). Sulle pagine di
  uso e manutenzione il modello nomina lo stato anomalo come causa ("parti allentate") senza un
  problema, e il revisore agente rifiuta "una verifica di manutenzione non è una voce di
  troubleshooting". Ho provato una regola ("se trovi X, fai Y": X è il problema osservato) con una
  sonda su tre unità: su Grizzly pp. 42–44 le proposte sono scese da 97 a 28 e su LG il titolo del
  diagramma è sparito; regola scartata, non misurata sulla campagna.
- **Due problemi per lo stesso diagramma** (titolo e prima domanda) restano in parte su LG: i rami
  del passo 3 di "No Heat" sono collegati a "Product does not operate after power on" e il giudice
  li considera un problema diverso da "No heat / no cook".
- **Rami completi di LG ancora bassi** (22–27/74) nonostante le asserzioni salgano (64–90 contro
  44–68): molti rami gold sono procedure con 5–15 azioni (R8, R54, R58, R59) e basta perderne una.
- **Instabilità di Lincoln** (14, 14, 2): in r3 l'assistenza condizionata ("se il problema persiste,
  contatta l'assistenza") non è collegata; è il limite noto dell'iterazione E.
- **Domande a una persona in aumento** su LG (8–10, al tetto) e Grundfos (6–10): più relazioni con
  il solo testimone del verificatore arrivano al cancello dei dubbi.
- **Non fatto:** grafo esplicito del diagramma dalle frecce del PDF (`get_drawings`), parser scritti
  dal modello come testimone indipendente, recupero per immagini tipo ColPali. Il verificatore e le
  due letture restano lo stesso modello.
- **Controllo del lettore** ([reader_check.json](iteration_F/reader_check.json)): gli ID di tutti gli
  otto manuali coincidono con `TESTO.md` e l'uscita del lettore è identica a prima; il testo delle
  celle differisce già da prima di questa iterazione in cinque `TESTO.md` di sviluppo (Atlas, Graco,
  Haas, Lincoln, ABB), generati prima delle correzioni del lettore delle iterazioni D ed E.

### Quanto delle perdite viene dal giudice

Nelle scomposizioni di sviluppo circa metà-due terzi delle asserzioni perse sono estratte ma giudicate
diverse (LG 79 su 149, Grizzly 27 su 51), il resto manca dal grafo verde. Tra le giudicate diverse
ci sono differenze vere (azioni mancanti) e artefatti della misura: il giudice non vede il nome di una
causa non scritta, quindi i rami di uno stesso sintomo gli sembrano uguali, e considera diversi il
titolo di un diagramma e la sua prima domanda. Per misurarlo: foglio cieco
[REVISIONE_GIUDICE.md](judge_audit/REVISIONE_GIUDICE.md), 40 coppie delle esecuzioni F (32 giudicate
diverse su rami mancati, 8 giudicate uguali come controllo), con le istruzioni in testa; poi
`scripts/kg_v3_judge_audit.py --score`. I voti del giudice vengono dal suo archivio, senza chiamate.

Esito della revisione di Fabio ([risultati](judge_audit/RISULTATI.md)): delle 32 coppie che il giudice
diceva diverse, 7 sono uguali (22%, IC95 0,11–0,39), 21 sono errori veri del sistema (66%) e 4 hanno un
gold discutibile (12%); delle 8 di controllo, 1 era un errore del sistema accettato dal giudice. I rami
mancati mancano quindi per lo più davvero. Errori principali del sistema: rimedio della causa vicina
nelle celle con elenchi numerati (Grizzly), ramo sbagliato dei diagrammi (LG), test dei componenti letti
come guasti che il manuale non afferma (regola 15 da rivedere), assistenza condizionata di Lincoln.

### Proposta

Non propongo ancora un nuovo tag di congelamento: prima giudicare Atlas Copco e Grundfos (circa
0,5 USD) e correggere la regressione delle tabelle di Grizzly, poi congelare. Se Fabio preferisce
congelare ora, il codice da congelare è `81ddd4b`.

## Secondo primo contatto: LG LMH2235ST (2026-09-28)

Service manual di un forno a microonde: codici d'errore, tabella dei controlli di base,
diagrammi di flusso di troubleshooting a bivi sì/no con test di continuità e valori attesi, test
dei componenti. Gold di Fabio Daniele: 74 rami, 234 asserzioni, 24 pagine. Stesso codice di
Grizzly (tag `v3-freeze-2026-09-28`, backend identico). [KPI](kpi_first_contact_lg.md).

| Esecuzione | Rami | Asserzioni | Pagine gold lette | Domande a persona | Cause orfane | USD | Secondi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| r1 | 25/74 | 59/234 | 21/24 | 1 | 37 | 0,145 | 405 |
| r2 | 22/74 | 44/234 | 22/24 | 6 | 50 | 0,160 | 415 |
| r3 | 22/74 | 68/234 | 22/24 | 5 | 44 | 0,162 | 390 |

Rami, tre esecuzioni: 69/222 = 31,1%, IC95 Wilson [0,254; 0,374].

| Zona del manuale | Rami ritrovati (r1, r2, r3) |
| --- | --- |
| Controlli di base, p. 13 | 5, 5, 5 su 5 |
| Codici d'errore, p. 12 | 3, 3, 3 su 8 |
| Diagrammi di flusso, pp. 14–24 | 13, 13, 12 su 35 |
| Test dei componenti, pp. 25–33 | 4, 0, 1 su 18 |

- **Qui la mappa non è il problema:** legge 21–22 delle 24 pagine; l'85–92% delle perdite è su
  pagine lette.
- **Il limite è la struttura a diagramma:** i passi vengono estratti ma non collegati al sintomo
  del diagramma (37–50 cause orfane per esecuzione, contro 1–5 di Grizzly). Il sintomo che apre il
  diagramma è spesso in un riquadro o nell'immagine, e i bivi sì/no con "Go to No. N" non
  diventano rami.
- **Test dei componenti con valori attesi:** quasi assenti (0–4 su 18).
- Fusioni vietate 0. Costo e tempo più alti che su Grizzly (0,15–0,16 USD, 6,5–7 minuti).

## Primo manuale di test: Grizzly G0872 (2026-09-28)

Codice congelato al tag `v3-freeze-2026-09-28`. Gold di Fabio Daniele, a mano e senza assistenti AI,
chiuso prima di ogni esecuzione: 66 rami (62 con causa o azione, 4 solo codice), 164 asserzioni,
20 pagine. Il lettore produce lo stesso `TESTO.md` su cui è stato annotato. Nessuna correzione del
codice deriva da questo manuale. [KPI](kpi_test_grizzly.md).

| Esecuzione | Rami | Asserzioni | Codici | Pagine gold lette | Domande a persona | USD | Secondi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| r1 | 29/62 | 86/160 | 3/4 | 8/20 | 5 | 0,099 | 252 |
| r2 | 32/62 | 88/160 | 1/4 | 6/20 | 0 | 0,080 | 178 |
| r3 | 30/62 | 87/160 | 3/4 | 6/20 | 0 | 0,066 | 189 |

Rami, tre esecuzioni: 91/186 = 48,9%, IC95 Wilson [0,418; 0,561]. Tempo con la lettura del PDF.

- **Tabelle di troubleshooting (pp. 51–52), 34 rami:** 29, 32 e 29 ritrovati (85–94%).
- **Altri 32 rami, sparsi nel manuale** (codici a p. 9, allarme del chiller a p. 32, amperometro
  a p. 37, condizioni di guasto con rimedio nelle pagine di manutenzione 46–64): 4–5 ritrovati.
  Tra il 58% e il 79% delle perdite (43–58 asserzioni per esecuzione) cade su pagine che la mappa
  non ha scelto: la mappa legge i test e le tabelle di troubleshooting, non le condizioni di guasto
  dentro le procedure di manutenzione.
- Qualità strutturale: fusioni vietate 0, archi senza prova 0, cause orfane 1–5 per esecuzione.
- È il primo risultato su un manuale non usato per correggere il codice. Un solo manuale: non
  basta per una conclusione sulla generalizzazione.

## Iterazione E: completezza dei rami (2026-09-28)

Codice: E1–E8 dell'altro agente ([brief](../../docs/PROMPT_ITERAZIONE_E.md)) più quattro correzioni
dopo la code review: limite di tempo rigido per ogni chiamata al modello (un'esecuzione ABB era
rimasta bloccata tre ore), cancello della mappa con al massimo otto domande (erano 284 per ABB),
esecuzione incompleta solo se tutte le unità sono vuote o una lettura fallisce, valutatore che
tratta la condizione del gold come contesto di ramo e le note di sezione come non vincolanti
(con la versione precedente Lincoln scendeva a 0/22 sugli stessi grafi). Le due esecuzioni ABB
fatte prima di queste correzioni sono in `runs_E_aborted/` e non entrano nel confronto.

Prima = esecuzioni D (`runs_D/`), dopo = esecuzioni E (`runs/`), **stesso valutatore** per
entrambe ([kpi_D_final.json](kpi_D_final.json), [kpi_E.json](kpi_E.json)). E7 ed E8 spenti.

| Manuale | Rami gold | D: rami r1, r2, r3 | **E: rami r1, r2, r3** | Asserzioni D → E | Domande a persona E | USD per esecuzione D → E | Secondi per esecuzione D → E |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Atlas Copco | 49 | 42, 42, 0 | **44, 41, 44** | 0–58 → 57–60 /66 | 0 | 0.016 → 0.035 | 81 → 139 |
| Graco GTX | 19 | 18, 18, 16 | **19, 17, 15** | 42–44 → 41–45 /45 | 0 | 0.009 → 0.023 | 47 → 85 |
| Haas | 45 | 30, 33, 28 | **35, 36, 35** | 33–38 → 41 /57 | 0–3 | 0.041 → 0.059 | 130 → 185 |
| ABB | 19 | 6, 7, 6 | **5, 8, 6** | 12–18 → 8–19 /38 | 0–3 | 0.045 → 0.072 | 291 → 394 |
| Grundfos | 146 | 141, 140, 135 | **140, 138, 138** | 135–141 → 138–140 /146 | 0 | 0.016 → 0.022 | 75 → 97 |
| Lincoln | 22 | 3, 3, 1 | **5, 4, 6** | 15–24 → 17–25 /47 | 0–1 | 0.025 → 0.112 | 90 → 187 |

Rami, tre esecuzioni per manuale: **D 669/900 = 74,3% [0,714; 0,771] → E 736/900 = 81,8%
[0,791; 0,842]** (IC95 Wilson). Costo e tempo sono medie per singola esecuzione, dalla lettura del
PDF al grafo, senza il valutatore.

- Nessuna esecuzione vuota; tutte approvate. In D Atlas Copco r3 era vuota (0/49).
- Guadagni oltre il rumore: Haas (+15 rami su 135), Lincoln (+8 su 66), Atlas Copco (+45, quasi
  tutti per l'esecuzione non più vuota). ABB, Graco e Grundfos invariati entro il rumore.
- Fusioni vietate 0 in D e in E. Cause orfane da 35 a 53 e problemi senza azione da 117 a 125:
  peggiorano ([quality_D_final.md](quality_D_final.md), [quality_E.md](quality_E.md)).
- Costo per esecuzione da circa 1,5 a 3–11 centesimi, tempo circa +40%. Causa principale: la mappa
  per sezioni spezza le tabelle in più unità (Lincoln da 1 a 6) e le letture ripetute portano
  tutta l'unità come contesto (Lincoln da 82 mila a 1,5 milioni di token per esecuzione).
- Domande a una persona: 0–3 per esecuzione.
- Spesa del registro dopo il giro e i KPI: 5,929 USD su 10, oltre i 3 USD previsti per
  l'iterazione (fino a 6,3) di circa 0,4 USD compreso il lavoro dell'altro agente.
- Numeri di sviluppo: tutti e sei i manuali sono ormai di messa a punto.

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
