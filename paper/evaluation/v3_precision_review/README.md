# Revisione cieca della precisione

Scopo: sapere quanto ci si può fidare delle relazioni che il sistema mette nel
grafo. Un tecnico giudica un campione di affermazioni confrontandole con il
manuale, senza sapere quale sistema le ha prodotte.

## File

- [REVISIONE_PRECISIONE.md](REVISIONE_PRECISIONE.md): il foglio da compilare, con
  affermazioni in ordine casuale. Metà vengono dalla nuova pipeline V3, metà
  dalla v22 congelata, 12 per sistema e per manuale.
- [REVISIONE_PRECISIONE_revisione_AI.md](REVISIONE_PRECISIONE_revisione_AI.md): lo stesso
  foglio compilato da un assistente AI (Codex) il 2026-09-27. È una revisione preliminare,
  non cieca in senso pieno (l'assistente conosce lo sviluppo della pipeline) e non vale
  come giudizio tecnico. Il tecnico deve usare il foglio pulito.
- `chiave_non_aprire.json`: collega ogni voce al sistema che l'ha prodotta. Il
  revisore non deve aprirlo, altrimenti la revisione non è più cieca.
- I PDF dei manuali sono in `paper/manuals/files/`, e servono se il testo mostrato
  non basta.

## Come si compila

Per ogni voce `R001`, `R002`, ... si legge **Il manuale dice** e **Il grafo
afferma**, poi si sostituisce `?` nella riga `- Giudizio:` con una lettera:

| Lettera | Significato |
| --- | --- |
| `C` | corretto: il manuale afferma questo fatto, anche con parole diverse |
| `P` | parziale: giusto ma incompleto o impreciso in modo che conta |
| `S` | sbagliato: il manuale non lo dice, lo dice di un'altra riga o problema, o dice il contrario |
| `N` | non valutabile: il testo non basta nemmeno guardando il PDF |

Per `P`, `S` e `N` si aggiunge una nota breve. In cima al file si scrivono il nome
del revisore, la data e il tempo totale impiegato.

## Calcolo

```bash
.venv/bin/python scripts/kg_v3_precision_sheet.py score
.venv/bin/python scripts/kg_v3_precision_sheet.py score --sheet paper/evaluation/v3_precision_review/REVISIONE_PRECISIONE_revisione_AI.md
```

Il comando stampa, per sistema e per manuale, i conteggi C/P/S/N e la precisione
C/(C+P+S) con intervallo di confidenza al 95% (Wilson), più la precisione che
conta anche i parziali. Il campione è piccolo: 12 voci per cella danno intervalli
larghi. Il confronto va letto sul totale per sistema.

Rigenerare il foglio cambia il campione (seme fisso `20260927`, ma dipende dal
run indicato) e cancella le risposte già date: salvare prima una copia.
