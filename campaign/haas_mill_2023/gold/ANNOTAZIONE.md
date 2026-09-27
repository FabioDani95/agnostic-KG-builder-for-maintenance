# Annotazione del gold: Haas vertical mill (2023 operator's manual)

Indicazione: la sezione diagnostica sembra alle pagine 141-146 (guida alle icone di controllo: icona di allarme o avviso, significato, azione). Controlla nel PDF: se ce ne sono altre, annotale.

Annotatore: Fabio Daniele
Data: 2026-09-27
Tempo impiegato (minuti): circa 24
Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): 32, 86, 141-146, 160

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
- problema: The beacon light is flashing red. | ID: p32.t2.r5
- codice: 
- causa: A fault has occurred. | ID: p32.t2.r5
- componente:  | ID:
- condizioni: Flashing red beacon light.
- nota: 

### Ramo R2
- problema: The beacon light is flashing red. | ID: p32.t2.r5
- codice: 
- causa: The machine is in Emergency Stop. | ID: p32.t2.r5
- componente:  | ID:
- condizioni: Flashing red beacon light.
- nota: 

### Ramo R3
- problema: The umbrella tool changer is jammed. | ID: p86.b3
- codice: 
- causa: non indicata nel manuale | ID:
- componente: umbrella tool changer | ID: p86.b3
- azione: Remove the cause of the jam. | tipo: riparazione | ID: p86.b5
- azione: Press RESET to clear the alarms. | tipo: riparazione | ID: p86.b6
- azione: Press RECOVER and follow the directions to reset the tool changer. | tipo: riparazione | ID: p86.b7
- condizioni: Do not put hands near the tool changer unless an alarm is displayed first.
- nota: 

### Ramo R4
- problema: Check that the tool probe operates correctly. | ID: p160.b5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: In MDI mode, run M59 P2; G04 P1.0; M59 P3. | tipo: controllo | ID: p160.b6, p160.b8, p160.b10, p160.b12
- azione: Touch the tool-probe stylus. | tipo: controllo | ID: p160.b7
- azione: Press RESET to deactivate the probe. | tipo: controllo | ID: p160.b18
- condizioni: The probe LED flashes green after activation; touching the stylus produces a beep and red LED; RESET turns the probe LED off.
- nota: 

### Ramo R5
- problema: Check that the work probe operates correctly. | ID: p160.b24
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Select the work probe with a tool change, or manually insert it into the spindle. | tipo: controllo | ID: p160.b25
- azione: In MDI mode, run M69 P2 to start communication with the work probe. | tipo: controllo | ID: p160.b29
- azione: In MDI mode, run M59 P3. | tipo: controllo | ID: p160.b32
- azione: Touch the work-probe stylus. | tipo: controllo | ID: p160.b26
- azione: Press RESET to deactivate the probe. | tipo: controllo | ID: p160.b31
- condizioni: The probe LED flashes green after activation; touching the stylus produces a beep and red LED; RESET turns the work-probe LED off.
- nota: 

### Ramo R6
- problema: The door has not yet been cycled after power-up, so the door sensor has not been confirmed to work. | ID: p141.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Cycle the door at least once. | tipo: controllo | ID: p141.t1.r3
- condizioni: The Cycle Door icon appears after [POWER UP] if the user has not yet cycled the door.
- nota: 

### Ramo R7
- problema: The door is open. | ID: p141.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Door Open warning icon.
- nota: 

### Ramo R8
- problema: The pallet load station is open. | ID: p141.t1.r5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R9
- problema: The light curtain is triggered. | ID: p141.t1.r6
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Remove the obstacle from the light-curtain line of sight. | tipo: controllo | ID: p141.t1.r6
- condizioni: The icon appears when the machine is idle or a program is running and the light curtain is triggered.
- nota: 

### Ramo R10
- problema: The Light Curtain Hold icon appears while the light curtain is triggered during a running program. | ID: p141.t1.r7
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Press [CYCLE START] to clear the icon. | tipo: controllo | ID: p141.t1.r7
- condizioni: Program is running.
- nota: 

### Ramo R11
- problema: Low gearbox oil flow has persisted for one minute. | ID: p142.t2.r1
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: Low gearbox oil flow persists for 1 minute.
- nota: 

### Ramo R12
- problema: The control detected a low gearbox oil level. | ID: p142.t2.r2
- codice: 
- causa: The control detected a low gearbox oil level. | ID: p142.t2.r2
- componente:  | ID:
- azione: Press [RESET] to clear the low gearbox oil icon. | tipo: riparazione | ID: p142.t2.r2
- condizioni: In software version 100.19.000.1100 and higher, monitoring occurs when the spindle fan is off, after a delay.
- nota: 

### Ramo R13
- problema: The rotary table lubrication reservoir requires checking and filling. | ID: p142.t2.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Check the rotary-table lubrication oil reservoir. | tipo: controllo | ID: p142.t2.r3
- azione: Fill the reservoir. | tipo: riparazione | ID: p142.t2.r3
- condizioni: 
- nota: 

### Ramo R14
- problema: The Through-Spindle Coolant or High-Pressure Flood Coolant filter is dirty. | ID: p142.t2.r4
- codice: 
- causa: The TSC/HPFC filter is dirty. | ID: p142.t2.r4
- componente: TSC/HPFC filter | ID: p142.t2.r4
- azione: Clean the filter. | tipo: riparazione | ID: p142.t2.r4
- condizioni: 
- nota: 

### Ramo R15
- problema: The coolant concentrate level is low. | ID: p142.t2.r5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Fill the concentrate reservoir for the coolant refill system. | tipo: riparazione | ID: p142.t2.r5
- condizioni: 
- nota: 

### Ramo R16
- problema: The system detects a low-oil condition in the PulseJet reservoir. | ID: p142.t2.r6
- codice: 
- causa: The PulseJet oil reservoir has a low-oil condition. | ID: p142.t2.r6
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R17
- problema: The Low Lube icon appears. | ID: p142.t2.r7
- codice: 
- causa: The spindle lubrication oil system detected a low-oil condition. | ID: p142.t2.r7
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R18
- problema: The Low Lube icon appears. | ID: p142.t2.r7
- codice: 
- causa: The axis ball-screw lubrication system detected low grease or low pressure. | ID: p142.t2.r7
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R19
- problema: The rotary brake oil level is low. | ID: p143.t1.r1
- codice: 
- causa: The rotary brake oil level is low. | ID: p143.t1.r1
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R20
- problema: Residual pressure is detected before a lubrication cycle. | ID: p143.t1.r2
- codice: 
- causa: An obstruction in the axes grease lubrication system can cause the residual pressure. | ID: p143.t1.r2
- componente:  | ID:
- condizioni: Detected by the grease pressure sensor before a lubrication cycle.
- nota: 

### Ramo R21
- problema: The mist extractor filter needs cleaning. | ID: p143.t1.r3
- codice: 
- causa: non indicata nel manuale | ID:
- componente: mist extractor filter | ID: p143.t1.r3
- azione: Clean the mist extractor filter. | tipo: riparazione | ID: p143.t1.r3
- condizioni: 
- nota: 

### Ramo R22
- problema: The coolant level is low. | ID: p143.t1.r5
- codice: 
- causa: Coolant level is low. | ID: p143.t1.r5
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R23
- problema: The PulseJet oil level is low. | ID: p143.t1.r6
- codice: 
- causa: PulseJet oil level is low. | ID: p143.t1.r6
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R24
- problema: Air flow is not sufficient for correct machine operation. | ID: p143.t1.r8
- codice: 
- causa: Air flow is not sufficient for correct machine operation. | ID: p143.t1.r8, p143.t2.r1
- componente:  | ID:
- condizioni: The icon applies in Inch Mode and Metric Mode.
- nota: 

### Ramo R25
- problema: The HPU oil level is low. | ID: p144.t1.r1
- codice: 
- causa: The HPU oil level is low. | ID: p144.t1.r1
- componente:  | ID:
- azione: Check the oil level. | tipo: controllo | ID: p144.t1.r1
- azione: Add the recommended oil for the machine. | tipo: riparazione | ID: p144.t1.r1
- condizioni: 
- nota: 

### Ramo R26
- problema: The HPU oil temperature is too high for reliable operation. | ID: p144.t1.r2
- codice: 
- causa: The oil temperature is too high to reliably operate the HPU. | ID: p144.t1.r2
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R27
- problema: The spindle fan has failed. | ID: p144.t1.r3
- codice: 
- causa: The spindle fan has stopped operating. | ID: p144.t1.r3
- componente: spindle fan | ID: p144.t1.r3
- condizioni: 
- nota: 

### Ramo R28
- problema: Cabinet temperatures are approaching levels that may be dangerous to the electronics (Electronics Overheat warning). | ID: p144.t1.r4
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- azione: Inspect the cabinet for clogged air filters and correctly operating fans. | tipo: controllo | ID: p144.t1.r4
- condizioni: If temperature reaches or exceeds the recommended level, alarm 253 ELECTRONICS OVERHEAT is generated.
- nota: 

### Ramo R29
- problema: The electronics remain in the overheat state too long; the machine will not operate until corrected. | ID: p144.t1.r5
- codice: 253 ELECTRONICS OVERHEAT | ID: p144.t1.r4
- causa: The electronics remain in the overheat state too long. | ID: p144.t1.r5
- componente:  | ID:
- azione: Inspect the cabinet for clogged air filters and correctly operating fans. | tipo: controllo | ID: p144.t1.r5
- condizioni: 
- nota: 

### Ramo R30
- problema: The transformer is overheated for more than one second (Transformer Overheat warning). | ID: p144.t1.r6
- codice: 
- causa: The transformer is detected to be overheated for more than 1 second. | ID: p144.t1.r6
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R31
- problema: The transformer remains overheated too long; the machine will not operate until corrected. | ID: p144.t2.r1
- codice: 
- causa: The transformer remains in the overheat state for too long. | ID: p144.t2.r1
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R32
- problema: Incoming voltage is low (Low Voltage warning). | ID: p144.t2.r2
- codice: 
- causa: The PFDM detects low incoming voltage. | ID: p144.t2.r2
- componente:  | ID:
- condizioni: If the condition continues, the machine cannot continue to operate.
- nota: 

### Ramo R33
- problema: Incoming voltage is too low to operate (Low Voltage alarm). | ID: p144.t2.r3
- codice: 
- causa: The PFDM detects incoming voltage that is too low to operate. | ID: p144.t2.r3
- componente:  | ID:
- condizioni: The machine will not operate until the condition is corrected.
- nota: 

### Ramo R34
- problema: Incoming voltage is above the set limit but remains within operating parameters (High Voltage warning). | ID: p144.t2.r4
- codice: 
- causa: The PFDM detects incoming voltage above a set limit but within operating parameters. | ID: p144.t2.r4
- componente:  | ID:
- azione: Correct the condition to prevent damage to machine components. | tipo: riparazione | ID: p144.t2.r4
- condizioni: 
- nota: 

### Ramo R35
- problema: Incoming voltage is too high to operate and could damage the machine (High Voltage alarm). | ID: p144.t2.r5
- codice: 
- causa: The PFDM detects incoming voltage that is too high to operate. | ID: p144.t2.r5
- componente:  | ID:
- condizioni: The machine will not operate until the condition is corrected.
- nota: 

### Ramo R36
- problema: A Surge Protector fault has been detected. | ID: p144.t2.r6
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: The icon remains active until the fault is cleared. Continuing to use the machine in this state could allow an electrical surge to damage the electronics.
- nota: 

### Ramo R37
- problema: The robot battery is low. | ID: p144.t2.r7
- codice: 
- causa: The pulse-coder batteries are low. | ID: p144.t2.r7
- componente: pulse-coder batteries | ID: p144.t2.r7
- azione: Replace the pulse-coder batteries as soon as possible. | tipo: riparazione | ID: p144.t2.r7
- azione: Do not turn off the robot. | tipo: controllo | ID: p144.t2.r7
- condizioni: If the robot is turned off, it may require remastering.
- nota: The manual refers to service documentation 9156.062, ROBOT COMMAND FAILED, SRVO-062 BZAL.

### Ramo R38
- problema: Air pressure to the machine is too low to reliably operate pneumatic systems (Low Air warning). | ID: p145.t1.r1
- codice: 
- causa: Air pressure to the machine is too low to reliably operate pneumatic systems. | ID: p145.t1.r1
- componente:  | ID:
- azione: Correct the condition to prevent damage to or incorrect operation of pneumatic systems. | tipo: riparazione | ID: p145.t1.r1
- condizioni: 
- nota: 

### Ramo R39
- problema: Air pressure is too low to operate pneumatic systems (Low Air alarm). | ID: p145.t1.r2
- codice: 
- causa: Air pressure to the machine is too low to operate pneumatic systems. | ID: p145.t1.r2
- componente:  | ID:
- azione: A higher-capacity air compressor may be needed. | tipo: riparazione | ID: p145.t1.r2
- condizioni: The machine will not operate until corrected.
- nota: 

