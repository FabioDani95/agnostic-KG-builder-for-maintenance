# Implementazione: iterazione E, completezza dei rami senza perdere fedeltà

Lavora nel repository agnostic-KG-builder-for-maintenance, branch `feat/cite-check-ask-v3`.
Prima leggi: `AGENTS.md`, `README.md`, `docs/PIANO_V3.md`, `campaign/results/REPORT.md` (in
particolare la sezione "Robustezza fasi 1–2"), `docs/NOTE_VALUTAZIONE_ROBUSTEZZA.md`,
`paper/evaluation/PROTOCOLLO_V3.md`.

## 0. Obiettivo

Dopo le fasi 1–2 il grafo è più pulito (zero fusioni vietate, celle unite verificate sulla
geometria, niente falsi codici), ma il recupero dei rami è fermo: 684/900 con il giudice aggiornato
(`campaign/results/kpi_D.json`, sei manuali, tre esecuzioni ciascuno). Questa iterazione deve
**recuperare i rami che si perdono senza reintrodurre errori di significato**. Una fusione sbagliata
o un rimedio della voce accanto valgono meno di un ramo mancante.

I 216 rami mancanti, sommando tre esecuzioni:

| Manuale | Mancanti | Causa principale |
| --- | --- | --- |
| Atlas Copco | 62 | circa 43 sono l'esecuzione r3 con grafo vuoto; il resto sono voci vicine nelle celle-elenco |
| Lincoln | 52 | 33 rami dove manca solo l'assistenza condizionata ("se i controlli non risolvono, contattare l'assistenza") |
| Haas | 42 | pagine perse dalla mappa (141–142), procedure, avvertenze |
| ABB | 36 | pagine perse dalla mappa (5–10 su 11), indicazioni che non sono guasti |
| Grundfos | 18 | pochi incroci stabili della matrice |
| Graco | 6 | — |

Obiettivi del sistema, in ordine: copertura dell'intero manuale; rami fedeli; robustezza tra
esecuzioni e produttori; al massimo circa 10 domande a una persona per manuale; grafo pulito,
connesso e navigabile; costo ragionevole. Non sono obiettivi la formulazione esatta dei nomi né
lo stile.

## 1. Regole

- Solo regole **strutturali**, valide per ogni lingua e produttore. Niente parole di una lingua,
  niente casi scritti per un manuale. Il gold serve solo a misurare, mai a selezionare o decidere.
- Il modello comprende e cita ID di segmento; il codice fa conti, prove e identificativi.
- **Un test per ogni correzione**, con un caso che senza la correzione fallisce.
- **Non cambiare gli ID dei segmenti**: i gold li usano. Se una modifica li cambia, fermati e chiedi.
- **Non modificare i gold** (`campaign/*/gold/`). In particolare Lincoln R1.1 e R1.2, dove la
  revisione indica una condizione messa per errore, li decide Fabio: segnala, non correggere.
- Non modificare le esecuzioni passate né `paper/` (salvo poche righe in `STATUS.md`).
- Nessuna interfaccia.
- Chiamate reali solo sul registro `campaign/real_call_budget.jsonl`. Spesa attuale circa 3,3 USD
  su 10. **Tetto di questa iterazione: 3 USD in totale**, comprese esecuzioni, giudice ed
  esperimenti. Controlla con `.venv/bin/python scripts/campaign.py status` prima e dopo ogni
  esecuzione; fermati e chiedi se la stima non basta.
- Ruff e pytest verdi prima di ogni commit. Commit piccoli, uno per punto.
- Riporta anche i risultati negativi. Separa sempre l'effetto della **pipeline** dall'effetto
  della **misura**.

## 2. Punti da implementare

**E1. Nessuna esecuzione fallisce in silenzio.**
- Una lettura vuota o "tutto non chiaro" su un'unità che contiene righe di tabella o passi
  numerati non si accetta: si ripete una volta, poi si divide l'unità a metà e si rilegge.
- Un'unità che resta vuota finisce nel rapporto come `failed_units`.
- Un grafo vuoto, o con unità diagnostiche fallite, non può essere approvato da nessun revisore
  automatico: lo stato è `incomplete`.

Verifica cosa copre già il commit `bec1e7c` e completa il resto.
*Test:* lettura finta tutta "unclear" → ripetizione, poi divisione; grafo vuoto → mai `approved`.

**E2. Assistenza condizionata e contesto nelle azioni.**
- Due occorrenze della stessa azione con condizioni tipizzate diverse (per esempio immediata, e
  "se i controlli non risolvono") restano due occorrenze distinte sul ramo, ciascuna con la sua
  condizione. Non si fondono in un'unica relazione che perde la condizione.
- Segui l'istruzione della cella unita di Lincoln (`campaign/lincoln_powermig_215mp`, p. 28, terza
  colonna) dall'estrazione al grafo, e trova in quale stazione si perde o si unisce. La
  propagazione delle celle unite (`inherited_cell_proposals` in `checker.py`) deve portare anche
  le condizioni.

*Test:* una tabella con una colonna unita "se persiste, contattare l'assistenza" e una riga che ha
anche un'assistenza immediata → due occorrenze con condizioni diverse su ogni riga.

**E3. Il valutatore vede le condizioni.**
- In `scripts/kg_v3_evaluate.py` il giudice riceve le condizioni tipizzate di entrambi i lati.
- Un divieto rappresentato come avvertenza deve poter corrispondere allo stesso fatto che il gold
  scrive come azione.
- Condizioni mancanti, negazioni invertite e rimedi della voce vicina devono essere rifiutati.
- Aggiungi test di equivalenza e di rifiuto sul testo che il giudice riceve (`pair_line` e simili).
- **Misura l'effetto a parte:** rivaluta con il nuovo valutatore le esecuzioni D già esistenti,
  senza rieseguirle, e riporta la differenza come "effetto della misura".

