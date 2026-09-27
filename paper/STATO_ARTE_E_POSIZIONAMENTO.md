# Stato dell'arte e posizionamento del paper

Nota di coordinamento del 2026-09-27. L'analisi completa, con 20 lavori letti per intero
e 8 rischi da ottenere, è in [state_of_the_art_maintenance_kg.md](state_of_the_art_maintenance_kg.md)
(in inglese, con BibTeX verificato alla sezione 10); questa nota ne riassume le
conseguenze e aggiunge una ricerca mirata sui lavori più recenti. Le fonti marcate **[verificata]** hanno autori e sede controllati sulla
pagina originale e sono in `references.bib`; le altre sono **[da verificare]** prima di
citarle. Nessuna affermazione qui è un risultato: i numeri della V3 sono in
[docs/V3_RISULTATI_SVILUPPO.md](../docs/V3_RISULTATI_SVILUPPO.md).

## 1. Cosa esiste

**LLM e grafi per la diagnosi dei guasti.** Filone molto affollato nel 2025–2026:
diagnosi CNC con LLM e grafi di dominio, pipeline FDRKG-LLM su International Journal of
Production Research, grafi per la diagnosi di componenti automotive, sistemi HVDC, una
revisione sistematica su come LLM e grafi migliorino la diagnosi **[da verificare]**.
Quasi tutti usano il grafo *per ragionare* (chatbot, RAG, suggerimento di cause); la
costruzione del grafo è un passo intermedio, spesso da log, FMEA o documenti già
strutturati, valutata poco o in modo qualitativo.

**Costruzione di grafi con LLM in generale.** La survey di Bian (2025) **[verificata]**
organizza il campo in ingegneria dell'ontologia, estrazione e fusione, con approcci a
schema fisso o libero. Lavori come EDC, KGGen, iText2KG e i benchmark tipo Text2KGBench
lavorano su testo pulito, non su PDF con tabelle e procedure.

**Radicamento e provenienza.** Il lavoro più vicino al nostro è **AEVS**, *Grounded
Knowledge Graph Extraction via LLMs: An Anchor-Constrained Framework with Provenance
Tracking*, rivista MDPI Computers, 2026 **[da verificare: autori]**. Scopre prima gli
"anchor" nel testo con le loro posizioni, vincola l'estrazione a quel vocabolario chiuso,
verifica per ricostruzione e completa la copertura. Riporta tassi di allucinazione dallo
0,23% al 20,23% con 2,8–4,3 chiamate per campione. Lavora su testo, senza layout PDF e
senza revisione umana.

