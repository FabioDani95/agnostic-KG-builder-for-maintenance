# Campagna di valutazione V3

Qui sta tutto ciò che serve per valutare la pipeline su manuali nuovi: input, gold,
esecuzioni e risultati. I protocolli del manoscritto sono conservati separatamente
nello spazio privato dell'autore e non sono inclusi nel repository condiviso.
Un solo comando: `.venv/bin/python scripts/campaign.py <passo>`.

## Struttura

```text
campaign/
  real_call_budget.jsonl       costi di tutta la campagna, tetto 20 USD
  results/                     KPI di tutti i manuali e foglio della precisione
  <manuale>/
    manual.pdf                 input: il PDF (resta locale, non va in git)
    info.yaml                  input: macchina e split (dev o test)
    manual.json                impronta del PDF e pagine senza testo
    gold/TESTO.md              testo di tutto il manuale in segmenti con ID
    gold/ANNOTAZIONE.md        il gold, scritto a mano
    gold/gold.json             il gold letto dal foglio
    runs/v3_r1 … v3_r3/        grafo (graph.json), rapporto, domande per le persone
    runs/v22/                  grafo della v22 dove esiste (solo i sei manuali già eseguiti), per confronto
```

## Passi

| Passo | Chi | Comando |
| --- | --- | --- |
| 1. Crea la cartella del manuale | Claude o Fabio | `campaign.py new <id>` |
| 2. Metti `manual.pdf` e compila `info.yaml` | Fabio | — |
| 3. Genera testo e foglio vuoto | Claude | `campaign.py prepare <id>` |
| 4. Annota `gold/ANNOTAZIONE.md` guardando il PDF e `TESTO.md` | Fabio | — |
| 5. Leggi il gold e controlla gli errori | Claude | `campaign.py gold <id>` |
| 6. Esegui 3 volte la V3 | Claude | `campaign.py run <id>` |
| 7. Calcola i KPI | Claude | `campaign.py kpi` |
| 8. Revisione cieca della precisione | Fabio | `campaign.py precision`, poi `precision --score` |

`campaign.py status` mostra a che punto è ogni manuale e quanto si è speso. Il gold va
scritto prima del passo 6: chi annota non deve vedere i grafi di quel manuale.

## Gold v2 (fatto da un'AI)

Il gold v2 è un secondo gold, più ampio: l'elenco di tutta la conoscenza diagnostica di ogni manuale,
pagina per pagina. **Lo ha scritto un'AI**, non una persona: annotatori, verificatore indipendente,
secondo annotatore sul 25% delle pagine e aggiudicatore sono Claude Opus 5.5, coordinati da Claude
Fable 5.2 che controlla a campione sul PDF. Finché Fabio non compila
`REVISIONE_FABIO.md`, nel file resta `human_review: false`. Il gold v1 in `gold/` resta congelato.
Esiste per tre manuali: `grizzly_g0872`, `graco_gtx_2000ex` e `lg_lmh2235st`; gli altri cinque non lo
hanno, per contenere il costo. Stato e numeri: [docs/evaluation.md](../docs/evaluation.md).

```text
  <manuale>/gold_v2/
    gold.json              rami, procedure, inventario delle entità, domande per l'agente
    PAGINE.md              ogni pagina del PDF: che cosa contiene e se è diagnostica
    NOTE.md                decisioni, dubbi, errori del manuale, verifica e accordo tra annotatori
    CONFRONTO_V1.md        confronto con il gold v1, fatto solo a gold v2 chiuso
    REVISIONE_FABIO.md     campione da far giudicare a una persona
    claims_v1_format.json  il gold v2 nel formato del v1, per lo scorer storico
```

Ogni elemento ha una categoria e uno scope: `core` (guasti, codici, diagrammi di flusso), `extended`
(test, manutenzione con condizione di guasto, procedure) e `context` (sicurezza, routine). La valutazione
sceglie il perimetro. Comandi, senza chiamate a modelli:

```sh
.venv/bin/python scripts/kg_gold_v2.py validate <manuale>       # schema, segmenti, citazioni, pagine, rimandi
.venv/bin/python scripts/kg_gold_v2.py stats                    # numeri per categoria e scope
.venv/bin/python scripts/kg_gold_v2.py export-claims <manuale>  # scrive claims_v1_format.json
```

## Cosa sta altrove

- Codice della pipeline: [backend/kg_v3](../backend/kg_v3/); architettura corrente: [docs/architecture.md](../docs/architecture.md).
