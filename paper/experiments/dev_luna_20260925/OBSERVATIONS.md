# Osservazioni diagnostiche del pilot

Queste osservazioni riguardano il profilo eseguito, non una valutazione isolata
della capacità di GPT-6 Luna. Rispetto alla campagna v11 cambiano codice,
configurazione di reasoning e recovery. Il gold storico è di sviluppo e il suo
matching automatico non sostituisce il controllo semantico dei tecnici.

## Risposte strutturate troncate

Eastman e Graco hanno ciascuno una chiamata diagnostica che esaurisce 8.000 token
di completamento. I log riportano 8.000 reasoning tokens e nessun JSON completo
utilizzabile. L'SDK solleva un errore di parsing per lunghezza; il budget ledger
conserva l'uso osservato e il relativo costo. La pipeline espone un problema di
contratto e non pubblica i record di quella risposta.

Questo giustifica un prossimo confronto controllato tra impostazioni di reasoning
e budget di output, su sviluppo. Non dimostra che tutte le risposte richiedano
un budget maggiore né che la causa sia esclusivamente il modello.

## Associazione errata tra citazione e fonte

In Danfoss, pagina fisica 64, un candidato per il guasto relativo agli ID ripetuti
contiene un'ispezione dei DIP switch. Il frammento `the individual modules.` è
associato all'anchor `ev_e5afd58033ce44902f2fb94c0b62`. Quel blocco contiene invece
`modules have repeated IDs.`. Il compilatore registra
`quote_not_in_anchored_evidence` e non emette relazioni da quel record.

Il controllo è corretto per questo esempio. Il prossimo intervento deve migliorare
la selezione/conservazione degli anchor, mantenendo la verifica del supporto.
Allentare la verifica per ottenere un numero maggiore di relazioni non è una
correzione giustificata da questo caso.

Il ledger Danfoss riporta 23 segnalazioni di questo tipo. Sono conteggi di motivi
di scarto, non 23 record indipendenti. I record possono avere più problemi.
Inoltre `missing_actions` può riflettere una reale ispezione senza riparazione
esplicita: prima di considerarla omissione del modello serve leggere la fonte.

## Come leggere i risultati

Un HTTP 200 o uno stato di esecuzione completed indica che il run ha prodotto un
artifact. Non significa che il grafo sia completo, corretto semanticamente o
approvato. Le colonne di revisione, accounting e corrispondenza al gold devono
essere lette insieme ai conteggi di nodi/relazioni e alla validità dello schema.

Le citazioni letterali valide dimostrano localizzazione del testo, non supporto
semantico completo. Lo zero di percorsi non supportati rilevati su un output
vuoto non è una dimostrazione di buona qualità.

## Intervento successivo proposto

Conservare questo pilot come baseline. Preparare piccoli casi di regressione
basati sui fallimenti osservati; provare il completamento del JSON e la corretta
associazione degli anchor prima di una nuova campagna sui quattro manuali.
Ripetere il confronto mantenendo invariati PDF, gold e scorer, annotando ogni
variazione di configurazione. Nessuna riscrittura dell'architettura è giustificata
solo da queste osservazioni.

## Esito Hypertherm e contabilità

Hypertherm produce 134 nodi e 132 relazioni, con 82 elementi di revisione e
approval_eligible=false. Il compilatore conta 10 record pubblicabili nel proprio
perimetro, che non equivalgono a 10 diagnosi corrette verificate. Manca un gold.

Si osservano una risposta troncata a 8.000 token, un errore di connessione e una
risposta respinta da un validatore perché sei record hanno indicatori vuoti.
Le ultime due chiamate non espongono usage utilizzabile al wrapper. Il loro
costo è contabilizzato con l'intera prenotazione conservativa: 0,016473375 USD
complessivi, inclusi nel totale della campagna. Lo scorer distingue il costo
calcolabile dai token da quello prudenziale.

Sono necessarie verifiche mirate anche sulla conservazione dei record validi
quando altri record della stessa risposta non superano la validazione. Il
pilot non include correzioni o rerun selezionati per migliorare il punteggio.
