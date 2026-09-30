# Editor del grafo: implementazione e verifica

Le fasi 1–5 e gli incarichi A–G di [PIANO_EDITOR_GRAFO.md](PIANO_EDITOR_GRAFO.md)
sono implementati nella UI React/TypeScript e nella API locale FastAPI. L’editor di
riferimento `kg-graph-editor_V1` ha fornito la logica funzionale degli indici, dei filtri,
degli stati dei campi, dei controlli e della navigazione; il renderer resta quello 3D
dell’applicazione. Non sono stati importati il suo salvataggio sul file originale,
l’architettura senza backend o i suoi vincoli visivi.

## Percorso disponibile

«Modifica grafo» è presente nel grafo finito, nel riepilogo live/replay e nella versione
attuale e nella cronologia del manuale. La capacità di modifica viene dal server:
un processo in corso, risposte non applicate o un formato non leggibile impediscono
l’apertura. PDF e stato della pipeline mancanti non impediscono l’editing supportato.

Consultazione: Grafo, Nodi, Relazioni e Controlli. Editing: Modifica ⇄ Controlla ⇄
Riepilogo, con tabelle editabili, dettagli, prove, selezione comune, filtri cumulativi,
ordinamento e undo/redo. Una selezione proveniente dai controlli viene mostrata anche
quando i filtri correnti la escludono. Il renderer conserva scena, camera e posizioni
mentre si cambiano scheda e passo; una modifica del nome aggiorna la sua etichetta.

Le operazioni vivono nel reducer della sessione. Avanti, blur, controllo e cambio scheda
non persistono alcuna bozza. L’uscita dalla route usa il blocker del data router, anche
per POP; `beforeunload` protegge ricarica/chiusura e `pagehide/pageshow` azzerano il
contenuto della sessione anche al ripristino dalla bfcache. Nessun payload editor viene
salvato in storage o history. Una URL diretta al riepilogo riparte da Modifica/Nodi.

Solo «Accetta modifiche e crea nuova versione» invia l’accettazione. La destinazione è
subito accettata, senza un secondo Approva. Con esito di rete incerto la UI congela
payload e chiave soltanto in memoria, interroga lo stato e riusa la stessa richiesta.
Un’accettazione già inviata può completarsi anche se il browser viene chiuso.

Celle e dettaglio distinguono campo assente, stringa vuota, `null`, lista vuota,
`not_stated`/`Unknown`, `0` e `false`. ID, tipi dei nodi esistenti, dati sconosciuti e
citazioni sono in sola lettura; nome e proprietà canoniche vengono sincronizzati.
Gli estremi delle relazioni seguono dominio/range; una proposta con tripla già presente
aggiunge un’occorrenza. Cancellazione a cascata e ultima occorrenza sono annullabili.

## API e persistenza

Il prefisso delle API di versione è `/api/manuals/{manual_id}/versions/{version_id}`.

| Endpoint | Comportamento |
| --- | --- |
| `GET /editor` | Documento completo, schema tipizzato, capacità, fonti, contesto ereditato e precondizioni |
| `POST /validate-edits` | Anteprima senza scritture; operazioni ammesse, diff, controlli, metriche, hash e generazione |
| `POST /revisions` | Nuova versione e accettazione atomiche; 201 alla prima richiesta, 200 al retry identico |
| `GET /api/manuals/{manual_id}/revision-requests/{request_id}` | `saved`, `in_progress` o `not_found`; risultati riusciti ricostruiti dai manifest dopo riavvio |
| `GET /changes` | Operazioni e differenze della revisione |
| `GET /provenance.zip` | Pacchetto grafo, base, accettazione, controlli, schema e fonti congelati |
| `GET /source-segments` | Ricerca/pagina/paginazione sull’indice verificato, senza modificare testo fonte |
| `GET /pages/{page}.png` | Pagina coerente con la fonte di quella versione |

I DTO Pydantic rifiutano campi extra e operazioni non ammesse. Gli errori editor 422
restituiscono codice traducibile e target/campo; 409 identifica precondizioni o preview
obsolete e chiavi riusate con un contenuto diverso. Anteprima e salvataggio ripetono
validazione e confronto di hash di grafo, schema, fonte e contesto delle domande.
Un documento senza differenze non può creare una versione.

