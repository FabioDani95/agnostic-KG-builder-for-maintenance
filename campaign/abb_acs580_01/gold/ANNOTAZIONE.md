# Annotazione del gold: ABB ACS580-01 variable speed drive

Indicazione: la sezione diagnostica sembra alle pagine 231-232, 365-366 (indicatori LED e fault tracing della funzione Safe torque off: sezione diagnostica breve). Controlla nel PDF: se ce ne sono altre, annotale.

Annotatore: Fabio Daniele
Data: 2026-09-27
Tempo impiegato (minuti): circa 18
Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): 231-232, 361, 365, 374-375, 380-381, 390-391, 396

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
- problema: A drive capacitor may have failed; capacitor failure is usually followed by unit damage, an input cable fuse failure, or a fault trip. | ID: p231.b4
- codice: 
- causa: non indicata nel manuale | ID:
- componente: DC-link electrolytic capacitors | ID: p231.b3
- azione: Contact ABB. | tipo: assistenza | ID: p231.b4
- condizioni: Se si sospetta il guasto di uno o più condensatori.
- nota: 

### Ramo R2
- problema: The drive LEDs are not visible while the control panel is attached. | ID: p231.t1.r1
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Switch to remote control before removing the panel, otherwise a fault will be generated. | tipo: controllo | ID: p231.t1.r1
- azione: Remove the panel to see the drive LEDs. | tipo: controllo | ID: p231.t1.r1
- condizioni: Se un control panel è collegato al drive.
- nota: 

### Ramo R3
- problema: The drive has no power. | ID: p231.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Drive LEDs off.
- nota: 

### Ramo R4
- problema: The power supply on the board is OK. | ID: p231.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Green POWER LED lit and steady.
- nota: 

### Ramo R5
- problema: The drive is in an alarm state. | ID: p231.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Green POWER LED blinking.
- nota: 

### Ramo R6
- problema: The drive is selected on the control panel when multiple drives are connected to the same panel bus. | ID: p231.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Green POWER LED blinks for one second; multiple drives share the panel bus.
- nota: 

### Ramo R7
- problema: There is an active fault in the drive. | ID: p231.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Reset the fault by pressing RESET on the control panel. | tipo: riparazione | ID: p231.t1.r4
- azione: Reset the fault by switching off the drive power. | tipo: riparazione | ID: p231.t1.r4
- condizioni: Red FAULT LED lit and steady.
- nota: 

### Ramo R8
- problema: There is an active fault in the drive. | ID: p231.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Reset the fault by switching off the drive power. | tipo: riparazione | ID: p231.t1.r4
- condizioni: Red FAULT LED blinking.
- nota: 

### Ramo R9
- problema: The control panel has no power. | ID: p232.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Control panel LED off.
- nota: 

### Ramo R10
- problema: The control panel LED is green and lit steady. | ID: p232.t1.r3
- codice: 
- causa: The connection between the drive and control panel may be faulty or lost. | ID: p232.t1.r3
- componente:  | ID:
- azione: Check the control panel display. | tipo: controllo | ID: p232.t1.r3
- condizioni: Drive is reported to function normally; green LED lit steady.
- nota: 

### Ramo R11
- problema: The control panel LED is green and lit steady. | ID: p232.t1.r3
- codice: 
- causa: The panel and drive may be incompatible. | ID: p232.t1.r3
- componente:  | ID:
- azione: Check the control panel display. | tipo: controllo | ID: p232.t1.r3
- condizioni: Drive is reported to function normally; green LED lit steady.
- nota: 

### Ramo R12
- problema: There is an active warning in the drive. | ID: p232.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Green control panel LED blinking.
- nota: 

### Ramo R13
- problema: Data is being transferred between the PC tool and drive through the control panel USB connection. | ID: p232.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Green control panel LED flickering.
- nota: 

### Ramo R14
- problema: There is an active fault in the drive. | ID: p232.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Check the display to see where the fault is. | tipo: controllo | ID: p232.t1.r4
- azione: Reset the fault. | tipo: riparazione | ID: p232.t1.r4
- condizioni: Red control panel LED lit and steady.
- nota: 

### Ramo R15
- problema: There is an active fault in another drive on the panel bus. | ID: p232.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Check the display to see where the fault is. | tipo: controllo | ID: p232.t1.r4
- azione: Switch to the drive in question. | tipo: controllo | ID: p232.t1.r4
- azione: Check the fault. | tipo: controllo | ID: p232.t1.r4
- azione: Reset the fault. | tipo: riparazione | ID: p232.t1.r4
- condizioni: Red control panel LED lit and steady.
- nota: 

### Ramo R16
- problema: There is an active fault in the drive. | ID: p232.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Cycle the drive power to reset the fault. | tipo: riparazione | ID: p232.t1.r4
- condizioni: Red control panel LED blinking.
- nota: 

### Ramo R17
- problema: The Bluetooth interface is enabled, discoverable, and ready for pairing. | ID: p232.t1.r5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Blue LED blinking; panels with a Bluetooth interface only.
- nota: 

### Ramo R18
- problema: Data is being transferred through the Bluetooth interface of the control panel. | ID: p232.t1.r5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Blue LED flickering; panels with a Bluetooth interface only.
- nota: 

