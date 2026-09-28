# Campagna di valutazione V3

Qui sta tutto ciò che serve per valutare la pipeline su manuali nuovi: input, gold,
esecuzioni e risultati. Regole e KPI: [protocollo](../paper/evaluation/PROTOCOLLO_V3.md).
Un solo comando: `.venv/bin/python scripts/campaign.py <passo>`.

## Struttura

```text
campaign/
  real_call_budget.jsonl       costi di tutta la campagna, tetto 10 USD
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

## Cosa sta altrove

- Codice della pipeline: [backend/kg_v3](../backend/kg_v3/); piano: [docs/PIANO_V3.md](../docs/PIANO_V3.md).
