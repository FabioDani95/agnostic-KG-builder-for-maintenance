# Pacchetto per i tecnici: annotazione indipendente e adjudication

**Non è gold verificato.** Nessuna predizione del generatore è stata caricata
nella preparazione di questi pacchetti. I PDF sono copie delle sole pagine
selezionate, senza modificare i documenti originali. `source_inventory.json`
associa pagina del pacchetto e pagina fisica originale; il testo nativo non
sostituisce la lettura della pagina, soprattutto per lo schema Hypertherm 228.

Due tecnici compilano separatamente `annotation_A.json` e `annotation_B.json`.
Prima leggono le fonti senza aprire `historical_proposals_for_adjudicator.json`.
Un terzo tecnico risolve i disaccordi conservando entrambe le versioni e ogni
motivazione. Se lavora un solo tecnico, registrare tale limite senza dichiarare
accordo tra annotatori. Le modifiche vanno salvate come nuova versione, senza
sovrascrivere il gold storico o le annotazioni indipendenti.

Ogni ramo deve contenere `branch_id`, `pages` fisiche, `symptoms`, `codes`
(distinti dal testo dell'allarme), `failure`, `component`, `conditions`
(con `text`, `polarity`, `applies_to`, `step_index`), `inspections`, `actions`
in ordine, `resolution_status`, evidenze letterali per affermazioni e relazioni.
Marcare ogni elemento come `stated`, `not_stated` o `ambiguous` e registrare
alternative, condizioni, negazioni e rinvii. Un'ispezione non diventa un rimedio.
Un guasto non può essere ricostruito soltanto perché è prescritta una sostituzione.

Per l'identità dei rami compilare anche `source_occurrence_id`, indipendente
dagli ID del generatore: documento/versione, pagina, tabella/riga o regione
del diagramma e sotto-ramo. Conservare la corrispondenza con bbox/celle nel
registro di annotazione. Due occorrenze con le stesse parole restano distinte.
`root_pages` identifica le pagine radice nel perimetro; `pages` include anche
le evidenze di continuazione. Il contesto fuori perimetro non aumenta il
denominatore e non deve escludere un ramo la cui radice è nel perimetro.
Lo scorer rifiuta gold dichiarato validato senza identità delle occorrenze.

Perimetri da annotare esaustivamente:

- Eastman: pagine fisiche 37–39, tutti i rami presenti; gli otto casi storici
  sono solo un campione di confronto.
- Danfoss: pagina 64, codici 1–6 e i loro rami; distinguere i tre casi con sole
  ispezioni dai cinque che rimandano al personale di assistenza.
- Graco: pagina 11, tutte le righe, nota a piè di pagina e condizioni applicabili.
  Pagine 9, 10, 12–14 fornite come contesto, non aggiunte al denominatore iniziale.
- Hypertherm: 65–77, 82–104 e 228 (37 pagine radice). Pagine 78–81 come contesto.
  Annotare i diversi esiti dei test, i valori e le tolleranze, i collegamenti
  multipagina, le alternative condizionate per scheda, ventola ed elettrovalvola.
  Un rinvio necessario fuori pacchetto va dichiarato: si estende il contesto con
  nuova versione motivata, non si indovina il suo contenuto.

Questioni già emerse da sottoporre ai tecnici: Eastman E4 definisce un guasto
solo attraverso il rimedio? E6–E8 hanno un supporto di layout sufficiente e
condizioni correttamente conservate? In Danfoss, “contattare il servizio” è
un'azione ammessa nel gold, ma non una riparazione fisica. Graco G8 è un'ispezione.
Per Hypertherm, definire la granularità dei sottoesiti del test 9 prima di
confrontare le predizioni.

`diagnostic_scoring.py` esegue un controllo esatto uno-a-uno e ammette equivalenze
solo se annotate esplicitamente. Non sostituisce l'adjudication semantica.
Finché `validation_status` non è `technician_validated` con autore identificabile,
non produce punteggi di qualità validata. Le predizioni non corrispondenti non
sono automaticamente falsi positivi, specialmente con gold parziale o fuori scope.

Misurare anche tempo di lettura, tempo per decisione, casi realmente ambigui,
correzioni di errore e lacune esplicite. Approvare il gold non approva i grafi,
e approvare un grafo non convalida il gold.
