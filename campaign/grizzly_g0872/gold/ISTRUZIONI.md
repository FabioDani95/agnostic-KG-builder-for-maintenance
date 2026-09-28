# Come annotare il gold di Grizzly G0872 (manuale di test)

Obiettivo: scrivere **tutti** i rami diagnostici del manuale, a mano, senza assistenti AI e senza
guardare risultati del sistema (per questo manuale non ce ne sono: resta così finché il gold non è
chiuso). Tieni il tempo.

## File

- `campaign/grizzly_g0872/manual.pdf`: il manuale.
- `gold/TESTO.md`: il testo diviso in segmenti con ID. Cerca `=== page 51 ===` per saltare alla pagina.
- `gold/ANNOTAZIONE.md`: il foglio da compilare.

Attenzione: le pagine sono quelle del **file PDF**, non quelle stampate. La tabella stampata come
pagina 49 è la pagina 51 del PDF.

## Passi

1. **Intestazione del foglio:** Annotatore, Data, Tempo impiegato in minuti, Pagine annotate.
2. **Perimetro.** Sfoglia tutto il PDF e scegli le pagine diagnostiche. Da una prima occhiata:
   - pp. **51–52**: le tabelle Troubleshooting (Electrical, Operations), 5 righe con cause e
     soluzioni numerate. È il cuore;
   - p. **9**: codici di errore della macchina con il loro significato (Frame Slop, Name Over Lap,
     XSlop Over, YSlop Over);
   - da verificare: allarmi del chiller (p. 32), note su guasti del tubo laser (p. 37), e ogni altra
     pagina che trovi con un problema e cosa fare.

   Scrivi in «Pagine annotate» quelle che scegli, e dentro quelle annota tutto.
3. **Un ramo per ogni causa numerata.** Nelle tabelle ogni sintomo ha cause numerate 1, 2, 3… e
   soluzioni con lo stesso numero. Ogni coppia causa N → soluzione N è un ramo separato, con lo
   stesso problema. Esempio: la riga «Machine does not start…» ha 9 cause, quindi 9 rami.
4. **ID.** Tutta la riga della tabella è un solo segmento (per esempio `p51.t1.r2`): usa quello per
   problema, causa, azioni e componente di quella riga.
5. **Controllo finale:** `.venv/bin/python scripts/campaign.py gold grizzly_g0872` (lo lancio io se
   preferisci). Deve dire zero errori.
6. **Il giorno dopo:** ricontrolla circa un ramo su cinque, scelto a caso, e correggi se serve.

## Regole dei campi

- **problema:** il sintomo come nel manuale; per un codice, il suo significato.
- **codice:** solo per i codici di errore (per esempio `XSlop Over`).
- **causa:** come scritta, oppure `non indicata nel manuale`. Mai dedurla dalla soluzione.
- **azione:** una riga per ogni istruzione, nell'ordine. `tipo`: `riparazione` se cambia la
  macchina (sostituire, stringere, pulire, regolare, resettare), `controllo` se osserva o verifica
  (ispezionare, controllare, misurare), `assistenza` se dice di chiamare il supporto.
  «Inspect/replace if at fault» sono due azioni: `controllo` e poi `riparazione`.
- **componente:** solo se il manuale dice che quella parte è guasta o da regolare.
- **condizioni:** «se…», «solo quando…», valori, e i rimandi come «(Page 63)».
- Un codice che ha solo il significato, senza causa e senza azione, va annotato lo stesso:
  il sistema lo misura come copertura dei codici.

## Esempio (riga `p51.t1.r2`, causa 1)

```text
### Ramo R1
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice:
- causa: Emergency stop button depressed or at fault. | ID: p51.t1.r2
- azione: Rotate emergency stop button head to reset. | tipo: riparazione | ID: p51.t1.r2
- azione: Replace emergency stop button if at fault. | tipo: riparazione | ID: p51.t1.r2
- componente: Emergency stop button | ID: p51.t1.r2
- condizioni: sostituire solo se il pulsante è guasto
- nota:
```

## Esempio (codice, p. 9)

```text
### Ramo R40
- problema: Travel exceeds the working envelope of the X-axis. | ID: p9.b43, p9.b44
- codice: XSlop Over
- causa: non indicata nel manuale | ID:
- azione:  | tipo: riparazione | ID:
- componente:  | ID:
- condizioni:
- nota:
```

Quando hai finito, dimmelo: controllo il foglio e lo congeliamo prima di qualsiasi esecuzione.
