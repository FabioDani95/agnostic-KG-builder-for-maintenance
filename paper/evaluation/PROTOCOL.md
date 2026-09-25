# Protocollo scientifico e gold standard

Stato: protocollo proposto, non ancora congelato. Specificare il commit di
approvazione prima della campagna finale. Le quantità indicate sono scelte di
disegno da verificare nel pilot, non risultati né soglie universali.

## Domande di ricerca

RQ1: il metodo conserva meglio le relazioni diagnostiche e l'identità dei rami
rispetto all'estrazione diretta con lo stesso modello?

RQ2: quali componenti spiegano il miglioramento e quale costo comportano in token,
retry, astensioni e lavoro umano?

RQ3: le prestazioni si trasferiscono a produttori e strutture documentali non
utilizzati durante lo sviluppo?

RQ4: a parità di informazione disponibile, l'organizzazione a grafo migliora la
risposta a query diagnostiche verificabili rispetto a record piatti e retrieval?

## Corpus, split e unità

Eastman E-554, Danfoss, Graco e Hypertherm già esaminati sono sviluppo. Raccogliere
un test nuovo stratificato per produttore, famiglia di prodotto, tabelle/prosa,
complessità dei rami, lunghezza e qualità di estrazione/OCR. Separare per documento
e famiglia, non per pagina; revisioni dello stesso manuale non vanno in split
diversi. Conservare SHA-256, provenienza, versione, lingua e storia di esposizione.

Un punto di partenza è 8–12 manuali nuovi distribuiti tra più produttori, da
ridimensionare in base a diversità, variabilità tra documenti e precisione degli
intervalli ottenuta nel pilot. Il numero di rami non sostituisce il numero di
fonti indipendenti. Se si rivendica il supporto ai manuali scansionati, includerli
come strato dichiarato; altrimenti restringere il claim ai PDF testuali.

Annotare esaustivamente le sezioni diagnostiche selezionate prima di osservare
le predizioni. Separare due condizioni: estrazione su perimetro gold comune
(isola l'estrattore) e pipeline end-to-end sul manuale completo (include errori
di scoping). Non dichiarare recall dell'intero manuale da un campione di pagine.
La correttezza di output fuori perimetro richiede annotazione supplementare o
uno stato non valutabile, mai un falso positivo automatico.

## Gold

L'unità primaria è un ramo diagnostico: asset/componente, osservazione o codice,
condizione, possibile guasto, ispezione, azione, loro relazioni e span di supporto.
Un campo assente nella fonte è assente nel gold. Un'ispezione non è una riparazione;
una relazione ipotizzata non è esplicitamente documentata. Distinguere rami
alternativi, congiunzioni, negazione, antecedenti e riferimenti tra pagine.

Due annotatori competenti lavorano indipendentemente sul materiale del test,
senza predizioni. Un terzo adjudica i disaccordi; conservare entrambe le versioni,
la decisione e la motivazione. Fare calibrazione su sviluppo, poi congelare le
linee guida. Misurare accordo su etichette, span e relazioni: per insiemi di rami
servono allineamento e accordo/F1, per categorie un coefficiente appropriato con
prevalenze e numerosità. Un solo kappa globale non descrive ogni oggetto.

Schema logico minimo del gold, da formalizzare in JSON Schema prima dei run:

- `document_id`, `document_sha256`, `split`, `product_family`, `exposure_status`;
- `scope_pages`, `scope_exhaustive`, `annotation_version`;
- `record_id`, `branch_id`, identificativi degli elementi e relazioni tipizzate;
- condizioni, polarità, ordine delle ispezioni quando espresso;
- per ogni asserzione: pagina fisica, testo esatto e coordinate/offset disponibili;
- stato esplicito `stated`, `ambiguous` o `not_stated`;
- annotazioni indipendenti, adjudication, identificativo anonimo dell'annotatore.

Le assenze e le ambiguità non sono valori da indovinare. Non generare il gold
copiando l'output della pipeline. Un LLM può aiutare l'interfaccia di annotazione,
ma i suggerimenti rendono necessaria una verifica dei bias introdotti.

## Confronti principali

| Sistema | Scopo |
| --- | --- |
| Estrazione diretta con GPT-6 Luna e lo stesso schema finale | Baseline che isola il contributo della pipeline |
| Baseline con esempi scelti solo dallo sviluppo | Confronto più competitivo con prompting ontology-guided |
| Pipeline completa con GPT-6 Luna | Candidato principale |
| Stessa pipeline con GPT-5.6 Luna | Confronto col modello storico senza cambiare architettura |
| Stessa pipeline con un modello più capace, fissato nel pilot | Stima del trade-off qualità/costo senza confondere modello e metodo |