### Ramo R19
- problema: The drive generates a FA81 Safe Torque Off 1 loss fault indication. | ID: p361.t1.r4
- codice: FA81 | ID: p361.t1.r4
- causa: The 1st channel of the STO circuit is opened during the failure-detection test. | ID: p361.t1.r4
- componente:  | ID:
- azione: Give a start command to verify that the STO function blocks drive operation; the motor should not start. | tipo: controllo | ID: p361.t1.r4
- azione: Close the STO circuit. | tipo: riparazione | ID: p361.t1.r4
- azione: Reset any active faults. | tipo: riparazione | ID: p361.t1.r4
- azione: Restart the drive. | tipo: riparazione | ID: p361.t1.r4
- azione: Check that the motor runs normally. | tipo: controllo | ID: p361.t1.r4
- condizioni: The motor may be stopped or running; if it is running, it should coast to a stop.
- nota: 

### Ramo R20
- problema: The drive generates a FA82 Safe Torque Off 2 loss fault indication. | ID: p361.t1.r4
- codice: FA82 | ID: p361.t1.r4
- causa: The 2nd channel of the STO circuit is opened during the failure-detection test. | ID: p361.t1.r4
- componente:  | ID:
- azione: Give a start command to verify that the STO function blocks drive operation; the motor should not start. | tipo: controllo | ID: p361.t1.r4
- azione: Close the STO circuit. | tipo: riparazione | ID: p361.t1.r4
- azione: Reset any active faults. | tipo: riparazione | ID: p361.t1.r4
- azione: Restart the drive. | tipo: riparazione | ID: p361.t1.r4
- azione: Check that the motor runs normally. | tipo: controllo | ID: p361.t1.r4
- condizioni: The motor may be stopped or running; if it is running, it should coast to a stop.
- nota: 

### Ramo R21
- problema: The drive trips on an STO hardware failure fault. | ID: p365.b4
- codice: STO hardware failure | ID: p365.b4
- causa: The two STO channels are not in the same state. | ID: p365.b4
- componente:  | ID:
- azione: See the drive control program firmware manual for generated indications and for directing fault/warning indications to a control-unit output for external diagnostics. | tipo: controllo | ID: p365.b5
- azione: Report any failure of the Safe torque off function to ABB. | tipo: assistenza | ID: p365.b6
- condizioni: 
- nota: 

### Ramo R22
- problema: The drive trips on an STO hardware failure fault. | ID: p365.b4
- codice: STO hardware failure | ID: p365.b4
- causa: The STO is used in a non-redundant manner, for example only one channel is activated. | ID: p365.b4
- componente:  | ID:
- azione: See the drive control program firmware manual for generated indications and for directing fault/warning indications to a control-unit output for external diagnostics. | tipo: controllo | ID: p365.b5
- azione: Report any failure of the Safe torque off function to ABB. | tipo: assistenza | ID: p365.b6
- condizioni: 
- nota: 

### Ramo R23
- problema: The A7AB Extension I/O configuration failure warning is shown. | ID: p374.b23
- codice: A7AB | ID: p374.b23
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Make sure that parameter 15.02 is CAIO-01. | tipo: controllo | ID: p374.b24
- azione: Set parameter 15.01 to CAIO-01. | tipo: riparazione | ID: p374.b25
- condizioni: If warning A7AB is shown during start-up.
- nota: 

### Ramo R24
- problema: The CAIO-01 adapter module is powered up. | ID: p375.t1.r2
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Diagnostic LED green.
- nota: 

### Ramo R25
- problema: The CAIO-01 diagnostic LED is red. | ID: p375.t1.r3
- codice: 
- causa: There is no communication with the drive control unit. | ID: p375.t1.r3
- componente:  | ID:
- condizioni: Diagnostic LED red.
- nota: 

### Ramo R26
- problema: The CAIO-01 diagnostic LED is red. | ID: p375.t1.r3
- codice: 
- causa: The adapter module has detected an error. | ID: p375.t1.r3
- componente:  | ID:
- condizioni: Diagnostic LED red.
- nota: 

### Ramo R27
- problema: The CBAI-01 adapter module is powered up. | ID: p381.t1.r2
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: After powering up the drive, verify that the diagnostic LED is on. | tipo: controllo | ID: p380.b42
- condizioni: Diagnostic LED green.
- nota: 

### Ramo R28
- problema: The A7AB Extension I/O configuration failure warning is shown. | ID: p391.b19
- codice: A7AB | ID: p391.b19
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Make sure that parameter 15.02 is CMOD-01. | tipo: controllo | ID: p390.b14
- azione: Set parameter 15.01 to CMOD-01. | tipo: riparazione | ID: p390.b15
- condizioni: If warning A7AB is shown during start-up.
- nota: 

### Ramo R29
- problema: The CMOD-01 extension module is powered up. | ID: p391.t3.r2
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Diagnostic LED green.
- nota: 

### Ramo R30
- problema: The A7AB Extension I/O configuration failure warning is shown. | ID: p396.b19
- codice: A7AB | ID: p396.b19
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Make sure that parameter 15.02 is CMOD-02. | tipo: controllo | ID: p396.b14
- azione: Set parameter 15.01 to CMOD-02. | tipo: riparazione | ID: p396.b15
- condizioni: If warning A7AB is shown during start-up.
- nota: 

### Ramo R31
- problema: The CMOD-02 extension module is powered up. | ID: p396.t1.r2
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Diagnostic LED green.
- nota: 
