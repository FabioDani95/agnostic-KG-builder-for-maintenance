# V3: risultati sui quattro manuali di sviluppo

Esecuzioni del 2026-09-26, codice V3 non ancora committato sopra `a699f6f`,
GPT-6 Luna (estrazione `low`, revisore agente `medium`), cancelli tutti gestiti
dall'agente (`--gates agent`), due ripetizioni indipendenti (r1, r2). Artifact:
[paper/experiments/v3_dev_20260926](../paper/experiments/v3_dev_20260926/),
confronto in [comparison.json](../paper/experiments/v3_dev_20260926/comparison.json),
script [kg_v3_compare.py](../scripts/kg_v3_compare.py). La v22 di riferimento è la
campagna congelata C11/C12 ([report](../paper/experiments/robustness_continuation_20260926/REPORT.md)).

Sono misure di sviluppo sugli stessi quattro manuali usati per costruire il
sistema, non una valutazione indipendente: il gold storico copre 34 casi scelti,
non è stato validato da tecnici, e il confronto è lessicale.

## Misura rivista: posizione e significato

Il primo confronto contava le parole in comune con il gold e sottostimava i
risultati: "Clear the restricted line" contro "clear the restriction" risultava
un errore. [kg_v3_evaluate.py](../scripts/kg_v3_evaluate.py) misura invece così:

1. **Posizione.** I 34 casi del gold storico sono stati riscritti come segmenti del
   manuale ([gold_segments_v1](../paper/evaluation/gold_segments_v1/)): mappati in
   automatico, controllati dall'agente, con una correzione a mano (E5). Un tecnico
   deve ancora confermarli. Una relazione è candidata se cita quei segmenti.
2. **Significato.** Un giudice LLM separato decide se candidata e gold dicono la
   stessa cosa. Vota tre volte e vince la maggioranza. I rimedi di una stessa causa
   si giudicano insieme, perché la V3 divide "clear valve; replace seals" in due azioni.

Un caso è recuperato quando problema → causa e causa → rimedio corrispondono
attraverso la stessa causa. Stesso gold, candidati e giudice per entrambi i sistemi
([evaluation_v2.json](../paper/experiments/v3_dev_20260926/evaluation_v2.json)).

| Manuale | v22 | V3 r1 | V3 r2 | V3 r3 | V3 r4 |
| --- | --- | --- | --- | --- | --- |
| Eastman (8) | 6 | 6 | 7 | 7 | 7 |
| Danfoss (8) | 5 | 8 | 8 | 8 | 8 |
| Graco (18) | 17 | 18 | 11 | 18 | 18 |

