# Come annotare il gold di LG LMH2235ST (primo contatto)

Obiettivo: scrivere **tutti** i rami diagnostici del manuale, a mano, senza assistenti AI e senza
guardare risultati del sistema (per questo manuale non ce ne sono: resta così finché il gold non è
chiuso). Tieni il tempo, in minuti.

## File

- `campaign/lg_lmh2235st/manual.pdf`: il manuale (service manual, 49 pagine).
- `gold/TESTO.md`: il testo diviso in segmenti con ID. Cerca `=== page 14 ===` per saltare alla pagina.
- `gold/ANNOTAZIONE.md`: il foglio da compilare.

Qui le pagine del file coincidono circa con l'indice del manuale, ma usa sempre quelle del
**file** (`=== page N ===`).

## Cosa contiene (da una prima occhiata, il perimetro lo decidi tu)

- **p. 12:** autodiagnosi e **codici d'errore** (F-1, F-2, F-4) con il loro significato.
- **p. 13:** *Basic Check Summary*, cioè sintomi e controlli di base (aperto/corto, porta chiusa o aperta).
- **pp. 14–24:** *Troubleshooting* a **diagrammi di flusso**: domande sì/no su test di continuità,
  con esito "Replace the …" o "Go to No. N". Ci sono anche i **valori attesi** dei test (per
  esempio "Primary winding: 0.2 ~ 0.5 Ohm").
- **pp. 29–30 in poi:** test di continuità degli interruttori e informazioni per testare i componenti.
- p. 11–12: prova di funzionamento e controlli dopo la riparazione, da valutare.

## Passi

1. **Intestazione del foglio:** Annotatore, Data, Tempo impiegato (minuti), Pagine annotate.
   Vanno bene anche come elenco ("- Annotatore: …").
2. **Perimetro:** sfoglia tutto il PDF, scegli le pagine diagnostiche e scrivile in «Pagine
   annotate». Dentro quelle annota **tutto**.
3. **Diagrammi di flusso: un ramo per ogni esito che dice cosa fare.** Esempio: a p. 15,
   "Is there any beeping sound in the continuity test between the ends of the
   fuse? — No → Replace the fuse" è un ramo:
   - problema = il sintomo del diagramma;
   - azione di controllo = il test;
   - azione di riparazione = la sostituzione;
   - condizione = l'esito del test ("se non c'è segnale acustico").

   "Go to No. N" non è un'azione: indica l'ordine, mettilo nelle condizioni o nella nota.
4. **Codici d'errore:** un ramo per codice. Nel manuale la colonna si chiama *Symptom* ma
   descrive il guasto (per esempio "PCB thermistor short"): decidi tu se è la **causa** o il
   **significato** del codice, e usa lo stesso criterio per tutti.
5. **Tabella di p. 13:** ogni riga (sintomo con porta chiusa o aperta, e il controllo) è un ramo
   con un'azione di tipo `controllo`.
6. **Controllo finale:** lancio io `campaign.py gold lg_lmh2235st`, che deve dare zero errori.
7. **Il giorno dopo:** ricontrolla circa un ramo su cinque.

## Regole dei campi

Come per Grizzly:
- **causa:** come è scritta, oppure `non indicata nel manuale`. Mai dedotta dal rimedio: "Replace
  the fuse" non scrive che il fusibile è guasto.
- **azione:** una riga per istruzione, nell'ordine. `tipo`: `riparazione`, `controllo` o
  `assistenza`.
- **componente:** solo se il manuale dice che quella parte è guasta o da verificare o sostituire.
- **condizioni:** esiti dei test ("se non c'è segnale acustico"), valori attesi ("0,2–0,5 Ω"),
  porta aperta o chiusa, rimandi.

## Esempio (p. 15, diagramma "Does the display operate? No", passo 4)

```text
### Ramo R1
- problema: The display does not operate. | ID: p15.b1, p15.b2
- codice:
- causa: non indicata nel manuale | ID:
- azione: Continuity test between the ends of the fuse. | tipo: controllo | ID: p15.b16, p15.b17
- azione: Replace the fuse. | tipo: riparazione | ID: p15.b18
- componente: Fuse | ID: p15.b17
- condizioni: sostituire se il test di continuità non dà segnale acustico
- nota:
```

Gli ID reali del problema e dei passi li trovi in `TESTO.md`: nei diagrammi il testo è spezzato
in molti segmenti, quindi usa tutti quelli del passo.

Quando hai finito, dimmelo: controllo il foglio e lo eseguiamo con il codice congelato.
