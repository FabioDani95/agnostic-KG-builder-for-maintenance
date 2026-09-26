# Autorizzazione e vincoli della fase di implementazione

L'utente ha approvato l'implementazione del piano con un **nuovo cap cumulativo
di 20,00 USD**, inclusi confronti, tentativi falliti, retry ed escalation.
Questo limite sostituisce la proposta di 40 USD e non somma il budget storico.

L'ontologia `ontology_schema.JSON` resta rigida e invariata. Le proposte del
modello rispettano tipi e relazioni ammessi; ispezioni, condizioni e ambiguità
sono record diagnostici tipizzati collegati ai rami, non nuovi tipi ontologici
inventati né ispezioni convertite in riparazioni. Il grafo finale deve essere
pulito e conservare le catene documentate quanto più completamente possibile.
L'assenza di un collegamento nella fonte non autorizza a inventarlo.

Il gate umano decide sui candidati dubbi dopo i controlli e il recupero
automatico. I candidati mantengono fonte, motivazione e alternative; non entrano
automaticamente nel grafo approvato. La validazione del gold resta riservata ai
tecnici e separata dalle predizioni.

Allocazione iniziale entro il cap unico: 4 USD pilot (12 pacchetti, confronto
Luna low/8k, low/24k, none/24k e controlli mirati con modello più capace);
8 USD confronti baseline/candidato sui quattro manuali; 3 USD ablation mirate;
5 USD riserva retry/escalation/usage ignoto. La matrice viene ridotta per prime
nelle ablation opzionali se il preflight non lascia margine per i run decisivi.
Ogni trasferimento fra sottobudget deve essere registrato; il totale non può
superare 20 USD. Nessuna chiamata fuori dal ledger cumulativo.

La baseline è in `baseline_source.tar.gz` e `baseline_manifest.json`, congelata
prima delle modifiche al servizio. I risultati successivi devono identificare
esattamente codice, configurazione, dipendenze, modello e stato della validazione
umana. In assenza di gold tecnico, i run di sviluppo restano esplorativi e non
dimostrano il superamento dei criteri semantici del piano.