**Uomo nel ciclo.** La revisione di Bajestani, Mun e Kim sul Journal of Manufacturing
Systems (2026) **[verificata]** mappa 180 studi su LLM e human-in-the-loop in manifattura
e propone una struttura concettuale (HITL, sistemi cyber-fisici, LLM, verifica e
validazione); è concettuale, non misura lo sforzo umano. CleanGraph di Bikaun, Stewart
e Liu (2024) **[verificata]** è uno strumento di revisione interattiva di grafi. Un lavoro
CIRP del 2025 costruisce grafi di asset da manuali e FMEA con raffinamento iterativo di
esperti **[da verificare]**. Esistono anche verificatori di triple con LLM ("LLM as graph
judge") **[da verificare]**.

**Uso a valle.** Mandarapu e Kunkunuru (2026) **[verificata]** mostrano su AssetOpsBench
che un grafo tipizzato come strato dati porta un agente per la manutenzione dal 65%
all'82–83% di scenari risolti, e fino al 99% con primitive di grafo senza LLM. È la
motivazione migliore per il nostro obiettivo: il grafo conta più del modello.

## 2. Lettura critica: dove i lavori esistenti sono deboli

1. **Documenti veri.** Pochi affrontano PDF di manuali con tabelle a celle unite,
   procedure numerate con sotto-passi, frasi spezzate su più righe. È esattamente dove
   la nostra v22 falliva e dove la V3 ha guadagnato di più.
2. **Provenienza solo testuale.** AEVS radica le triple a posizioni di carattere in
   testo lineare; non usa la struttura della pagina (riga, passo, blocco) come prova.
3. **Lo sforzo umano non si misura.** Si scrive "serve l'uomo nel ciclo", ma quasi mai
   quante domande, quanto tempo, con quale qualità finale. Lo sforzo è implicito e
   illimitato: rivedere tutto il grafo.
4. **Valutazione fragile.** Gold piccoli o costruiti dagli stessi autori, confronti
   lessicali, una sola esecuzione, nessun costo, nessuna prova su produttori nuovi.
5. **"Agnostico" senza prova.** Si dichiara generalità su un solo tipo di macchina.

Onestamente, anche i nostri componenti presi uno per uno **non sono nuovi**: citazioni
vincolate (AEVS), verifica con LLM (graph judge, chain-of-verification), accordo tra
letture (self-consistency), uomo nel ciclo (CleanGraph, revisione JMS). Un paper che
vendesse uno di questi pezzi come novità verrebbe respinto.

## 3. Dove possiamo distinguerci davvero

L'analisi completa corregge un eccesso di ottimismo: anche i due contributi che sembravano
più nostri hanno precedenti diretti. La struttura dei documenti formattati come fonte di
prova c'è già in **Fonduer** (SIGMOD 2018); la divisione del lavoro tra persona e LLM guidata
dall'incertezza c'è già in **CoAnnotating** (EMNLP 2023). Estrazione di procedure da
manuali e flowchart di manutenzione: Rula e D'Souza (K-CAP 2023), **FlowExtract** (APMS
2026). Rischi ancora da leggere per intero: grafo di manutenzione "task-centric"
multimodale (Liu e Lu, Engineering Reports 2024) e **alberi di troubleshooting generati
con LLM** (Vidyaratne et al., IEEE ICPHM 2024 e 2025): vanno ottenuti prima di scrivere
qualsiasi frase sulla novità.

Il contributo difendibile è quindi **empirico e integrato**, non un singolo algoritmo:

1. **Preservazione dei rami diagnostici a parità di copertura.** Quanto bene un sistema
   mantiene insieme problema, causa e rimedio dello stesso ramo del manuale (tabelle a
   celle unite, procedure numerate), con provenienza per occorrenza. Prova: recall dei rami
   per significato sul gold, contro baseline e ablation.
2. **Sforzo umano reale a parità di qualità finale.** Non "meno segnalazioni", ma minuti
   reali di un esperto per arrivare alla stessa qualità del grafo, con domande raggruppate
   per ramo e un budget, e con il confronto agente-persona sulle stesse domande. Prova: curva
   qualità-sforzo e tempo cronometrato. Nessun lavoro letto misura questo per grafi di
   manutenzione da manuali.
3. **Trasferimento tra produttori e settori** con gold cieco e congelamento del codice:
   la fase C del protocollo.

Le singole tecniche (testimoni strutturali, accordo tra letture, verificatore, certificati)
si presentano come scelte di progetto con ablation, citando i precedenti, non come novità.

## 4. Come inquadrarlo: HITL, simbiosi o altro?

- **"Human-in-the-loop"** è il termine che i revisori cercano, ma da solo è generico e
  suggerisce "l'uomo rivede tutto". Va qualificato: *bounded*, *selective*, *auditable*.
- **"Human symbiosis"** è suggestivo ma poco usato nella letteratura tecnica e rischia di
  sembrare marketing. Meglio **"human–AI teaming"** o **"hybrid intelligence"**, e il
  richiamo a **Industry 5.0 / human-centric manufacturing**, che è il linguaggio di Journal
  of Manufacturing Systems e Computers in Industry.
- Il messaggio forte è economico e verificabile: *l'esperto fa poche domande mirate
  invece di rivedere un grafo intero, e ogni sua decisione resta tracciata*. La v22 dava
  26–157 segnalazioni per manuale; la V3, sugli stessi manuali, 0–2 domande.
- La sostituibilità del revisore umano con un agente va presentata con cautela: non
  come "l'uomo non serve", ma come modo per **misurare** dove l'uomo aggiunge valore
  (domande che l'agente non risolve, errori che l'agente accetta).

Titoli possibili:

- *Cite, Check, Ask: Evidence-Bound Maintenance Knowledge Graphs with Bounded Human Verification*
- *Structural Witnesses and Bounded Expert Review for Trustworthy Knowledge Graphs from Maintenance Manuals*
- *How Much Human Is Needed? Building Verified Maintenance Knowledge Graphs from Technical Manuals*

