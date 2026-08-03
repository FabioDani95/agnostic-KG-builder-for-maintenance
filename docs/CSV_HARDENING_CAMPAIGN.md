# Campagna di hardening CSV

## Obiettivo e stato

Questa campagna verifica il percorso deterministico:

```text
CSV → RawUnit per riga → EvidenceUnit → sottografo source-scoped → validazione → review umana
```

Non approva un grafo e non effettua merge tra fonti. Il gate G3 rimane aperto.

## Regole di costruzione del grafo

Il parser e il generatore non usano LLM. Il comportamento è ripetibile a parità
di file e mapping profile.

1. Il parser rileva encoding/delimitatore, applica quote CSV standard e isola
   le righe con forma incompatibile.
2. Gli alias versionati propongono ruoli (`observation`, `cause`, `action`,
   `component`, `error_code`, `measurement`, `occurred_at`, `outcome`).
3. Un header potenzialmente diagnostico ma sconosciuto richiede una decisione
   HITL; le colonne descrittive non vengono promosse a sintomo o azione per
   semplice somiglianza di suffisso.
4. Ogni riga valida conserva raw hash, locator, attributi e evidence ID.
5. Il generatore crea soltanto relazioni consentite dall'ontologia e fondate
   nella stessa evidenza. Una relazione non accoppiabile non viene inventata.
6. Il consolidamento unisce claim, non evidenze: un nodo è identificato da
   `tipo + label normalizzata`; un arco da `tipo + endpoint`. Ogni oggetto
   contiene tutti gli evidence ID che lo sostengono.

La normalizzazione corregge case, spazi e punteggiatura ordinaria. Non traduce
e non applica sinonimi: `BL-101` e `BL101`, oppure `Low pressure` e
`Pressione bassa`, restano distinti.

## Casi reali eseguiti

| Dataset | Parsing / mapping | Risultato G3 | Stato |
|---|---|---|---|
| `log_manutenzione_linea_packaging_farmaceutico_simulato.csv` | 120 record, mapping confermato; due campi liberi mantenuti come attributi | 217 nodi, 358 relazioni, 120 evidenze; validazione strict verde; nessun gap | `reviewing`, non approvato |
| `log_manutenzione_ro_multilingua.csv` | 120 record, 35 colonne, UTF-8 e `;`; quote escape corrette; mapping operativo EN aggiunto | 115 nodi, 160 relazioni, 120 evidenze; validazione strict verde; 11 gap intenzionali | `reviewing`, non approvato |

### Packaging farmaceutico

Il caso farmaceutico ha dimostrato la catena chiusa da sintomo/errore a causa,
componente e azione. Sono stati consolidati 504 claim-nodo e 482
claim-relazione ripetuti, senza cancellare nessuna delle 120 righe sorgente.

### Osmosi inversa multilingua

Il caso RO ha scoperto e fissato due aspetti importanti:

- `csv.Sniffer` poteva indicare `doublequote=False` anche in presenza di quote
  CSV valide. La correzione mantiene il delimitatore rilevato, ma applica
  `doublequote=True` quando il sample contiene escape standard; 120/120 righe
  sono ora lette correttamente.
- Le stringhe semanticamente equivalenti in lingue diverse restano nodi
  distinti. Per esempio, una formulazione italiana e la sua resa inglese di
  una conducibilità fuori soglia non vengono fuse automaticamente. Il grafo è
  corretto e provato, ma meno compatto finché non esiste un layer canonico
  revisionabile.

Gli 11 gap RO sono attesi dal dataset: cinque cause assenti, tre azioni assenti
e tre pairing sintomo-causa many-to-many ambigui. Bloccano l'approvazione anche
se il payload ontologico è valido.

## Test automatici eseguiti

```bash
.venv/bin/python -m pytest -q tests/planned/test_g2_acceptance.py tests/planned/test_g3_acceptance.py
```

Il set mirato copre 22 casi, inclusa la regressione sulle quote CSV e gli
header operativi multilingua (`opened_at`, `alert_code`, `symptom_reported`,
`process_measurement`, `work_outcome`, `restart_test`).

## Prossima campagna

Nuovi file reali vanno in `manuals/csv_hardening/`, un file per caso. Non
modificare un input dopo un run: crea una copia con suffisso per mantenere la
riproducibilità.

Priorità di hardening:

1. Export CMMS/ERP con codici, valute, null, timestamp e quoting reali.
2. Dataset multi-lingua con concetti equivalenti esplicitamente annotati.
3. Righe duplicate, quasi duplicate e conflittuali per separare occorrenza
   reale da duplicazione di export.
4. Tabelle con molte relazioni e pairing ambiguo.
5. Definizione e test di candidate merge assistiti da LLM, sempre con
   spiegazione, evidence ID e approvazione umana obbligatoria.
