# Annotazione del gold: Graco GTX 2000EX texture sprayer

Indicazione: la sezione diagnostica sembra alle pagine 8-9 (tabella Problem / Cause / Solution). Controlla nel PDF: se ce ne sono altre, annotale.

Annotatore: Fabio Daniele
Data: 2026-09-27
Tempo impiegato (minuti): circa 12
Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): 8-9

## Istruzioni

- Apri `manual.pdf` e trova le pagine diagnostiche (guasti, allarmi, troubleshooting).
  Scrivile sopra in «Pagine annotate»: dentro quelle pagine annota **tutti** i rami.
- Un ramo è una voce: una riga di tabella, un problema con i suoi passi, un codice.
  Copia il modello «Ramo» per ogni voce e numera R1, R2, ...
- **problema**: sintomo o significato del codice; il codice va in **codice**.
- **causa**: come scritta nel manuale, oppure `non indicata nel manuale`. Mai dedurla dal rimedio.
- **azione**: una riga per ogni rimedio o controllo, in ordine; **tipo**: `riparazione`,
  `controllo` o `assistenza`. Nessuna azione: lascia la riga vuota.
- **componente**: solo se il manuale dice che quella parte è guasta o da regolare.
- **condizioni**: "se...", "solo quando...", valori, esiti dei test.
- **ID**: dal file `TESTO.md`, separati da virgole (`p11.t1.r2, p11.t1.r3`).
- Non guardare grafi o risultati del sistema per questo manuale.
- Il giorno dopo ricontrolla circa un ramo su cinque e correggi se serve.

## Rami

### Ramo R1
- problema: No material output from pump. | ID: p8.t1.r2
- codice:
- causa: Not enough air pressure to pump. | ID: p8.t1.r2
- componente: air regulator | ID: p8.t1.r2
- azione: Shut off air at the gun. | tipo: controllo | ID: p8.t1.r2
- azione: Increase air pressure to the pump to the maximum. | tipo: riparazione | ID: p8.t1.r2
- azione: Turn the regulator clockwise to increase pressure. | tipo: riparazione | ID: p8.t1.r2
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R2
- problema: No material output from pump. | ID: p8.t1.r2
- codice:
- causa: Material too thick. | ID: p8.t1.r3
- componente:  | ID:
- azione: Thin the material. | tipo: riparazione | ID: p8.t1.r3
- azione: Mix the material thoroughly until it immediately folds back in as you draw your finger through the surface. | tipo: riparazione | ID: p8.t1.r3
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. The material should immediately fold back in as a finger is drawn through its surface.
- nota:

### Ramo R3
- problema: No material output from pump. | ID: p8.t1.r2
- codice:
- causa: Damaged checkballs or seats. | ID: p8.t1.r4
- componente: checkballs; seats | ID: p8.t1.r4
- azione: Replace the checkballs or seats. | tipo: riparazione | ID: p8.t1.r4
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R4
- problema: No material output from pump. | ID: p8.t1.r2
- codice:
- causa: Plugged gun or nozzle. | ID: p8.t1.r5
- componente: gun; nozzle | ID: p8.t1.r5
- azione: Relieve pressure using the procedure on page 6. | tipo: controllo | ID: p8.t1.r5
- azione: Remove the gun from the material hose. | tipo: controllo | ID: p8.t1.r5
- azione: Cycle the pump. | tipo: riparazione | ID: p8.t1.r5
- azione: If necessary, flush the hose and pump with clean water. | tipo: riparazione | ID: p8.t1.r5
- azione: Cycle material through the hose with the gun removed. | tipo: riparazione | ID: p8.t1.r5
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. A plugged gun or nozzle may also cause the hose and pump to plug.
- nota:

### Ramo R5
- problema: No material output from pump. | ID: p8.t1.r2
- codice:
- causa: Plugged hose, or hose too small. | ID: p8.t1.r6
- componente: hose | ID: p8.t1.r6
- azione: Relieve pressure using the procedure on page 6. | tipo: controllo | ID: p8.t1.r6
- azione: Flush the hose with clean water. | tipo: riparazione | ID: p8.t1.r6
- azione: Try a 1-1/4 in. hose. | tipo: riparazione | ID: p8.t1.r6
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R6
- problema: Pump stops pumping. | ID: p8.t1.r7
- codice:
- causa: Stalled pump. | ID: p8.t1.r7
- componente: pump | ID: p8.t1.r7, p8.t1.r8
- azione: Shut down the system. | tipo: controllo | ID: p8.t1.r7
- azione: Relieve pressure using the procedure on page 6. | tipo: controllo | ID: p8.t1.r7
- azione: Restart the system. | tipo: riparazione | ID: p8.t1.r7
- azione: Contact an authorized Graco service center. | tipo: assistenza | ID: p8.t1.r8
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R7
- problema: Pump stops pumping. | ID: p8.t1.r7
- codice:
- causa: Pump in need of repair. | ID: p8.t1.r9
- componente: pump | ID: p8.t1.r9
- azione: See texture pump instruction manual 308479. | tipo: assistenza | ID: p8.t1.r9
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R8
- problema: Pulsing or surging material. | ID: p8.t1.r10
- codice:
- causa: Triggering too fast. | ID: p8.t1.r10
- componente:  | ID:
- azione: Slowly squeeze the trigger to the fully open position. | tipo: riparazione | ID: p8.t1.r10
- azione: Move the gun quickly in a circular motion. | tipo: riparazione | ID: p8.t1.r10
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R9
- problema: Speed of application too slow. | ID: p8.t1.r11
- codice:
- causa: Not enough air pressure to pump. | ID: p8.t1.r11
- componente: air regulator | ID: p8.t1.r11
- azione: Shut off air at the gun. | tipo: controllo | ID: p8.t1.r11
- azione: Increase air pressure to the pump to the maximum. | tipo: riparazione | ID: p8.t1.r11
- azione: Turn the regulator clockwise to increase pressure. | tipo: riparazione | ID: p8.t1.r11
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R10
- problema: Speed of application too slow. | ID: p8.t1.r11
- codice:
- causa: Material too thick. | ID: p8.t1.r12
- componente:  | ID:
- azione: Thin the material. | tipo: riparazione | ID: p8.t1.r12
- azione: Mix the material thoroughly until it immediately folds back in as you draw your finger through the surface. | tipo: riparazione | ID: p8.t1.r12
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. The material should immediately fold back in as a finger is drawn through its surface.
- nota:

### Ramo R11
- problema: Speed of application too slow. | ID: p8.t1.r11
- codice:
- causa: Nozzle too small. | ID: p8.t1.r13
- componente: nozzle | ID: p8.t1.r13
- azione: Increase the nozzle size. | tipo: riparazione | ID: p8.t1.r13
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R12
- problema: Speed of application too slow. | ID: p8.t1.r11
- codice:
- causa: Hose plugged or too small. | ID: p8.t1.r14
- componente: hose | ID: p8.t1.r14
- azione: Relieve pressure using the procedure on page 6. | tipo: controllo | ID: p8.t1.r14
- azione: Clean the hose with clean water. | tipo: riparazione | ID: p8.t1.r14
- azione: Try a 1-1/4 in. hose. | tipo: riparazione | ID: p8.t1.r14
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R13
- problema: Speed of application too slow. | ID: p8.t1.r11
- codice:
- causa: Pump in need of repair. | ID: p8.t1.r15
- componente: pump | ID: p8.t1.r15
- azione: See texture pump instruction manual 308479. | tipo: assistenza | ID: p8.t1.r15
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R14
- problema: Pattern too fine or too much overspray. | ID: p9.t1.r2
- codice:
- causa: Material too thin. | ID: p9.t1.r2
- componente:  | ID:
- azione: Thicken the material. | tipo: riparazione | ID: p9.t1.r2
- azione: Mix the material thoroughly until it immediately folds back in as you draw your finger through the surface. | tipo: riparazione | ID: p9.t1.r2
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. The material should immediately fold back in as a finger is drawn through its surface.
- nota:

### Ramo R15
- problema: Pattern too fine or too much overspray. | ID: p9.t1.r2
- codice:
- causa: Air pressure at gun too high. | ID: p9.t1.r3
- componente: gun fitting; regulator | ID: p9.t1.r3
- azione: Decrease air to the gun at the gun fitting and/or regulator. | tipo: riparazione | ID: p9.t1.r3
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R16
- problema: Pattern too fine or too much overspray. | ID: p9.t1.r2
- codice:
- causa: Fluid delivery too low. | ID: p9.t1.r4
- componente: nozzle; gun fitting; regulator; fluid knob on gun | ID: p9.t1.r4, p9.t1.r5, p9.t1.r6
- azione: Increase nozzle size. | tipo: riparazione | ID: p9.t1.r4
- azione: Increase air pressure to the pump, or decrease air to the gun at the gun fitting and/or regulator. | tipo: riparazione | ID: p9.t1.r5
- azione: Turn the fluid knob out on the gun. | tipo: riparazione | ID: p9.t1.r6
- azione: See Spray Techniques in Operation Manual 309915. | tipo: controllo | ID: p9.t1.r6
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R17
- problema: Pattern too coarse. | ID: p9.t1.r7
- codice:
- causa: Material too thick. | ID: p9.t1.r7
- componente:  | ID:
- azione: Thin the material. | tipo: riparazione | ID: p9.t1.r7
- azione: Mix the material thoroughly until it immediately folds back in as you draw your finger through the surface. | tipo: riparazione | ID: p9.t1.r7
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. The material should immediately fold back in as a finger is drawn through its surface.
- nota:

### Ramo R18
- problema: Pattern too coarse. | ID: p9.t1.r7
- codice:
- causa: Air pressure at gun too low. | ID: p9.t1.r8
- componente: gun fitting; regulator | ID: p9.t1.r8
- azione: Increase air to the gun at the gun fitting and/or regulator. | tipo: riparazione | ID: p9.t1.r8
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:

### Ramo R19
- problema: Pattern too coarse. | ID: p9.t1.r7
- codice:
- causa: Fluid delivery too high. | ID: p9.t1.r9
- componente: nozzle; gun fitting; regulator; fluid knob on gun | ID: p9.t1.r9, p9.t1.r10, p9.t1.r11
- azione: Decrease nozzle size. | tipo: riparazione | ID: p9.t1.r9
- azione: Decrease air pressure to the pump, or increase air to the gun at the gun fitting and/or regulator. | tipo: riparazione | ID: p9.t1.r10
- azione: Turn the fluid knob in on the gun. | tipo: riparazione | ID: p9.t1.r11
- azione: See Spray Techniques in Operation Manual 309915. | tipo: controllo | ID: p9.t1.r11
- condizioni: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.
- nota:
