# Piano di lavoro verso il primo draft

## Priorità corrente: qualità dell'estrazione prima del paper

La richiesta corrente dell'utente antepone la pipeline diagnostica sui quattro
manuali esistenti alla scrittura e all'ampliamento del corpus. Il riferimento
operativo proposto è [Analisi e piano di robustezza](ANALISI_PIANO_ROBUSTEZZA_ESTRAZIONE.md).
L'analisi è completata e l'utente ha approvato l'implementazione con cap API
cumulativo di 20 USD. Ontologia invariata. Il nuovo registro operativo è in
`experiments/robustness_20260925/`; baseline, varianti, risposte originali e
fallimenti restano distinti.

Deliverable: P0 baseline/replay e osservabilità; P1 gold tecnico e scorer;
P2 recupero per record; P3 layout, scope e contesto; P4 contratto diagnostico e
compilazione; P5 identità/export/revisione; P6 confronti controllati; P7 quattro
manuali e valutazione documentale. Dipendenze e criteri di completamento sono
nel §7 del piano; la proposta di 40 USD del §12 è superata dall'autorizzazione
di 20 USD. P0 e gli incrementi di parsing, recupero, layout, grounding,
condizioni e visibilità delle ispezioni sono implementati e verificati tecnicamente (599 test; replay esatto sui quattro manuali).
Il [rapporto di implementazione](experiments/robustness_20260925/REPORT.md) registra risultati, regressioni e stato puntuale P0–P7.
P1 dispone di scorer e pacchetti sorgente indipendenti, ma la validazione
tecnica del gold è aperta. P6/P7 sono confronti di sviluppo: non sostituiscono
il confronto decisivo su gold validato. Duplicati residui, copertura e carico
di revisione restano criteri da soddisfare, anche quando i test software passano.

Il [seguito C7/C8](experiments/robustness_followup_20260926/REPORT.md) verifica
un nuovo incremento sulle tabelle Hypertherm, un run reale e quattro replay.
In C7/C8 P5 era aperto anche per la correzione/ricompilazione dei singoli
record; questo limite è affrontato dalla continuazione descritta sotto.
Il gold Hypertherm è ancora da annotare; le note dell'assistente sono proposte
per adjudication, non riferimento validato.

La [continuazione C9–C12](experiments/robustness_continuation_20260926/REPORT.md)
completa il flusso software di correzione per record P5: revisione tracciata,
fonti, nuova compilazione, blocchi residui e concorrenza verificati via API/UI.
P5 resta aperto per la risoluzione di identità/duplicati e per misure con tecnici.
P2–P4 aggiungono recupero circoscritto, protezione delle negazioni e contesto
multipagina; P6/P7 comprendono quattro nuove estrazioni complete C11, verifica
incrementale C12 e audit documentali separati dal gold. La suite finale ha
612 test superati; il beneficio locale Test 9 è di quattro esiti terminali
supportati, senza certificazione dei percorsi completi. Il carico totale non
è ridotto: Hypertherm ha 157 review e Graco 64. L'accettazione semantica resta
aperta, senza attribuire la regressione al solo modello o al solo codice.

Prossimi deliverable dipendenti: ricostruire e verificare prerequisiti/salti delle
procedure, risolvere duplicati preservando condizioni e provenienza, separare
conflitti documentali da errori tecnici persistenti, quindi misurare decisioni e
tempo di revisione con i tecnici secondo la procedura preparata. Completamento:
rami corretti preservati, nessun collegamento inventato nei casi auditati,
completezza esplicitamente giudicata e riduzione motivata del lavoro umano.
Gli audit dei 34 casi storici e delle 21 ambiguità sono proposte da adjudicare;
P1 resta aperto per il gold indipendente. Il costo cumulativo è 1,644144695 USD
sullo stesso cap di 20 USD; nessun budget nuovo.

Il percorso verso il paper riportato sotto resta un obiettivo successivo. La
verifica/creazione del gold richiede tecnici; annotazioni proposte dall'assistente
non diventano gold verificato. Il passaggio a implementazione non autorizza a
saltare quel requisito né a sostituire la qualità sui PDF con test software.

Il piano usa deliverable e criteri di completamento, senza calendario. Le risorse
aggiuntive vanno soprattutto in annotazione indipendente, diversità del corpus,
confronti controllati e misure dell'utilità; più chiamate sullo stesso gold di
sviluppo non aumentano da sole la forza dell'evidenza.

## A. Definire il contributo e il perimetro

Formulare il contributo attorno alla costruzione verificabile di relazioni
diagnostiche da manuali, con conservazione dei rami e gestione esplicita delle
lacune. Chiarire con i coautori se il downstream è una dimostrazione limitata o
un secondo contributo valutato. Il primo articolo può concentrarsi sui manuali
PDF: CSV, fusione multisorgente e un prodotto agentico completo non sono
prerequisiti impliciti.

Deliverable: domande di ricerca, confronto con lavori vicini e titolo coerente
con il perimetro. Completamento: ogni contributo ha un esperimento o una prova
tecnica associata e una condizione che potrebbe smentirlo.

