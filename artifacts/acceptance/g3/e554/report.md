# G3 acceptance campaign — Eastman Eagle S3L E-554

## Verdetto

**G3 non è accettabile nello stato corrente e non conviene procedere al merge dei sottografi.**

Il percorso reale da UI funziona fino in fondo e il sistema fallisce in modo sicuro: il CSV è stato approvato, il PDF è stato segnalato da correggere e la barriera di merge è rimasta chiusa. Il sottografo PDF contiene però difetti di qualità e revisione sufficienti a bloccare l'accettazione.

## Fixture e percorso eseguito

- Manuale: `/Users/fabiodaniele/Downloads/E-554.pdf`, 54 pagine, SHA-256 `a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0`.
- CSV sintetico: `synthetic_eagle_s3l_logs.csv`, 11 righe, incluse due righe intenzionalmente duplicate.
- Modello reale: `gpt-5.6-terra`.
- Workspace: `ws_KDXOoS3tgJcUSGP-NfuzSA`.
- Percorso UI: creazione macchina, upload PDF, upload CSV, conferma mapping, generazione di entrambi i sottografi, revisione, decisione e reload di persistenza.

## Risultato CSV

- 39 nodi, 40 relazioni, 11 evidenze, 0 lacune.
- Validazione stretta superata; approvabile.
- Le 11 righe sono state contabilizzate senza scarti.
- Il duplicato intenzionale è stato consolidato semanticamente, mantenendo entrambe le righe come evidenza.
- Decisione UI: **Verificata**; persistenza confermata dopo reload.

## Risultato PDF

- 39/54 pagine selezionate (72,2%); le pagine diagnostiche 37–39 sono state mantenute.
- 345 nodi, 288 relazioni, 518 evidenze e 30 lacune.
- Tutte le 8 catene diagnostiche minime attese sono presenti; nessuno dei 3 abbinamenti proibiti è presente.
- La validazione strutturale passa e tutte le 518 evidenze referenziate sono risolvibili.
- Non esiste però alcun nodo `Asset`: l'identità prodotta dal PDF non coincide con quella canonica del workspace.
- 19/30 lacune sono citazioni mancanti; sono inoltre presenti riferimenti di pagina palesemente incoerenti con la sezione troubleshooting.
- Due gruppi sono duplicati anche dopo normalizzazione e sono presenti diversi duplicati semantici cross-chunk, per esempio le due varianti della calibrazione touch screen e le varianti del circuito di pausa.
- Decisione UI: **Da correggere**; persistenza confermata dopo reload.

## Difetti prioritari

1. **Asset canonico assente.** Il bridge scarta il nodo `Asset` quando l'ID generato non coincide con quello del workspace (`pdf_source_subgraph_generation.py`, righe 397–404). La validazione successiva controlla bene ciò che è presente, ma non rende obbligatoria la radice Asset; l'approvazione viene bloccata solo dalla knowledge gap.
2. **Scoping troppo inclusivo.** Le sezioni rule-based, LLM e keyword vengono unite anche quando il ToC è disponibile (`scoping_workflow.py`, riga 479; `cutplan_service.py`, righe 496–503). Sono entrate installazione, checklist, diagrammi elettrici/pneumatici e pagina FCC, con 17 chunk e circa 12 minuti di generazione.
3. **Deduplicazione cross-chunk insufficiente.** Il grafo mostra cause e componenti equivalenti come nodi separati; questo moltiplica catene e rende la revisione manuale poco affidabile.
4. **Provenance strutturalmente valida ma semanticamente imprecisa.** Il sistema risolve 518/518 ID, ma 19 relazioni dichiarano una pagina senza una citazione verificabile e alcune pagine indicate sono errate. La risolvibilità dell'ID non basta come metrica di grounding.
5. **Contraddizione UI sulle lacune.** La pagina mostra “Cosa manca 30”, ma il filtro “Solo con lacune” è disabilitato e dichiara che nessun elemento ha lacune. `frontend/app/graph.js` associa ai nodi solo i codici delle lacune strutturate (righe 32–43), ignorando i codici `pdf_*`.
6. **Revisione troppo onerosa.** La ricerca elementi funziona e nasconde correttamente 337/345 elementi nel caso “Touch screen”, ma la mappa completa a 345 nodi non è una superficie di approvazione realistica. Inoltre la ricerca resta visibile nella tab “Cosa manca” senza filtrare le 30 lacune.
7. **Osservabilità incompleta.** Il run conserva conteggi, revisioni e audit decisionale, ma non persiste/esibisce l'aggregato completo token/costo della generazione PDF G3.

## Preparazione al merge

Se entrambi i sottografi fossero approvati, il matcher esatto corrente troverebbe soltanto 7 nodi condivisi, nonostante il CSV sia stato costruito dallo stesso manuale. Le cause e le azioni equivalenti hanno formulazioni diverse e richiederanno matching semantico nel merge; questa è una criticità di readiness, non un motivo per forzare l'approvazione del PDF.

## Correzioni richieste prima del rerun

1. Riconciliare sempre il nodo Asset con l'identità canonica del workspace.
2. Separare scoping diagnostico, manutenzione programmata e inventario componenti; non usare il keyword scan come unione espansiva quando ToC/LLM sono disponibili.
3. Consolidare nodi semanticamente equivalenti tra chunk prima di produrre la revisione fonte.
4. Rendere claim-level la provenance e scartare o mettere in review le relazioni con pagina/quote incoerente.
5. Mappare le lacune `pdf_*` ai nodi/relazioni e rendere coerenti filtri, badge e testi UI.
6. Persistire durata, chiamate, token e costo aggregato del run G3.

Il rerun deve usare gli stessi `gold.json`, PDF e CSV: in questo modo il confronto resta riproducibile e non si spostano i criteri dopo aver visto il risultato.
