# Come funziona la pipeline diagnostica v22

> Dal 2026-09-26 il generatore predefinito è la V3: si veda il [Piano V3](PIANO_V3.md),
> che la spiega in parole semplici, e i [risultati](V3_RISULTATI_SVILUPPO.md).
> Questa guida descrive la v22, ancora selezionabile come `legacy_v22`.

Questa guida descrive il generatore `pdf-g3-structured-recovery-v22`, verificato
nella campagna C9–C12. La [guida precedente](PIPELINE_SPIEGAZIONE_IT_20260728.md)
è preservata come documento storico: i suoi risultati non si trasferiscono
alla versione corrente.

## Che cosa fa

Il sistema trasforma un manuale PDF in conoscenza diagnostica collegata alla
fonte: sintomi e codici, possibili cause, componenti, controlli, condizioni e
azioni. Produce un grafo da revisionare. Non esegue la manutenzione e non
certifica che una sequenza di interventi sia completa o sicura.

Un ramo può contenere più indicatori e più passi ordinati. L'identità del ramo
serve a mantenere insieme le informazioni dello stesso caso, evitando di
associare una causa al rimedio di un'altra riga. Una citazione presente nel PDF
è necessaria ma non basta a dimostrare che l'associazione sia corretta.

## Dal PDF al grafo

1. **Preparazione.** L'adapter PDF conserva il testo e, dove disponibili, layout,
   tabelle, pagine e coordinate come evidenze canoniche. Le pagine senza testo
   utilizzabile e i limiti OCR restano espliciti.
2. **Scelta del contesto.** Il workflow seleziona contenuto diagnostico e finestre
   di record. Le procedure numerate possono includere pagine successive di
   contesto anche se classificate strutturali. Il recupero è limitato; non
   interpreta automaticamente tutti i diagrammi o i rimandi del manuale.
3. **Estrazione.** Il modello propone record strutturati con citazioni. Richieste,
   risposte originali e usage sono archiviati prima del parsing.
4. **Compilazione.** Il backend controlla il contratto, le prove, gli estremi delle
   relazioni e alcune incoerenze di ramo o condizione. Un elenco di cause non
   viene abbinato a un elenco di rimedi soltanto perché hanno la stessa lunghezza.
5. **Recupero mirato.** Per alcuni errori tecnici viene preparato un nuovo tentativo
   con fonte e feedback separati. La risposta precedente non diventa una prova.
   I tentativi sono limitati e contabilizzati; i rami validi precedenti sono
   protetti durante la scelta di un risultato di escalation.
6. **Revisione.** Il grafo conserva record accettati dal compilatore, lacune e
   segnalazioni. L'operatore può correggere un singolo record; una nuova
   compilazione decide cosa può essere incluso nella nuova revisione. I blocchi
   residui restano attivi.

Il percorso workspace è `/console.html?foundation=1`. La console senza quel
parametro conserva il precedente flusso PDF con stato separato; il suo export
non prova che la pubblicazione cross-source del nuovo prodotto sia completa.

## Che cosa rappresenta il grafo

L'[ontologia](../ontology_schema.JSON) resta invariata: Asset, Component,
Symptom, ErrorCode, FailureMode e CorrectiveAction, collegati dalle relazioni
previste dal contratto. I controlli e le condizioni sono metadati diagnostici
collegati ai rami; un'ispezione non diventa automaticamente una riparazione.

Il contesto ordinato della procedura (`procedure_context`) permette di leggere
la fonte accanto al risultato. `procedure_path_verified=false` indica che quel
contesto non è stato trasformato in un percorso operativo completo verificato.
Un guasto non dichiarato nella fonte non viene inventato per chiudere la catena.

## Come correggere un caso

Nella fase **Grafo**, aprire **Revisione dei record**, selezionare il caso e
leggere le evidenze. Modificare i campi necessari e le citazioni, indicando
revisore e motivo della modifica. Il salvataggio crea una nuova revisione con
cronologia prima/dopo e ricompila il record.

La correzione non equivale all'approvazione. Una citazione non valida rimane
segnalata e non abilita la pubblicazione; una modifica su una revisione ormai
superata viene rifiutata. Le altre relazioni e i problemi ancora aperti vengono
preservati. La [procedura per i tecnici](../paper/experiments/robustness_continuation_20260926/PROCEDURA_TECNICI.md)
distingue questo lavoro di revisione dall'annotazione indipendente del gold.

## Quanto funziona oggi

| Manuale | Rami nel grafo | Record irrisolti | Segnalazioni di revisione |
| --- | ---: | ---: | ---: |
| Eastman | 9 | 57 | 75 |
| Danfoss | 8 | 9 | 26 |
| Graco | 19 | 36 | 64 |
| Hypertherm | 21 | 145 | 157 |

Tutti e quattro i grafi restano non approvabili. Su Hypertherm sono recuperati
quattro esiti diagnostici locali del Test 9, ma restano passaggi preparatori e
percorsi alternativi incompleti. Le segnalazioni salgono da 111 in C8 a 157 in
C12: non è dimostrata una riduzione complessiva del lavoro umano.

I 612 test Python superati, la verifica API/browser e i quattro replay offline
confermano comportamenti software e riproducibilità. Non misurano la precisione
semantica globale. Il gold dei tecnici è ancora da annotare; gli audit dell'agente
sono separati e non vengono presentati come validazione umana indipendente.

## Come leggere le misure

- **Rami nel grafo:** identità dei rami rappresentati; possono esserci duplicati
  dello stesso caso sorgente e percorsi incompleti.
- **Record irrisolti:** candidati per cui non è stato completato il percorso
  previsto di compilazione; non coincidono con tutte le notifiche UI.
- **Notifiche di revisione:** problemi da esaminare; più notifiche possono
  riguardare la stessa decisione. Non sono minuti di lavoro né catene uniche.
- **Grounding letterale:** citazione e posizione coincidono con la fonte
  canonica. Il supporto semantico della relazione richiede un controllo distinto.
- **Precisione e recall semantiche:** correttezza e copertura rispetto a un
  riferimento adeguato. Non sono disponibili globalmente per questa campagna.
- **Costo API:** il ledger cumulativo registra 1,644144695 USD su 20, inclusi
  errori e retry. Il costo umano non è ancora misurato. Il budget non riparte
  da zero a ogni nuova campagna.

## Dove si trova l'implementazione

| Responsabilità | File principale |
| --- | --- |
| Evidenze PDF | `backend/adapters/pdf.py` |
| Contesto ed escalation | `backend/services/ontology_workflow.py` |
| Record e compilazione | `backend/domain/diagnostic_bundles.py`, `backend/services/diagnostic_bundle_compiler.py` |
| Recupero e riconciliazione | `backend/services/diagnostic_recovery.py`, `backend/services/diagnostic_reconciliation.py` |
| Correzione singola | `backend/services/diagnostic_record_review.py`, `backend/routers/subgraphs.py` |
| Interfaccia | `frontend/app/graph.js` |
| Risposte e budget | `backend/services/llm_response_archive.py`, `backend/services/real_call_budget_ledger.py` |

I [risultati completi](../paper/experiments/robustness_continuation_20260926/REPORT.md)
includono anche fallimenti e regressioni. Le [istruzioni di riproduzione](../paper/experiments/robustness_continuation_20260926/REPRODUCE.md)
separano nuove estrazioni, verifiche incrementali e replay senza rete. Database e
copie raw esclusi da Git restano locali: una nuova checkout necessita anche degli
input congelati per riprodurre gli esperimenti.