## B. Congelare gold e protocollo prima della campagna

Applicare `evaluation/PROTOCOL.md`. Costituire un gruppo di annotazione separato
da chi modifica prompt e filtri. Usare manuali nuovi per il test; associare ogni
fonte a famiglia di prodotto, produttore e storia di esposizione. Preparare
annotazioni indipendenti, adjudication e manuale delle decisioni.

Deliverable: manifest del corpus, gold versionato e verificato, scorer con casi
positivi e negativi, protocollo congelato. Completamento: perimetro esaustivo
esplicito, denominatori verificabili, nessun overlap per famiglia tra sviluppo
e test, ambiguità risolte o marcate. L'eventuale test resta non accessibile allo
sviluppo fino al congelamento dei sistemi.

## C. Stabilizzare il codice per esperimenti confrontabili

Il primo incremento integra GPT-6 Luna e i relativi costi. Proseguire con:

1. Separazione configurabile tra selezione del contesto, estrazione, compilatore,
   grounding e recovery, per cambiare un fattore per volta.
2. Manifest automatico per codice anche dirty, prompt, schema, configurazione,
   input, modello restituito dal provider, dipendenze e prezzi.
3. Scorer indipendente dai filtri della pipeline, con matching uno-a-uno e
   gestione esplicita di gold parziale, duplicati e predizioni fuori perimetro.
4. Casi di regressione su rami mischiati, negazioni, numeri/unità, riferimenti
   multipagina, citazioni vere associate alla relazione sbagliata e OCR incompleto.
5. Contratto di pubblicazione: record incomplete o non approvate non diventano
   automaticamente conoscenza utilizzabile dal consumer.

Completamento: replay riproducibile, test dei contratti superati e output
riconducibile senza ambiguità a input e configurazione. Il testset non si usa
per scegliere fix. Evitare una riscrittura, un vector database o un passaggio a
RDF salvo che un requisito o un errore misurato lo giustifichi.

## D. Eseguire confronti e analizzare gli errori

Prima verificare accesso API e formato su sviluppo. Poi scegliere il profilo
Luna tramite il pilot, congelare sistemi e lanciare la matrice del protocollo.
Usare budget espliciti del runner dimensionati alla matrice, senza ereditare
inconsapevolmente il tetto per singolo documento della configurazione applicativa.

Deliverable: risultati per documento e aggregati, intervalli, variabilità tra
run, costi e tassonomia degli errori. Completamento: tutti i run previsti sono
contabilizzati, compresi fallimenti e astensioni; le differenze non dipendono da
input o gold diversi. Ogni correzione guidata dal test richiede una nuova fase
con un ulteriore test indipendente.

## E. Dimostrare l'utilità del grafo

Implementare un consumer minimo che accetti osservazioni canoniche, interroghi
solo un grafo versionato approvato e restituisca candidati, evidenze e lacune.
Definire regole e ordinamento deterministici. Verificare lo stesso contratto su
record strutturati piatti e retrieval testuale per isolare il valore del grafo.
Misurare anche l'onere umano in uno studio di revisione con compiti controbilanciati.

Deliverable: benchmark di query diagnostiche, trace del consumer, confronto di
correttezza e supporto delle risposte; misure del tempo di revisione e qualità
finale. Completamento: risultati ripetibili sui dati fissati e limiti documentati.
La generazione libera di risposte e l'attuazione fisica non servono per questa prova.

## F. Assemblare e revisionare il draft

Scrivere introduzione, related work e metodo mentre B e C procedono. Inserire i
risultati soltanto dai report verificati di D ed E. Figure previste: architettura
con confini stocastici/deterministici; esempio di ramo con evidenza e gap; curva
qualità/costo/revisione. Tabelle: corpus e split, confronti principali, ablation,
errori e downstream. Compilare abstract e conclusioni per ultimi.

Deliverable: manoscritto completo con bibliografia, figure, supplemento
riproducibile e domande mirate ai coautori. Completamento: nessuna metrica senza
fonte, nessun risultato pianificato presentato come osservato, limiti espliciti,
coerenza di tutte le cifre e verifica visiva dell'export.

## Decisioni che restano da chiudere

Scegliere con i colleghi journal, autori e responsabilità scientifiche; verificare
accesso ai nuovi manuali e possibilità di distribuire testi/annotazioni; decidere
se rilasciare codice e con quale licenza. Il repository attuale non va chiamato
open source per il solo fatto di essere accessibile. Stabilire il livello di
validazione industriale proporzionato alle conclusioni. Queste decisioni possono
procedere insieme al lavoro tecnico e non richiedono di sospenderlo.

## Passaggio proposto alla verifica su nuovi manuali

Preparare un piccolo pilot su nuovi produttori e strutture documentali, con
versione congelata e sezioni diagnostiche valutate integralmente. Dopo la lettura
degli errori quei manuali diventano sviluppo; mantenere separati i documenti del
test finale. Questo è il prossimo esperimento proposto, non una campagna già
eseguita né una prova di generalizzazione. Le correzioni documentate del codice
corrente restano accompagnate dai risultati negativi C9–C12.
