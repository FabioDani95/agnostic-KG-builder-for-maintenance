# Registro dei manuali e responsabilità

Obiettivo iniziale proposto: **16 manuali**, di cui **4 di sviluppo già osservati**
e **12 nuovi per il test finale**. Il numero 12 è una scelta di pianificazione,
non una garanzia di sufficienza statistica. Confermarlo dopo il pilot, considerando
variabilità tra documenti e ampiezza degli intervalli. I manuali nuovi non sono
ancora selezionati. Il registro strutturato è `registry.json`.

## Quali manuali

| Gruppo | Numero | Documenti | Uso |
| --- | --- | --- | --- |
| Sviluppo | 4 | Eastman E-554, Danfoss APF, Graco Check-Mate 200, Hypertherm già analizzato | Prime estrazioni col nuovo modello, comprensione degli errori, calibrazione delle annotazioni |
| Test nuovo | 12 da selezionare | Identificativi T01–T12 nel registro | Valutazione finale dopo aver fissato metodo, gold e metriche |

Per i 12 nuovi puntare ad almeno 6 produttori, preferibilmente assenti dallo
sviluppo, e almeno 3 famiglie di macchine. Distribuzione proposta: 4 manuali
prevalentemente a tabelle diagnostiche, 4 prevalentemente in prosa e 4 misti con
rimandi o rami articolati. Queste sono caratteristiche delle sezioni diagnostiche.
Evitare revisioni o documenti quasi duplicati della stessa famiglia tra gli split.

Se vogliamo includere l'OCR nel claim, almeno 2 dei 12 dovranno contenere sezioni
diagnostiche scansionate; non sono 2 manuali aggiuntivi. In caso contrario,
restringere esplicitamente lo studio ai PDF testuali.

Altri 6 PDF sono presenti in `manuals/`: FANUC, LG, Eagle, Haas e i file
`g0872_m.pdf` e `bfp-a3729e.pdf`. Sono candidati con storia di utilizzo da verificare,
non nuovi test già approvati. La presenza nella cartella non dimostra né idoneità
né assenza di esposizione durante lo sviluppo. Non sono conteggiati nei 16.

## Come tracciare e conservare

Per ciascun manuale compilare nel registro titolo e versione esatti, produttore,
famiglia, fonte, percorso del PDF, SHA-256, split, storia di esposizione, lingua,
formato, pagine diagnostiche da annotare e assegnazioni agli annotatori.
I quattro documenti storici sono identificati tramite gli artifact già presenti;
il loro percorso PDF e hash sono stati riconciliati e registrati per il pilot.

Usare `files/<document_id>/` per i PDF locali, senza duplicare quelli già presenti
se basta un percorso nel registro. Usare `annotations/<document_id>/` per le
annotazioni indipendenti e la versione adjudicata. Queste directory locali sono
escluse dal Git: il loro contenuto va conservato in uno spazio controllato dal
responsabile del corpus, con hash e versione nel registro. Eventuali copie dei
dati pubblicabili saranno aggiunte esplicitamente soltanto dopo averne verificato
le condizioni di distribuzione.

Il test non va usato per modificare prompt o filtri. I tecnici possono annotarlo
prima dei run; chi sviluppa il sistema non deve consultare il gold del test per
ottimizzarlo. Condividere qui i metadati non equivale a rendere il gold accessibile
al processo di estrazione.

## Prossimi passi e chi li esegue

| Passo | Lavoro concreto | Responsabile proposto | Risultato |
| --- | --- | --- | --- |
| 1 | Recuperare i 4 PDF storici e fare le prime estrazioni col nuovo modello | Codex con supervisione di Fabio | Output leggibili, costi, tempi e primi errori; risultati di sviluppo |
| 2 | Selezionare i 12 nuovi manuali e verificarne provenienza e idoneità | Fabio con i tecnici; Codex organizza e controlla il registro | Lista definitiva dei documenti e split |
| 3 | Definire cosa conta come risposta corretta e preparare il formato di annotazione | Codex con Fabio e un tecnico esperto | Regole gold e un esempio compilato sullo sviluppo |
| 4 | Annotare le sezioni diagnostiche senza vedere le estrazioni del sistema | Due tecnici indipendenti; terzo esperto per disaccordi | Gold verificato con fonti e rami corretti |
| 5 | Completare scorer, tracciamento dei run e configurazioni di confronto | Codex con supervisione di Fabio | Misure automatiche riproducibili e codice congelato |
| 6 | Eseguire la campagna finale e confrontare i sistemi | Codex; Fabio supervisiona, tecnici esaminano gli errori | Accuratezza, omissioni, relazioni errate, costi e lavoro umano |
| 7 | Provare alcune query diagnostiche sul grafo e sui confronti | Codex implementa; tecnici verificano; Fabio definisce il perimetro | Evidenza dell'utilità del grafo |
| 8 | Scrivere il draft e revisionarlo | Codex con Fabio; colleghi e tecnici revisionano | Primo manoscritto completo |

Fabio gestisce direttamente accesso ai tecnici, scelta dei colleghi/coautori e
accordo sul journal. Non deve annotare tutto da solo; può adjudicare soltanto se
ha la competenza sul dominio e mantiene l'indipendenza richiesta.

## Cosa cambia nel codice adesso

Nessuna riscrittura architetturale pianificata prima di osservare il pilot.
Le prime estrazioni sui 4 manuali possono precedere il benchmark completo.
Restano necessari scorer e tracciamento sperimentale; eventuali bug del builder
si correggono sullo sviluppo, registrando una nuova versione. Prima del test
finale si congelano codice, prompt e configurazioni. Il consumer del grafo è
un incremento successivo, necessario se ne misuriamo l'utilità nel paper.