Stesso corpus e informazioni ammesse, medesimo scorer, log dei prompt e parametri.
Il baseline diretto può richiedere chunking per limiti di contesto: predefinirlo
e conteggiarne il costo. Fornire un confronto sul perimetro oracle e uno
end-to-end; non concedere pagine gold soltanto al sistema proposto.

Ablation mirate, un fattore per volta: finestre restrittive v11 contro contesto
semantico v12; identità dei rami; vincolo di supporto delle relazioni; completion
pass; escalation selettiva. Mantenere formato e scoring comparabili anche quando
si disabilita un modulo. Non chiamare ablation il confronto tra commit che
cambiano contemporaneamente prompt, gold, filtri e modello.

## Metriche

La metrica primaria proposta è F1 delle relazioni diagnostiche con corretto
contesto di ramo. Lo scorer usa associazione uno-a-uno e un'ontologia di alias
fissata sullo sviluppo; un overlap lessicale non basta per dichiarare correttezza.
Aggiungere esattezza del ramo completo per distinguere errori strutturali che le
metriche aggregate delle singole relazioni potrebbero nascondere.

Riportare precision, recall e F1 per documento, micro sul totale delle unità e
macro come media per documento. Rendere espliciti i denominatori e la gestione
delle classi vuote. Precision richiede giudicare tutte le predizioni nel perimetro;
un gold incompleto consente al massimo una copertura dei casi annotati.

Metriche secondarie: supporto semantico delle relazioni, localizzazione degli span,
mescolamento dei rami, rami completi autonomi, lacune esplicite, review rate,
precisione dell'output accettato e recall rispetto a tutto il gold. Un sistema
che respinge tutto non deve ottenere un punteggio favorevole. Separare sempre
accounting, output autonomo e output finale corretto dopo revisione.

Costi: input/output/cached/cache-write tokens, retry, chiamate fallite, latenza,
profilo di servizio e costo stimato per documento e per ramo corretto. Il costo
umano include minuti di revisione e correzione, separati dal costo API. Congelare
la tabella prezzi nel manifest; conservare il modello richiesto e quello restituito.

Prevedere cinque repliche delle condizioni LLM principali; confermare il numero
nel pilot prima del freeze. Usare confronti appaiati sul medesimo documento e
intervalli bootstrap raggruppati per documento, mantenendo esplicita la variabilità
tra repliche. Non trattare rami dello stesso documento come campioni indipendenti.
Dichiarare confronti primari e secondari prima dell'analisi; non scegliere la
replica migliore come risultato principale.

## Prova downstream e lavoro umano

Definire query con risposte gold indipendenti: guasti candidati per codice,
ispezioni pertinenti, azioni condizionate, origine di una relazione, informazioni
mancanti e condizioni incompatibili. Includere query senza risposta. Usare gli
stessi contenuti per grafo, record piatti e retrieval testuale; un confronto con
text-RAG generativo è un'estensione distinta, con costo e variabilità propri.

Separare due prove: grafo corretto di riferimento (utilità della rappresentazione)
e grafo estratto (errore end-to-end). Misurare esattezza dell'insieme restituito,
correttezza del ramo, supporto delle citazioni e astensione. Ripetere query su
snapshot immutabile, variando ordine di serializzazione e inserimento, e verificare
output canonico identico. Questa è la prova di determinismo del consumer, non
dell'LLM. Il consumer non esegue interventi fisici.

Per la revisione umana, assegnare compiti controbilanciati tra esperti e condizioni,
evitarne la ripetizione sullo stesso caso noto, misurare qualità finale oltre al
tempo. Specificare esperienza, istruzioni e criteri di correzione. Se questo
studio non viene effettuato, eliminare le conclusioni sul risparmio di lavoro.

## Suite tecnica e congelamento

Mantenere distinti test unitari, replay offline, integrazione API, benchmark
scientifico e studio utenti. Casi obbligatori dello scorer: duplicati, gold
parziale, predizione extra, nessuna predizione, ramo sbagliato con parole uguali,
citazione vera ma relazione falsa, macro diverso da micro e intervalli per documento.

Prima della campagna finale devono esistere gold verificato, scorer testato,
manifest completo, configurazioni baseline/ablation congelate e smoke test reale
del modello. Conservare output grezzi e fallimenti. Generare automaticamente le
tabelle del paper dai risultati, senza trascrizione manuale. Cambiare il protocollo
dopo aver visto il test richiede una dichiarazione esplicita e nuova validazione.

## Registro operativo del corpus

La proposta operativa in [manuals/README.md](../manuals/README.md) fissa come
obiettivo iniziale 12 manuali nuovi, oltre ai 4 di sviluppo. Gli slot e il loro
stato sono in `../manuals/registry.json`. La selezione e il numero finale restano
da confermare secondo i criteri del pilot: nessuno slot è già un manuale acquisito.