**E4. Mappa per sezioni, più stabile.**
- La mappa lavora per sezioni (titoli e indice del manuale come segnale strutturale, dove ci
  sono), con risposte più piccole, e rilegge una seconda volta solo le sezioni incerte.
- Il revisore del cancello della mappa non può togliere una pagina che sta tra pagine confermate
  della stessa sezione, oltre alle pagine già confermate da entrambe le letture.
- Riporta per ogni esecuzione le pagine lette, confermate e tolte.

*Test:* una sezione con pagine confermate ai lati e una pagina incerta in mezzo → la pagina resta
diagnostica anche se il revisore la toglie.

**E5. Il giudice delle fusioni vede il contesto.**
- Oltre ai nomi, il giudice di `merger.py` riceve, per ogni lato, il testo dei segmenti citati e
  i rami collegati (problema e rimedi).
- Due entità con rimedi diversi in voci diverse sono "diverse" salvo prova contraria.
- Restano valide tutte le regole di F1: vincoli `different`, numeri, nessuna unione transitiva
  contro un vincolo.

*Test:* "LED blu lampeggiante: disponibile per l'abbinamento" e "LED blu tremolante: trasferimento
dati" (ABB p. 232) con rimedi diversi → il giudice riceve il contesto, e il codice non li fonde
senza un `same` motivato.

**E6. Il ramo si conserva durante separazione e fusione.**
- Quando una relazione perde i propri testimoni dopo una separazione (`split_disagreements`) o una
  fusione rifiutata, si fa una verifica mirata sul ramo risultante, non si butta.
- Un'azione composta in parte sbagliata si riduce alla parte sostenuta dal manuale. Esempio Atlas
  Copco p. 43: tenere "contattare l'assistenza" e rifiutare "arresto immediato", che appartiene a
  un'altra voce.
- Avvertenze e condizioni estratte restano sul ramo anche dopo la separazione (caso Haas p. 144,
  batterie del robot).

*Test:* un'azione composta con una parte sostenuta e una no → resta la parte sostenuta, con
citazioni e condizioni.

**E7. Esperimento: revisore selettivo delle omissioni.**
- Attivo solo sui rami incompleti o discordanti tra le letture, con un tetto di tentativi per
  manuale.
- Riceve la porzione del manuale e il ramo estratto, e propone integrazioni documentate con
  citazioni. Le proposte passano dal checker come ogni altra relazione, niente scorciatoie verso
  il verde.
- Deve essere spento per impostazione predefinita (`RunConfig`) e misurato **a parte**: le stesse
  unità con e senza, con costo e domande in più.

**E8. Esperimento: verifica sul ritaglio della pagina.**
- Solo se il modello accetta immagini: verificalo con una chiamata di prova e riporta costo e
  risposta.
- Per le relazioni verdi che dipendono da celle-elenco o da celle ereditate, invia al verificatore
  il ritaglio della riga della tabella (reso con PyMuPDF) insieme al testo.
- Spento per impostazione predefinita e misurato a parte, su un sottoinsieme: pagine tabellari di
  ABB, Atlas Copco e Lincoln.
- Se il modello non accetta immagini, riportalo e salta il punto.

## 3. Misura

1. **Prima:** esecuzioni D attuali in `runs/`. Calcola `campaign.py kpi` con il nuovo valutatore
   (E3) e `campaign.py quality`. Riporta anche i numeri D con il valutatore precedente
   (`kpi_D.json`), per separare l'effetto della misura.
2. Implementa E1–E6 con i test. Dove possibile verifica **offline** sullo stato salvato
   (`state/`) prima di spendere, e riporta cosa cambia.
3. Sposta le esecuzioni D in `campaign/<manuale>/runs_D/` e riesegui i sei manuali con E1–E6
   attivi e E7–E8 spenti: `scripts/campaign.py run <id>`, uno alla volta, tre esecuzioni ciascuno.
4. Dopo: `campaign.py kpi`, `campaign.py quality`, domande contrastive (`contrastive.json`, non
   ancora riviste da Fabio: indicale come provvisorie).
5. Esperimenti E7 ed E8 a parte, sul sottoinsieme indicato, entro il tetto di spesa.

Criteri di accettazione:
- nessuna esecuzione vuota o `approved` con unità diagnostiche fallite;
- `fusion_violations` = 0;
- rami recuperati superiori a D con lo stesso valutatore, oltre il rumore (0–4 rami per manuale),
  e riportati sia in totale sia separando rami con azioni e rami con sole cause;
- cause orfane e problemi senza azione non peggiori di D;
- domande a una persona ≤ 10 per manuale;
- costo per esecuzione riportato.

Se un criterio non è raggiunto, spiega dove e perché.

## 4. Cosa consegnare

- Commit sul branch, uno per punto, con ruff e pytest verdi.
- Una sezione nuova in `campaign/results/REPORT.md` con:
  - tabella prima e dopo per manuale (rami, rami con azioni, asserzioni, fusioni vietate, cause
    orfane, pagine gold lette, stabilità, domande a persona, costo, tempo);
  - effetto della misura e effetto della pipeline, separati;
  - esiti di E7 ed E8;
  - esempi verificati sul PDF di rami recuperati e di errori rimasti;
  - risultati negativi.
- Poche righe in `paper/STATUS.md`.
- In chat, in italiano e in modo semplice: cosa hai fatto, la tabella prima e dopo, cosa resta
  aperto e cosa deve decidere Fabio (Lincoln R1.1/R1.2, coppie contrastive, fogli di precisione).