### Ramo R40
- problema: Air pressure to the machine is too high to reliably operate pneumatic systems (High Air warning). | ID: p145.t1.r3
- codice: 
- causa: Air pressure to the machine is too high to reliably operate pneumatic systems. | ID: p145.t1.r3
- componente:  | ID:
- azione: Correct the condition to prevent damage to or incorrect operation of pneumatic systems. | tipo: riparazione | ID: p145.t1.r3
- azione: Install a regulator at the machine air input if needed. | tipo: riparazione | ID: p145.t1.r3
- condizioni: 
- nota: 

### Ramo R41
- problema: Air pressure is too high to operate pneumatic systems (High Air alarm). | ID: p145.t1.r4
- codice: 
- causa: Air pressure to the machine is too high to operate pneumatic systems. | ID: p145.t1.r4
- componente:  | ID:
- azione: Install a regulator at the machine air input if needed. | tipo: riparazione | ID: p145.t1.r4
- condizioni: The machine will not operate until corrected.
- nota: 

### Ramo R42
- problema: The Emergency Stop on the pendant has been pressed. | ID: p145.t1.r5
- codice: 
- causa: The Emergency Stop on the pendant has been pressed. | ID: p145.t1.r5
- componente:  | ID:
- azione: Release the Emergency Stop on the pendant to clear the icon. | tipo: controllo | ID: p145.t1.r5
- condizioni: 
- nota: 

### Ramo R43
- problema: The Emergency Stop on the pallet changer has been pressed. | ID: p145.t1.r6
- codice: 
- causa: The Emergency Stop on the pallet changer has been pressed. | ID: p145.t1.r6
- componente:  | ID:
- azione: Release the Emergency Stop on the pallet changer to clear the icon. | tipo: controllo | ID: p145.t1.r6
- condizioni: 
- nota: 

### Ramo R44
- problema: The Emergency Stop on the tool changer cage has been pressed. | ID: p145.t1.r7
- codice: 
- causa: The Emergency Stop on the tool changer cage has been pressed. | ID: p145.t1.r7
- componente:  | ID:
- azione: Release the Emergency Stop on the tool changer cage to clear the icon. | tipo: controllo | ID: p145.t1.r7
- condizioni: 
- nota: 

### Ramo R45
- problema: The Emergency Stop on the auxiliary device has been pressed. | ID: p145.t2.r1
- codice: 
- causa: The Emergency Stop on the auxiliary device has been pressed. | ID: p145.t2.r1
- componente:  | ID:
- azione: Release the Emergency Stop on the auxiliary device to clear the icon. | tipo: controllo | ID: p145.t2.r1
- condizioni: 
- nota: 

### Ramo R46
- problema: The Emergency Stop on the RJH-XL has been pressed. | ID: p145.t2.r2
- codice: 
- causa: The Emergency Stop on the RJH-XL has been pressed. | ID: p145.t2.r2
- componente:  | ID:
- azione: Release the Emergency Stop on the RJH-XL to clear the icon. | tipo: controllo | ID: p145.t2.r2
- condizioni: 
- nota: 

### Ramo R47
- problema: Tool life remaining is below Setting 240, or the current tool is the last one in its tool group. | ID: p145.t2.r4
- codice: 
- causa: Tool life remaining is below Setting 240 or the current tool is the last one in its tool group. | ID: p145.t2.r4
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R48
- problema: The tool or tool group has expired and no replacement tools are available. | ID: p145.t2.r5
- codice: 
- causa: The tool or tool group has expired, and no replacement tools are available. | ID: p145.t2.r5
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R49
- problema: The side-mount tool-changer door is open. | ID: p146.t1.r1
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: 
- nota: 

### Ramo R50
- problema: The tool in the spindle is unclamped. | ID: p146.t1.r6
- codice: 
- causa: The tool in the spindle is unclamped. | ID: p146.t1.r6
- componente: tool in spindle | ID: p146.t1.r6
- condizioni: 
- nota: 

### Ramo R51
- problema: The optional High Intensity Lighting is on while the doors are open. | ID: p146.t2.r5
- codice: 
- causa: non indicata nel manuale | ID:
- componente:  | ID:
- condizioni: The optional HIL is turned on and the doors are open; duration is determined by Setting 238.
- nota: 