Ogni revisione usa `revision~<uuid>` e un numero per manuale. La cartella
`workspace/<manual_id>/revisions/<uuid>/` contiene:

- `graph.json`, in formato `kg-v3-graph-3`;
- `base-graph.json`, con i byte esatti della base;
- `revision.json`, con padre, run radice, hash, autore, data, nota, chiave di richiesta
  e mappa tra ID temporanei e definitivi;
- `changes.json`, `validation.json`, `acceptance.json`;
- `source-review.json`, `source-report.json`, `ontology.json`, `source-segments.json`;
- `source.pdf`, quando la fonte è disponibile e verificabile.

`validation.json` conserva l’anteprima effettivamente riconosciuta, con hash e ID
provvisori; `revision.json.id_map` li collega agli ID pubblicati. Il diff salvato contiene
la base e il risultato effettivi. Il rapporto della pipeline rimane storico, separato
dal risultato umano: la revisione non inventa report, eventi, costi o tempi di estrazione.

La pubblicazione usa lock per manuale, anche fra processi, directory temporanea nascosta,
flush/fsync e rename atomico. Preview non crea file di revisione o lock. Accettazione,
risposte, applicazione e approvazione coordinano il lock; i comandi della pipeline
rifiutano gli ID di revisione. Il catalogo ignora directory incomplete/nascoste e
separa esecuzioni e revisioni. Le attività dei run restano in «Tocca a te» anche quando
la versione più recente è una revisione.

## Provenienza e fiducia

Modificare un nodo invalida le occorrenze diagnostiche incidenti; modificare un’occorrenza
invalida il suo certificato. I dati intatti, compresi i campi sconosciuti, rimangono nel
JSON; gli stati precedenti restano consultabili nella base e nel diff congelati.

Accettazione della versione, verifica V3 e decisione umana sono distinte. Una conferma
esplicita vale soltanto per l’hash del contenuto corrente; una modifica successiva la
fa scadere. Una relazione può essere utilizzabile grazie a una conferma umana con
`tier: null`, senza certificato inventato. Grafico, tabelle e dettagli distinguono
confermata, verificata, da verificare e rifiutata. I contatori del catalogo separano
verifiche automatiche, conferme umane, dubbi e rifiuti; gli archi derivati non gonfiano
quelli diagnostici. Il rifiuto di un’occorrenza non nasconde altre occorrenze attive.

L’indice integrale del PDF viene usato soltanto quando tutte le citazioni incorporate
corrispondono a testo, pagina e bounding box. Se la fonte non è ricostruibile, rimangono
leggibili le citazioni incorporate; nuove associazioni e apertura di un PDF non
verificabile vengono impedite. Una revisione non cambia fonte quando cambia il run.

I controlli distinguono difetti ereditati e introdotti. I confronti delle condizioni
sono prudenti: compatibilità per uguaglianza o assenza di condizioni, non un motore
logico del linguaggio naturale. I nomi simili sono suggerimenti, senza merge automatici.
Le metriche descrivono completezza e documentazione, non correttezza tecnica.
Le operazioni tipizzate sono anche il punto di estensione per suggerimenti futuri;
non esistono chiamate AI nel percorso dell’editor.

## Verifiche automatizzate

| Criteri della sezione 12 | Copertura principale |
| --- | --- |
| 1, 14 | `editor-entry.test.tsx`, `editor-flow.test.tsx`, `editor-tables.test.tsx` e browser |
| 2, 3 | Selettori/reducer, tabelle, tipi sintetici, persistenza/riapertura e browser |
| 4–7 | `test_ui_graph_document.py`, `test_ui_revisions.py`, reducer/tabelle e stili del renderer |
| 8–10 | PDF locale, indice congelato, fonte cambiata, base byte-identica, due revisioni consecutive |
| 11 | Retry concorrenti, due figli, errore prima della pubblicazione, riavvio, precondizioni, esito in corso, mock di timeout dopo commit |
| 12, 13 | Catalogo, endpoint dei run, guardie dei job e domande della fonte conservate nell’Inbox |
| 15 | Test IT/EN, errori, valori invalidi, filtri vuoti, browser nelle due risoluzioni |