r1 e r2 usano il codice del primo commit. La caduta di Graco r2 non era un errore
del modello. Una lettura aveva scritto "clear the piston valve and replace the
seals" come azione unica; nell'unione dei nodi quel nome composto ha fuso due
azioni distinte e "Replace the piston valve seals" è sparita dal grafo. Il bug è
corretto (nomi uniti solo se davvero simili, un'azione per rimedio nel prompt) e
coperto da un test. r3 e r4 usano il codice corretto.

Eastman E4 manca sempre alla V3: il manuale non nomina la causa e la V3 scrive
"causa non specificata", mentre il gold la deduce dal rimedio.

La **precisione**, cioè quante relazioni del grafo sono giuste, richiede un tecnico:
[revisione cieca](../paper/evaluation/v3_precision_review/README.md) di 96
affermazioni, 12 per sistema e per manuale, campionate da V3 r3 e dalla v22.

## In breve (prima misura, lessicale)

| Manuale | Casi gold recuperati v22 → V3 (r1, r2) | Cose per una persona v22 → V3 | Tempo v22 → V3 | Costo API v22 → V3 (USD) |
| --- | --- | --- | --- | --- |
| Eastman E-554 | 4/8 → 4, 5 | 75 → 0, 0 | 1013 s → 77, 96 s | 0,053 → 0,015, 0,016 |
| Danfoss APF | 5/8 → 8, 8 | 26 → 1, 1 | 111 s → 50, 60 s | 0,016 → 0,011, 0,009 |
| Graco Check-Mate 200 | 16/18 → 16, 16 | 64 → 0, 0 | 162 s → 59, 52 s | 0,022 → 0,009, 0,008 |
| Hypertherm Powermax30 AIR | senza gold | 157 → 0, 1 | 1615 s → 152, 184 s | 0,122 → 0,079, 0,085 |

- **Cose per una persona.** Per la v22 sono le segnalazioni in coda. Per la V3
  sono le domande che l'agente revisore non ha saputo decidere. Nella stessa
  esecuzione l'agente ha risolto da solo tra 2 e 52 domande per manuale, sempre
  con una motivazione registrata.
- **Tempo e costo.** Il tempo è quello dell'intera esecuzione. Il costo è quello
  prudenziale del registro condiviso (`real_call_budget.jsonl`). Il totale speso
  finora è 2,01 USD sui 20 autorizzati.
- **Nessuna lettura persa.** In tutte e otto le esecuzioni `failed_reads` è 0.

## Il grafo

| Manuale | Relazioni verdi (r1, r2) | Gialle | Rosse, fuori dal grafo | Relazioni v22 |
| --- | --- | --- | --- | --- |
| Eastman | 80, 88 | 0, 0 | 7, 15 | 159 |
| Danfoss | 38, 40 | 0, 0 | 0, 1 | 60 |
| Graco | 53, 47 | 0, 0 | 2, 1 | 84 |
| Hypertherm | 385, 386 | 0, 1 | 22, 20 | 182 |

Le relazioni della v22 comprendono molti `HAS_COMPONENT` ricavati da liste di
parti: su Eastman 133 nodi su 157 erano componenti. La V3 tiene solo i
componenti coinvolti in un guasto, quindi il grafo è più piccolo ma contiene
più catene diagnostiche. Su Graco, ad esempio, ci sono tutte le 18 righe della
tabella con azioni come "Clear the restricted line" o "Replace the intake valve seals".

## Cosa manca e perché

- **Graco G1 e G5.** L'azione estratta è "Clear the restricted line", il gold
  dice "clear the restriction": il confronto lessicale non le accoppia. Il
  contenuto è presente.
- **Eastman E3 ed E7.** Sono presenti in entrambe le esecuzioni con parole
  diverse: "Tool mapping in software is incorrect", "Beam-deflecting mirrors are
  damaged, burned, or dirty". Il confronto lessicale li perde.
- **Eastman E4.** La V3 estrae "sostituire i filtri del vuoto", ma con causa
  "non specificata", perché il manuale non nomina un guasto. Il gold storico
  deduce la causa dal rimedio; l'audit precedente lo aveva già segnalato come
  caso da discutere con i tecnici.
- **Eastman E2** in r1: la procedura di calibrazione è divisa in più azioni. In
  r2 c'è la catena completa.

Questi controlli li ho fatti leggendo i grafi. Non sono una validazione tecnica
e non danno precisione o recall semantici.

## Il cancello della mappa

Il revisore agente ha corretto la mappa del modello: su Hypertherm r1 ha tolto
11 pagine di montaggio e sostituzione componenti (55, 158–169) etichettate per
errore come diagnostiche. La rete di sicurezza strutturale ha recuperato Eastman
p. 38, prima esclusa.

## Limiti noti

- Restano alcuni quasi-doppioni con parole diverse tra pagine diverse (Eastman:
  due catene "causa non specificata" con le stesse azioni) e qualche componente
  discutibile (Eastman: "Tool and layer mapping").
- Le domande per le persone non hanno ancora API e interfaccia; nell'app finiscono
  nella coda di revisione come domande.
- Il costo del revisore agente è incluso nel registro. Il costo del lavoro umano
  non è misurato.