Riviste adatte: Journal of Manufacturing Systems (ha appena pubblicato la revisione HITL
e LLM), Computers in Industry, Advanced Engineering Informatics, Journal of Industrial
Information Integration. Da scegliere con i coautori.

## 5. Cosa serve perché il paper sia accettato

| Requisito | Stato | Cosa fare |
| --- | --- | --- |
| Test su manuali nuovi, produttori diversi | pianificato | fase C del [protocollo](evaluation/PROTOCOLLO_V3.md), 6–8 manuali |
| Gold serio | 34 casi rivisti dall'autore | un annotatore per la campagna, ricontrollo a distanza, limite dichiarato |
| Baseline forti | solo v22 | estrazione diretta con lo stesso modello; baseline tipo AEVS o EDC (vincolo di citazione o canonicalizzazione senza testimoni e senza domande); vedi sezione 7.3 dell'analisi completa |
| Ablation | assenti | senza struttura, senza accordo, senza verificatore, senza agente revisore, K variabile |
| Precisione umana cieca | foglio pronto | compilarlo sui manuali della campagna |
| Sforzo umano misurato | domande contate | cronometrare le risposte; confronto agente–persona |
| Stabilità e costo | misurati | riportare min/max e USD per manuale |
| Uso a valle | motivato con la letteratura | piccolo esperimento: domande di manutenzione con e senza grafo, con citazioni |
| Dipendenza dal modello | un solo modello | una ripetizione con un secondo modello su un sottoinsieme |
| Riproducibilità | registro, archivio, replay | rilasciare codice, gold e grafi dove le licenze dei manuali lo permettono |

## 6. Rischi

- **Un solo annotatore**, che è anche l'autore: dichiararlo, ricontrollo a distanza,
  revisione cieca separata della precisione.
- **Contaminazione sviluppo–test**: i manuali del test non si aprono prima che il gold
  sia chiuso e il codice congelato.
- **Lavori concorrenti**: ottenere per intero Liu e Lu 2024 e gli alberi di troubleshooting
  ICPHM 2024/2025 prima di scrivere; aggiornare questa nota prima della scrittura. Il nostro
  spazio è documenti reali, sforzo umano misurato e generalizzazione tra produttori, non la
  singola tecnica.
- **Numeri di sviluppo gonfiati**: nel paper vanno solo i numeri della fase C.

## Fonti consultate

- Bian, *LLM-empowered knowledge graph construction: A survey*, arXiv:2510.20345, 2025.
- Bajestani, Mun, Kim, *Human-in-the-loop and large language models in smart manufacturing*,
  Journal of Manufacturing Systems 86, 2026. <https://www.sciencedirect.com/science/article/pii/S0278612526001135>
- Bikaun, Stewart, Liu, *CleanGraph: Human-in-the-loop Knowledge Graph Refinement and
  Completion*, arXiv:2405.03932, 2024.
- Mandarapu, Kunkunuru, *Knowledge Graphs as the Missing Data Layer for LLM-Based Industrial
  Asset Operations*, arXiv:2605.26874, 2026.
- AEVS, *Grounded Knowledge Graph Extraction via LLMs: An Anchor-Constrained Framework with
  Provenance Tracking*, Computers (MDPI) 15(3):178, 2026, <https://www.mdpi.com/2073-431X/15/3/178>,
  codice <https://github.com/yyz-nbt/AEVS> — autori da verificare.
- Da verificare: revisione sistematica LLM e grafi per la diagnosi
  (<https://www.sciencedirect.com/science/article/pii/S156849462600356X>), grafi per la
  diagnosi di componenti automotive (<https://www.sciencedirect.com/science/article/pii/S2950550X2600049X>),
  FDRKG-LLM (<https://www.tandfonline.com/doi/full/10.1080/00207543.2025.2472298>), grafo di
  asset da manuali CIRP 2025 (<https://www.sciencedirect.com/science/article/pii/S2212827125004469>),
  *Can LLMs be Good Graph Judge for Knowledge Graph Construction?* (arXiv:2411.17388),
  KEO per la manutenzione aeronautica (arXiv:2510.05524).