FLOW-01/02 sono automatizzati nei test degli ingressi con eventi finti, libreria e scelta
storica. FLOW-03–14 sono coperti dai test del percorso con il data router reale,
`StrictMode`, POP, blocker, generazioni asincrone, errori certi/incerti e ciclo di vita
persistito. I test backend verificano le scritture assenti prima del clic e gli snapshot
dopo l’accettazione. Il fixture API fallisce se viene costruito un client modello.

## Verifica browser del 30 settembre–1 ottobre 2026

Usato il browser dell’app su FastAPI e build di produzione, con workspace esterno alla
repository in `/tmp/kg-editor-browser`. Fixture artificiali: grafo piccolo con versione
storica, PDF locale di una pagina con due segmenti, schema con campi numerici/booleani/
liste e grafo grande con **601 nodi e 400 relazioni**. Nessuna estrazione a pagamento.

Verificati nel browser:

- redirect di completamento live con SSE sintetico → pulsante dedicato → Modifica;
- libreria e versione storica con base/breadcrumb corretti;
- Modifica → Controlla → Riepilogo → Indietro, due celle e undo conservati;
- uscita/continua, scarto dal breadcrumb, rientro con Indietro senza recupero dei valori;
- navigazione fra prove, relazioni, nodi, grafo e PDF; selezione di un secondo segmento
  e annotazione personale, senza alterare citazioni;
- cambio IT/EN nella sessione, filtri di stato conservati, filtri cumulativi e zero risultati;
- numero invalido che blocca Avanti e avverte in uscita; tastiera Enter/Esc/Tab;
- salvataggio/riapertura di `0`, `false`, `[]`, `null` e testo multilinea;
- due revisioni consecutive con PDF; la prima resta da verificare, la seconda contiene
  una conferma umana esplicita e mantiene `tier: null`;
- 409 reale dopo cambiamento della base: messaggio EN, accettazione disabilitata,
  modifica ancora presente tornando al passo 1;
- IT/EN a **1440×900** e **1024×768**, etichetta finale intera e cambio versione visibile;
- editing, ricerca e passaggio al grafo della fixture grande senza errori del renderer.

Controllati anche i file: zero directory/revisioni prima dell’accettazione; base e PDF
byte-identici; versione e decisione pubblicate insieme. I difetti emersi nella QA
(barra troppo larga e digitazione nella cella ancora a fuoco dopo Esc/Enter) sono stati
corretti e il salvataggio tipizzato è stato ripetuto sul file e nella riapertura UI.
Gli screenshot di QA sono in `/tmp/kg-editor-browser/*.png`, esterni alla repository.

**Limite della verifica:** il browser pilotato non ha esposto un dialogo nativo
`beforeunload` durante il tentativo di ricarica. Non viene quindi dichiarata verificata
visivamente quella finestra. Guardie unload e reset bfcache sono coperti da eventi
nei test; navigazione, scarto e cronologia sono stati provati anche nel browser reale.
La sessione browser interrotta e riaperta non ha recuperato alcuna bozza.

Fixture browser riproducibili, con estrazione/applicazione/approvazione disabilitate:

```bash
npm --prefix frontend run build
.venv/bin/python -m tests.graph_editor_browser_fixture --root /tmp/kg-editor-qa
# In un secondo terminale, dopo aver aperto /manuali/livepump/versioni/runs~v3_r1/esecuzione:
.venv/bin/python -m tests.graph_editor_browser_fixture --root /tmp/kg-editor-qa --finish-live
```

Aprire `http://127.0.0.1:8017/`. I manuali sono sintetici e i salvataggi modificano
soltanto il workspace di prova indicato. Non usare una directory di dati reali come root.

Verifica finale del 1 ottobre: Ruff senza errori, **270 test Python passati**,
**68 test frontend passati** in 13 file, build di produzione riuscita e
`git diff --check` senza errori. La suite completa è stata eseguita nel workspace condiviso; le modifiche concorrenti della pipeline e della guida preesistente sono
preservate e non incluse nel commit dell’editor.
