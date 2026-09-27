# Annotazione del gold: Trane Series R RTAC air-cooled chiller

Indicazione: sezione diagnostica verificata nel PDF alle pagine 105-123: tabelle 66-68 e tabella 69 dei messaggi di avvio e diagnostica. Il PDF passa alla sezione Unit Wiring a p. 124.

Annotatore: Fabio Daniele
Data: 2026-09-27
Tempo impiegato (minuti): circa 55
Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): 105-123

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
- problema: Motor Current Overload - Compressor 1A | ID: p105.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Compressor current exceeded overload time versus trip characteristic. For A/C products: must trip 140% RLA, must hold 125%, nominal trip 132.5% in 30 seconds. | ID: p105.b16
- nota:

### Ramo R2
- problema: Motor Current Overload - Compressor 1B | ID: p105.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Compressor current exceeded overload time versus trip characteristic. For A/C products: must trip 140% RLA, must hold 125%, nominal trip 132.5% in 30 seconds. | ID: p105.b18
- nota:

### Ramo R3
- problema: Motor Current Overload - Compressor 2A | ID: p105.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Compressor current exceeded overload time versus trip characteristic. For A/C products: must trip 140% RLA, must hold 125%, nominal trip 132.5% in 30 seconds. | ID: p105.b20
- nota:

### Ramo R4
- problema: Motor Current Overload - Compressor 2B | ID: p105.b21
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Compressor current exceeded overload time versus trip characteristic. For A/C products: must trip 140% RLA, must hold 125%, nominal trip 132.5% in 30 seconds. | ID: p105.b22
- nota:

### Ramo R5
- problema: Over Voltage | ID: p105.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Nominal trip: 60 seconds at greater than 112.5%; at 200 V, 2.5%; at 575 V, 1.8%. Automatic reset at 109% or less. Applies in pre-start and when any circuit is energized. | ID: p105.b23, p105.b24
- nota:

### Ramo R6
- problema: Phase Loss - Compressor 1A | ID: p105.b27
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: No current was sensed on one or two current-transformer inputs while running or starting. Must hold 20% RLA; must trip 5% RLA; design trip point 10%, design trip time 2.64 seconds, maximum 3 seconds. If phase-reversal protection is enabled and current is not sensed on one or more inputs, trip within 0.3 second of compressor start. | ID: p105.b25
- nota:

### Ramo R7
- problema: Phase Loss - Compressor 1B | ID: p106.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: No current was sensed on one or two current-transformer inputs while running or starting. Must hold 20% RLA; must trip 5% RLA; design trip point 10%, design trip time 2.64 seconds, maximum 3 seconds. If phase-reversal protection is enabled and current is not sensed on one or more inputs, trip within 0.3 second of compressor start. | ID: p106.b9
- nota:

### Ramo R8
- problema: Phase Loss - Compressor 2A | ID: p106.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: No current was sensed on one or two current-transformer inputs while running or starting. Must hold 20% RLA; must trip 5% RLA; design trip point 10%, design trip time 2.64 seconds, maximum 3 seconds. If phase-reversal protection is enabled and current is not sensed on one or more inputs, trip within 0.3 second of compressor start. | ID: p106.b13
- nota:

### Ramo R9
- problema: Phase Loss - Compressor 2B | ID: p106.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: No current was sensed on one or two current-transformer inputs while running or starting. Must hold 20% RLA; must trip 5% RLA; design trip point 10%, design trip time 2.64 seconds, maximum 3 seconds. If phase-reversal protection is enabled and current is not sensed on one or more inputs, trip within 0.3 second of compressor start. | ID: p106.b13
- nota:

### Ramo R10
- problema: Phase Reversal - Compressor 1A | ID: p106.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A phase reversal was detected on the incoming current. On compressor startup, detection and trip occur within a maximum of 0.3 second. | ID: p106.b18
- nota:

### Ramo R11
- problema: Phase Reversal - Compressor 1B | ID: p106.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A phase reversal was detected on the incoming current. On compressor startup, detection and trip occur within a maximum of 0.3 second. | ID: p106.b21
- nota:

### Ramo R12
- problema: Phase Reversal - Compressor 2A | ID: p106.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A phase reversal was detected on the incoming current. On compressor startup, detection and trip occur within a maximum of 0.3 second. | ID: p106.b24
- nota:

### Ramo R13
- problema: Phase Reversal - Compressor 2B | ID: p106.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A phase reversal was detected on the incoming current. On compressor startup, detection and trip occur within a maximum of 0.3 second. | ID: p106.b27
- nota:

### Ramo R14
- problema: Power Loss - Compressor 1A | ID: p106.b31
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The compressor had established currents while running, then all three phases of current were lost. Design: below 10% RLA, trip in 2.64 seconds. Inactive before transition-complete input is proven during start; a power loss during that period results instead in Starter Fault Type III or Starter Did Not Transition. | ID: p106.b29.1, p106.b29.2
- nota:

### Ramo R15
- problema: Power Loss - Compressor 1B | ID: p107.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The compressor had established currents while running, then all three phases of current were lost. Design: below 10% RLA, trip in 2.64 seconds. The diagnostic precludes Phase Loss and Transition Complete Input Opened; the minimum trip time must exceed the Starter module reset time. | ID: p107.b6
- nota:

### Ramo R16
- problema: Power Loss - Compressor 2A | ID: p107.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The compressor had established currents while running, then all three phases of current were lost. Design: below 10% RLA, trip in 2.64 seconds. The diagnostic precludes Phase Loss and Transition Complete Input Opened; the minimum trip time must exceed the Starter module reset time. | ID: p107.b10
- nota:

### Ramo R17
- problema: Power Loss - Compressor 2B | ID: p107.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The compressor had established currents while running, then all three phases of current were lost. Design: below 10% RLA, trip in 2.64 seconds. The diagnostic precludes Phase Loss and Transition Complete Input Opened; the minimum trip time must exceed the Starter module reset time. | ID: p107.b14
- nota:

### Ramo R18
- problema: Severe Current Imbalance - Compressor 1A | ID: p107.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A 30% current imbalance was detected on one phase relative to the average of all three phases for 90 continuous seconds. | ID: p107.b17
- nota:

### Ramo R19
- problema: Severe Current Imbalance - Compressor 1B | ID: p107.b18
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A 30% current imbalance was detected on one phase relative to the average of all three phases for 90 continuous seconds. | ID: p107.b18
- nota:

### Ramo R20
- problema: Severe Current Imbalance - Compressor 2A | ID: p107.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A 30% current imbalance was detected on one phase relative to the average of all three phases for 90 continuous seconds. | ID: p107.b19
- nota:

### Ramo R21
- problema: Severe Current Imbalance - Compressor 2B | ID: p107.b20
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A 30% current imbalance was detected on one phase relative to the average of all three phases for 90 continuous seconds. | ID: p107.b20
- nota:

### Ramo R22
- problema: Starter 1A Dry Run | ID: p107.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While in Starter Dry Run mode, either 50% line voltage was sensed at the potential transformers or 10% RLA current was sensed at the current transformers. | ID: p107.b23
- nota:

### Ramo R23
- problema: Starter 1B Dry Run | ID: p107.b24
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While in Starter Dry Run mode, either 50% line voltage was sensed at the potential transformers or 10% RLA current was sensed at the current transformers. | ID: p107.b25
- nota:

### Ramo R24
- problema: Starter 2A Dry Run | ID: p107.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While in Starter Dry Run mode, either 50% line voltage was sensed at the potential transformers or 10% RLA current was sensed at the current transformers. | ID: p107.b27
- nota:

### Ramo R25
- problema: Starter 2B Dry Run | ID: p107.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While in Starter Dry Run mode, either 50% line voltage was sensed at the potential transformers or 10% RLA current was sensed at the current transformers. | ID: p107.b27
- nota:

### Ramo R26
- problema: Starter Contactor Interrupt Failure - Compressor 2A | ID: p107.b31
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente: Starter contactor | ID: p107.b31
- condizioni: Compressor current greater than 10% RLA on any or all phases while the compressor was commanded off; detection time 5-10 seconds. The controller generates the diagnostic and keeps the affected compressor off until manually reset. | ID: p107.b29
- nota:

### Ramo R27
- problema: Starter Contactor Interrupt Failure - Compressor 1A | ID: p108.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente: Starter contactor | ID: p108.b7
- condizioni: Compressor current greater than 10% RLA on any or all phases while the compressor was commanded off; detection time 5-10 seconds. The controller generates the diagnostic and keeps the affected compressor off until manually reset. | ID: p108.b9
- nota:

### Ramo R28
- problema: Starter Contactor Interrupt Failure - Compressor 1B | ID: p108.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente: Starter contactor | ID: p108.b11
- condizioni: Compressor current greater than 10% RLA on any or all phases while the compressor was commanded off; detection time 5-10 seconds. The controller generates the diagnostic and keeps the affected compressor off until manually reset. | ID: p108.b13
- nota:

### Ramo R29
- problema: Starter Contactor Interrupt Failure - Compressor 2B | ID: p108.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente: Starter contactor | ID: p108.b15
- condizioni: Compressor current greater than 10% RLA on any or all phases while the compressor was commanded off; detection time 5-10 seconds. The controller generates the diagnostic and keeps the affected compressor off until manually reset. | ID: p108.b13
- nota:

### Ramo R30
- problema: Starter Did Not Transition - Compressor 1A | ID: p108.b18
- codice: 
- causa: The Starter Module did not receive a transition-complete signal within the designated time after its transition command. | ID: p108.b17
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Must-hold time 1 second; must-trip time 6 seconds; design time 2.5 seconds. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. | ID: p108.b17
- nota:

### Ramo R31
- problema: Starter Did Not Transition - Compressor 1B | ID: p108.b21
- codice: 
- causa: The Starter Module did not receive a transition-complete signal within the designated time after its transition command. | ID: p108.b20
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Must-hold time 1 second; must-trip time 6 seconds; design time 2.5 seconds. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. | ID: p108.b20
- nota:

### Ramo R32
- problema: Starter Did Not Transition - Compressor 2A | ID: p108.b24
- codice: 
- causa: The Starter Module did not receive a transition-complete signal within the designated time after its transition command. | ID: p108.b23
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Must-hold time 1 second; must-trip time 6 seconds; design time 2.5 seconds. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. | ID: p108.b23
- nota:

### Ramo R33
- problema: Starter Did Not Transition - Compressor 2B | ID: p108.b27
- codice: 
- causa: The Starter Module did not receive a transition-complete signal within the designated time after its transition command. | ID: p108.b26
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Must-hold time 1 second; must-trip time 6 seconds; design time 2.5 seconds. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. | ID: p108.b26
- nota:

### Ramo R34
- problema: Starter Fault Type I - Compressor 1A | ID: p108.b30
- codice: 
- causa: If current is detected when only 1M (1K1) is closed first at start, one of the other contactors is shorted. | ID: p108.b29
- azione: Check for current detected by the CTs when only 1M (1K1) is closed first at start. | tipo: controllo | ID: p108.b29
- componente: One of the other contactors | ID: p108.b29
- condizioni: The specific starter test applies only to Y-Delta starters. It checks for no current when 1M (1K1) is closed first. | ID: p108.b29
- nota:

### Ramo R35
- problema: Starter Fault Type I - Compressor 1B | ID: p108.b33
- codice: 
- causa: If current is detected when only 1M (1K1) is closed first at start, one of the other contactors is shorted. | ID: p108.b32
- azione: Check for current detected by the CTs when only 1M (1K1) is closed first at start. | tipo: controllo | ID: p108.b32
- componente: One of the other contactors | ID: p108.b32
- condizioni: The specific starter test applies only to Y-Delta starters. It checks for no current when 1M (1K1) is closed first. | ID: p108.b32
- nota:

### Ramo R36
- problema: Starter Fault Type I - Compressor 2A | ID: p108.b36
- codice: 
- causa: If current is detected when only 1M (1K1) is closed first at start, one of the other contactors is shorted. | ID: p108.b35
- azione: Check for current detected by the CTs when only 1M (1K1) is closed first at start. | tipo: controllo | ID: p108.b35
- componente: One of the other contactors | ID: p108.b35
- condizioni: The specific starter test applies only to Y-Delta starters. It checks for no current when 1M (1K1) is closed first. | ID: p108.b35
- nota:

### Ramo R37
- problema: Starter Fault Type I - Compressor 2B | ID: p109.b6
- codice: 
- causa: If current is detected when only 1M (1K1) is closed first at start, one of the other contactors is shorted. | ID: p109.b5
- azione: Check for current detected by the CTs when only 1M (1K1) is closed first at start. | tipo: controllo | ID: p109.b5
- componente: One of the other contactors | ID: p109.b5
- condizioni: The specific starter test applies only to Y-Delta starters. It checks for no current when 1M (1K1) is closed first. | ID: p109.b5
- nota:

### Ramo R38
- problema: Starter Fault Type II - Compressor 1A | ID: p109.b9
- codice: 
- causa: If current is detected when only the Shorting Contactor (1K3) is energized at start, 1M is shorted. | ID: p109.b8
- azione: Check for current detected by the CTs when only the Shorting Contactor (1K3) is individually energized. | tipo: controllo | ID: p109.b8
- componente: Main Contactor 1M | ID: p109.b8
- condizioni: The test applies to all starter types; many starters do not connect to the Shorting Contactor. | ID: p109.b8
- nota:

### Ramo R39
- problema: Starter Fault Type II - Compressor 1B | ID: p109.b12
- codice: 
- causa: If current is detected when only the Shorting Contactor (1K3) is energized at start, 1M is shorted. | ID: p109.b11
- azione: Check for current detected by the CTs when only the Shorting Contactor (1K3) is individually energized. | tipo: controllo | ID: p109.b11
- componente: Main Contactor 1M | ID: p109.b11
- condizioni: The test applies to all starter types; many starters do not connect to the Shorting Contactor. | ID: p109.b11
- nota:

### Ramo R40
- problema: Starter Fault Type II - Compressor 2A | ID: p109.b15
- codice: 
- causa: If current is detected when only the Shorting Contactor (1K3) is energized at start, 1M is shorted. | ID: p109.b14
- azione: Check for current detected by the CTs when only the Shorting Contactor (1K3) is individually energized. | tipo: controllo | ID: p109.b14
- componente: Main Contactor 1M | ID: p109.b14
- condizioni: The test applies to all starter types; many starters do not connect to the Shorting Contactor. | ID: p109.b14
- nota:

### Ramo R41
- problema: Starter Fault Type II - Compressor 2B | ID: p109.b18
- codice: 
- causa: If current is detected when only the Shorting Contactor (1K3) is energized at start, 1M is shorted. | ID: p109.b17
- azione: Check for current detected by the CTs when only the Shorting Contactor (1K3) is individually energized. | tipo: controllo | ID: p109.b17
- componente: Main Contactor 1M | ID: p109.b17
- condizioni: The test applies to all starter types; many starters do not connect to the Shorting Contactor. | ID: p109.b17
- nota:

### Ramo R42
- problema: Starter Fault Type III - Compressor 1A | ID: p109.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: During the normal start sequence, the Shorting Contactor (1K3) and then Main Contactor (1K1) were energized; 1.6 seconds later no current was detected by the CTs for the last 1.2 seconds on all three phases. Applies to all starter types except Adaptive Frequency Drives. | ID: p109.b24
- nota:

### Ramo R43
- problema: Starter Fault Type III - Compressor 1B | ID: p109.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: During the normal start sequence, the Shorting Contactor (1K3) and then Main Contactor (1K1) were energized; 1.6 seconds later no current was detected by the CTs for the last 1.2 seconds on all three phases. Applies to all starter types except Adaptive Frequency Drives. | ID: p109.b28
- nota:

### Ramo R44
- problema: Starter Fault Type III - Compressor 2A | ID: p109.b30
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: During the normal start sequence, the Shorting Contactor (1K3) and then Main Contactor (1K1) were energized; 1.6 seconds later no current was detected by the CTs for the last 1.2 seconds on all three phases. Applies to all starter types except Adaptive Frequency Drives. | ID: p109.b32
- nota:

### Ramo R45
- problema: Starter Fault Type III - Compressor 2B | ID: p109.b34
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: During the normal start sequence, the Shorting Contactor (1K3) and then Main Contactor (1K1) were energized; 1.6 seconds later no current was detected by the CTs for the last 1.2 seconds on all three phases. Applies to all starter types except Adaptive Frequency Drives. | ID: p109.b32
- nota:

### Ramo R46
- problema: Transition Complete Input Opened - Compressor 1A | ID: p109.b37
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input opened while the compressor motor was running after a successful transition. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. The minimum trip time must exceed the Power Loss diagnostic trip time. | ID: p109.b36
- nota:

### Ramo R47
- problema: Transition Complete Input Opened - Compressor 1B | ID: p109.b40
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input opened while the compressor motor was running after a successful transition. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. The minimum trip time must exceed the Power Loss diagnostic trip time. | ID: p109.b39
- nota:

### Ramo R48
- problema: Transition Complete Input Opened - Compressor 2A | ID: p110.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input opened while the compressor motor was running after a successful transition. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. The minimum trip time must exceed the Power Loss diagnostic trip time. | ID: p110.b5
- nota:

### Ramo R49
- problema: Transition Complete Input Opened - Compressor 2B | ID: p110.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input opened while the compressor motor was running after a successful transition. Active only for Y-Delta, Auto-Transformer, Primary Reactor, and X-Line starters. The minimum trip time must exceed the Power Loss diagnostic trip time. | ID: p110.b8
- nota:

### Ramo R50
- problema: Transition Complete Input Shorted - Compressor 1A | ID: p110.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input was found shorted before the compressor started. Active for all electromechanical starters. | ID: p110.b11
- nota:

### Ramo R51
- problema: Transition Complete Input Shorted - Compressor 1B | ID: p110.b12
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input was found shorted before the compressor started. Active for all electromechanical starters. | ID: p110.b12
- nota:

### Ramo R52
- problema: Transition Complete Input Shorted - Compressor 2A | ID: p110.b13
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input was found shorted before the compressor started. Active for all electromechanical starters. | ID: p110.b13
- nota:

### Ramo R53
- problema: Transition Complete Input Shorted - Compressor 2B | ID: p110.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The Transition Complete input was found shorted before the compressor started. Active for all electromechanical starters. | ID: p110.b14
- nota:

### Ramo R54
- problema: Under Voltage | ID: p110.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Nominal trip: 60 seconds below 87.5%; 2.8% at 200 V and 1.8% at 575 V. Automatic reset at 90% or greater. Applies in pre-start and when any circuit is energized. | ID: p110.b15, p110.b16
- nota:

### Ramo R55
- problema: BAS Communication Lost | ID: p110.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The BAS was configured as installed; communication with the BAS was lost for 15 contiguous minutes after it had been established. The chiller follows the Tracer Default Run Command previously stored by the MP. | ID: p110.b21
- nota:

### Ramo R56
- problema: BAS Failed to Establish Communication | ID: p110.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: BAS configured as installed but did not communicate with the MP within 15 minutes after power-up. | ID: p110.b24
- nota:

### Ramo R57
- problema: Check Clock | ID: p110.b28
- codice: 
- causa: The real-time clock detected loss of its oscillator at some time in the past. | ID: p110.b27
- azione: Check or replace the battery. | tipo: controllo | ID: p110.b27
- azione: Write a new value to the chiller's time clock using TechView or DynaView's Set Chiller Time function. | tipo: riparazione | ID: p110.b27
- componente: Battery | ID: p110.b27
- condizioni: The diagnostic can be effectively cleared only by writing a new time-clock value. | ID: p110.b27
- nota:

### Ramo R58
- problema: Condenser Fan Variable Speed Drive Fault - Circuit 1 (Drive 1) | ID: p110.b31
- codice: 
- causa: The MP received a fault signal from the respective condenser fan Variable Speed Inverter Drive and failed to clear it after five attempts. | ID: p110.b30
- azione: If the fault does not clear, manually bypass the inverter and rebind the fan outputs for full fixed-speed fan operation. | tipo: riparazione | ID: p110.b30
- componente: Condenser fan variable-speed inverter drive | ID: p110.b31, p110.b30
- condizioni: The MP attempts to clear the fault five times within one minute; the fourth attempt removes inverter power for a power-up reset. If not cleared, the MP reverts to constant-speed operation without that inverter fan. | ID: p110.b30
- nota:

### Ramo R59
- problema: Condenser Fan Variable Speed Drive Fault - Circuit 1 (Drive 2) | ID: p111.b6
- codice: 
- causa: The MP received a fault signal from the respective condenser fan Variable Speed Inverter Drive and failed to clear it after five attempts. | ID: p111.b5
- azione: If the fault does not clear, manually bypass the inverter and rebind the fan outputs for full fixed-speed fan operation. | tipo: riparazione | ID: p111.b5
- componente: Condenser fan variable-speed inverter drive | ID: p111.b6, p111.b5
- condizioni: The MP attempts to clear the fault five times within one minute; the fourth attempt removes inverter power for a power-up reset. If not cleared, the MP reverts to constant-speed operation without that inverter fan. | ID: p111.b5
- nota:

### Ramo R60
- problema: Condenser Fan Variable Speed Drive Fault - Circuit 2 (Drive 1) | ID: p111.b13
- codice: 
- causa: The MP received a fault signal from the respective condenser fan Variable Speed Inverter Drive and failed to clear it after five attempts. | ID: p111.b11
- azione: If the fault does not clear, manually bypass the inverter and rebind the fan outputs for full fixed-speed fan operation. | tipo: riparazione | ID: p111.b11
- componente: Condenser fan variable-speed inverter drive | ID: p111.b13, p111.b11
- condizioni: The MP attempts to clear the fault five times within one minute; the fourth attempt removes inverter power for a power-up reset. If not cleared, the MP reverts to constant-speed operation without that inverter fan. | ID: p111.b11
- nota:

### Ramo R61
- problema: Condenser Fan Variable Speed Drive Fault - Circuit 2 (Drive 2) | ID: p111.b18
- codice: 
- causa: The MP received a fault signal from the respective condenser fan Variable Speed Inverter Drive and failed to clear it after five attempts. | ID: p111.b17
- azione: If the fault does not clear, manually bypass the inverter and rebind the fan outputs for full fixed-speed fan operation. | tipo: riparazione | ID: p111.b17
- componente: Condenser fan variable-speed inverter drive | ID: p111.b18, p111.b17
- condizioni: The MP attempts to clear the fault five times within one minute; the fourth attempt removes inverter power for a power-up reset. If not cleared, the MP reverts to constant-speed operation without that inverter fan. | ID: p111.b17
- nota:

### Ramo R62
- problema: Condenser Refrigerant Pressure Transducer - Circuit 1 | ID: p111.b23
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b24
- azione:  | tipo: riparazione | ID: 
- componente: Condenser refrigerant pressure transducer; LLID | ID: p111.b23, p111.b24
- condizioni: 
- nota:

### Ramo R63
- problema: Condenser Refrigerant Pressure Transducer - Circuit 2 | ID: p111.b25
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b26
- azione:  | tipo: riparazione | ID: 
- componente: Condenser refrigerant pressure transducer; LLID | ID: p111.b25, p111.b26
- condizioni: 
- nota:

### Ramo R64
- problema: Emergency Stop | ID: p111.b27
- codice: 
- causa: An external interlock has tripped. | ID: p111.b27
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The EMERGENCY STOP input is open; trip to unit stop is 0.1-1.0 seconds. | ID: p111.b27
- nota:

### Ramo R65
- problema: Evaporator Entering Water Temperature Sensor | ID: p111.b29
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b28
- azione:  | tipo: riparazione | ID: 
- componente: Evaporator entering-water temperature sensor; LLID | ID: p111.b29, p111.b28
- condizioni: Normal operation has no control effects. The chiller removes any Return or Constant Return Chilled Water Reset that was in effect and applies the specified slew rates. | ID: p111.b28, p111.b30
- nota:

### Ramo R66
- problema: Evaporator Leaving Water Temperature Sensor | ID: p111.b32
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b32
- azione:  | tipo: riparazione | ID: 
- componente: Evaporator leaving-water temperature sensor; LLID | ID: p111.b32
- condizioni: 
- nota:

### Ramo R67
- problema: Evaporator Liquid Level Sensor - Circuit 1 | ID: p111.b33
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b33
- azione:  | tipo: riparazione | ID: 
- componente: Evaporator liquid-level sensor; LLID | ID: p111.b33
- condizioni: 
- nota:

### Ramo R68
- problema: Evaporator Liquid Level Sensor - Circuit 2 | ID: p111.b34
- codice: 
- causa: Bad Sensor or LLID | ID: p111.b34
- azione:  | tipo: riparazione | ID: 
- componente: Evaporator liquid-level sensor; LLID | ID: p111.b34
- condizioni: 
- nota:

### Ramo R69
- problema: Evaporator Refrigerant Drain - Circuit 1 | ID: p111.b37
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Effective only with remote evaporator units and in circuit non-running modes. The liquid level was not below -21.2 mm within five minutes after the Drain Valve Solenoid was commanded open. Inactive if the drain valve is commanded closed. | ID: p111.b36, p111.b39
- nota:

### Ramo R70
- problema: Evaporator Refrigerant Drain - Circuit 2 | ID: p111.b41
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Effective only with remote evaporator units and in circuit non-running modes. The liquid level was not below -21.2 mm within five minutes after the Drain Valve Solenoid was commanded open. Inactive if the drain valve is commanded closed. | ID: p111.b40, p111.b39
- nota:

### Ramo R71
- problema: Evaporator Water Flow (Entering Water Temperature) | ID: p111.b43
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Entering evaporator water temperature fell below leaving evaporator water temperature by more than 2°F for 180°F-sec; minimum trip time is one minute. | ID: p111.b44
- nota:

### Ramo R72
- problema: Evaporator Water Flow (High Approach Temperature) - Circuit 1 | ID: p111.b45
- codice: 
- causa: No or reversed evaporator water flow is suggested. | ID: p111.b47
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Large evaporator approach temperatures, low evaporator saturated temperatures, and liquid refrigerant are the stated signs. | ID: p111.b47
- nota:

### Ramo R73
- problema: Evaporator Water Flow (High Approach Temperature) - Circuit 2 | ID: p112.b5
- codice: 
- causa: No or reversed evaporator water flow is suggested. | ID: p112.b7
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Large evaporator approach temperatures, low evaporator saturated temperatures, and liquid refrigerant are the stated signs. | ID: p112.b7
- nota:

### Ramo R74
- problema: Evaporator Water Flow Lost | ID: p112.b10
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Active when the evaporator pump is commanded on in Auto mode or by certain off-cycle diagnostics. The input must remain open more than 6-10 seconds (high-voltage binary input) or 20-25 seconds (factory-mounted low-voltage input); 6-10 seconds of continuous flow clears the diagnostic. | ID: p112.b8, p112.b9, p112.b28
- nota:

### Ramo R75
- problema: Evaporator Water Flow Overdue | ID: p112.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Flow was not proven within 4:15 for RTAC Rev 20 and earlier, or 20:00 for Rev 21. For software Rev 17 and earlier the pump output is de-energized; for Rev 18 and later its command status is not affected. Certain off-cycle diagnostics shorten the callout delay to 4:15. | ID: p112.b12, p112.b13
- nota:

### Ramo R76
- problema: External Chilled Water Setpoint | ID: p112.b17
- codice: 
- causa: When enabled, the input is out of range low or high, or has a bad LLID. | ID: p112.b16
- azione:  | tipo: riparazione | ID: 
- componente: LLID | ID: p112.b16
- condizioni: When not enabled, no diagnostic is generated. When enabled, the chiller defaults the chilled-water setpoint to the next priority; the diagnostic resets automatically when the input returns to the normal range. | ID: p112.b16
- nota:

### Ramo R77
- problema: External Current Limit Setpoint | ID: p112.b20
- codice: 
- causa: When enabled, the input is out of range low or high, or has a bad LLID. | ID: p112.b19
- azione:  | tipo: riparazione | ID: 
- componente: LLID | ID: p112.b19
- condizioni: When not enabled, no diagnostic is generated. When enabled, the current-limit setpoint defaults to the next priority; the diagnostic resets automatically when the input returns to the normal range. | ID: p112.b19
- nota:

### Ramo R78
- problema: High Differential Refrigerant Pressure - Circuit 1 | ID: p112.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: System differential pressure for the circuit exceeded 275 psid for two consecutive samples or more than 10 seconds. | ID: p112.b22
- nota:

### Ramo R79
- problema: High Differential Refrigerant Pressure - Circuit 2 | ID: p112.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: System differential pressure for the circuit exceeded 275 psid for two consecutive samples or more than 10 seconds. | ID: p112.b23
- nota:

### Ramo R80
- problema: High Evaporator Liquid Level - Circuit 1 | ID: p112.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While the compressor is running, the liquid-level sensor was at or near the high end of its range for 80 contiguous minutes (80% or more of bit count at +21.2 mm or higher). The timer holds but does not clear while the circuit is off. | ID: p112.b24
- nota:

### Ramo R81
- problema: High Evaporator Liquid Level - Circuit 2 | ID: p112.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While the compressor is running, the liquid-level sensor was at or near the high end of its range for 80 contiguous minutes (80% or more of bit count at +21.2 mm or higher). The timer holds but does not clear while the circuit is off. | ID: p112.b27
- nota:

### Ramo R82
- problema: High Evaporator Refrigerant Pressure | ID: p112.b31
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Either circuit exceeded 190 psig. The diagnostic resets automatically when all evaporator pressures fall below 185 psig. The water-pump relay is de-energized and the chiller is prevented from starting; this protects against pump heat raising refrigerant pressure near the relief-valve setting while the chiller is stopped. | ID: p112.b30
- nota:

### Ramo R83
- problema: High Evaporator Water Temperature - Pre-Refresh Rev 39 | ID: p113.b7, p113.b8
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Effective only while Evap Water Flow Overdue, Evap Water Flow Loss, or Low Evap Refrigerant Temp - Unit Off is active. Leaving-water temperature exceeded the service-menu limit (default 105°F) for 15 continuous seconds. It resets automatically when temperature falls 5°F below the trip setting; pump relay is de-energized only if running due to one of the listed diagnostics. | ID: p113.b5.1, p113.b5.2, p113.b6, p113.b7
- nota:

### Ramo R84
- problema: High Evaporator Water Temperature - Beginning with RTAC Refresh Rev 39 | ID: p113.b13, p113.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Effective only while Evap Water Flow Overdue, Evap Water Flow Loss, or Low Evap Refrigerant Temp - Unit Off is active. Leaving-water temperature exceeded the service-menu limit (default 105°F) for 15 continuous seconds. The pump relay is de-energized. Manual reset is required; the diagnostic clears regardless of temperature and may recur if trip criteria remain. | ID: p113.b11.1, p113.b11.2, p113.b12, p113.b13
- nota:

### Ramo R85
- problema: High Oil Temperature - Compressor 1B | ID: p113.b18
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Oil temperature supplied to the compressor exceeded 200°F for two consecutive samples or more than 10 seconds. In Compressor High Temperature Limit Mode, the female load step is forced loaded above 190°F and returns to normal control below 170°F. | ID: p113.b17
- nota:

### Ramo R86
- problema: High Oil Temperature - Compressor 2B | ID: p113.b21
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Oil temperature supplied to the compressor exceeded 200°F for two consecutive samples or more than 10 seconds. In Compressor High Temperature Limit Mode, the female load step is forced loaded above 190°F and returns to normal control below 170°F. | ID: p113.b20
- nota:

### Ramo R87
- problema: High Oil Temperature - Compressor 1A | ID: p113.b24
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Oil temperature supplied to the compressor exceeded 200°F for two consecutive samples or more than 10 seconds. In Compressor High Temperature Limit Mode, the female load step is forced loaded above 190°F and returns to normal control below 170°F. | ID: p113.b23
- nota:

### Ramo R88
- problema: High Oil Temperature - Compressor 2A | ID: p113.b27
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Oil temperature supplied to the compressor exceeded 200°F for two consecutive samples or more than 10 seconds. In Compressor High Temperature Limit Mode, the female load step is forced loaded above 190°F and returns to normal control below 170°F. | ID: p113.b26
- nota:

### Ramo R89
- problema: High Pressure Cutout - Compressor 1A | ID: p113.b30
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A high-pressure cutout was detected; stated trip is 315 ± 5 psig. Expected Phase Loss, Power Loss, and Transition Complete Input Open diagnostics are suppressed. | ID: p113.b29
- nota:

### Ramo R90
- problema: High Pressure Cutout - Compressor 1B | ID: p113.b33
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A high-pressure cutout was detected; stated trip is 315 ± 5 psig. Expected Phase Loss, Power Loss, and Transition Complete Input Open diagnostics are suppressed. | ID: p113.b32
- nota:

### Ramo R91
- problema: High Pressure Cutout - Compressor 2A | ID: p114.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A high-pressure cutout was detected; stated trip is 315 ± 5 psig. Expected Phase Loss, Power Loss, and Transition Complete Input Open diagnostics are suppressed. | ID: p114.b5
- nota:

### Ramo R92
- problema: High Pressure Cutout - Compressor 2B | ID: p114.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: A high-pressure cutout was detected; stated trip is 315 ± 5 psig. Expected Phase Loss, Power Loss, and Transition Complete Input Open diagnostics are suppressed. | ID: p114.b8
- nota:

### Ramo R93
- problema: Intermediate Oil Pressure Transducer - Compressor 1A | ID: p114.b11
- codice: 
- causa: Bad Sensor or LLID | ID: p114.b11
- azione:  | tipo: riparazione | ID: 
- componente: Intermediate oil-pressure transducer; LLID | ID: p114.b11
- condizioni: 
- nota:

### Ramo R94
- problema: Intermediate Oil Pressure Transducer - Compressor 1B | ID: p114.b12
- codice: 
- causa: Bad Sensor or LLID | ID: p114.b12
- azione:  | tipo: riparazione | ID: 
- componente: Intermediate oil-pressure transducer; LLID | ID: p114.b12
- condizioni: 
- nota:

### Ramo R95
- problema: Intermediate Oil Pressure Transducer - Compressor 2A | ID: p114.b13
- codice: 
- causa: Bad Sensor or LLID | ID: p114.b13
- azione:  | tipo: riparazione | ID: 
- componente: Intermediate oil-pressure transducer; LLID | ID: p114.b13
- condizioni: 
- nota:

### Ramo R96
- problema: Intermediate Oil Pressure Transducer - Compressor 2B | ID: p114.b14
- codice: 
- causa: Bad Sensor or LLID | ID: p114.b14
- azione:  | tipo: riparazione | ID: 
- componente: Intermediate oil-pressure transducer; LLID | ID: p114.b14
- condizioni: 
- nota:

### Ramo R97
- problema: Low Chilled Water Temperature: Unit Off | ID: p114.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Leaving evaporator water temperature was below the cutout setting for 30 degree-F seconds while the chiller was stopped or in Auto with no compressors running. The pump relay runs until automatic reset; reset occurs 2°F (1.1°C) above cutout for 30 minutes. | ID: p114.b15, p114.b16, p114.b37
- nota:

### Ramo R98
- problema: Low Chilled Water Temperature: Unit On | ID: p114.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Evaporator water temperature was below cutout setpoint for 30 degree-F seconds while the compressor was running. Automatic reset occurs 2°F (1.1°C) above cutout for 2 minutes. The diagnostic does not de-energize the evaporator-water-pump output. | ID: p114.b19, p114.b20, p114.b21
- nota:

### Ramo R99
- problema: Low Differential Refrigerant Pressure - Circuit 1 | ID: p114.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: System differential pressure was below 35 psid for more than 2000 psid-sec, after an ignore time of 1 minute for a single-compressor circuit or 2.5 minutes for a manifolded-compressor circuit. | ID: p114.b24
- nota:

### Ramo R100
- problema: Low Differential Refrigerant Pressure - Circuit 2 | ID: p114.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: System differential pressure was below 35 psid for more than 2000 psid-sec, after an ignore time of 1 minute for a single-compressor circuit or 2.5 minutes for a manifolded-compressor circuit. | ID: p114.b27
- nota:

### Ramo R101
- problema: Low Evaporator Liquid Level - Circuit 1 | ID: p114.b31
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While the compressor is running, the liquid-level sensor was at or near the low end of its range for 80 contiguous minutes (20% or less of bit count at -21.2 mm or lower). The timer holds but does not clear while the circuit is off. | ID: p114.b30
- nota:

### Ramo R102
- problema: Low Evaporator Liquid Level - Circuit 2 | ID: p114.b34
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: While the compressor is running, the liquid-level sensor was at or near the low end of its range for 80 contiguous minutes (20% or less of bit count at -21.2 mm or lower). The timer holds but does not clear while the circuit is off. | ID: p114.b33
- nota:

### Ramo R103
- problema: Low Evaporator Refrigerant Temperature - Circuit 1 | ID: p114.b37
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Inferred saturated evaporator refrigerant temperature, calculated from suction pressure, fell below the Low Refrigerant Temperature Cutout setpoint for 1125°F-sec, with an 8°F-sec/sec maximum integral rate during startup (4°F-sec/sec if manifolded with one compressor running). Minimum cutout setpoint is -5°F (18.7 psia). During a nonzero trip integral the unload solenoids remain energized and the load solenoid is off. Normal load/unload resumes when the trip integral decays to zero; the integral is retained through power-down and may decay during the circuit off-cycle. | ID: p114.b36.1, p114.b36.2
- nota:

### Ramo R104
- problema: Low Evaporator Refrigerant Temperature - Circuit 2 | ID: p115.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Inferred saturated evaporator refrigerant temperature, calculated from suction pressure, fell below the Low Refrigerant Temperature Cutout setpoint for 1125°F-sec, with an 8°F-sec/sec maximum integral rate during startup (4°F-sec/sec if manifolded with one compressor running). Minimum cutout setpoint is -5°F (18.7 psia). During a nonzero trip integral the unload solenoids remain energized and the load solenoid is off. Normal load/unload resumes when the trip integral decays to zero; the integral is retained through power-down and may decay during the circuit off-cycle. | ID: p115.b5.1, p115.b5.2
- nota:

### Ramo R105
- problema: Low Evaporator Temperature - Circuit 1: Unit Off | ID: p115.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: In Stop or Auto with no compressors running, an evaporator saturated temperature fell below the water-temperature cutout setting while liquid level exceeded -21.2 mm for 150°F-sec. Pump relay remains energized until automatic reset; reset occurs when temperature rises 2°F (1.1°C) above cutout or liquid level stays below -21.2 mm for 30 minutes. | ID: p115.b9, p115.b10, p115.b22, p115.b27
- nota:

### Ramo R106
- problema: Low Evaporator Temperature - Circuit 2: Unit Off | ID: p115.b16
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: In Stop or Auto with no compressors running, an evaporator saturated temperature fell below the water-temperature cutout setting while liquid level exceeded -21.2 mm for 150°F-sec. Pump relay remains energized until automatic reset; reset occurs when temperature rises 2°F (1.1°C) above cutout or liquid level stays below -21.2 mm for 30 minutes. | ID: p115.b14, p115.b15, p115.b34, p115.b38
- nota:

### Ramo R107
- problema: Low Oil Flow - Compressor 1A | ID: p115.b20
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: With compressor energized and delta pressure above 35 psid, the intermediate oil-pressure transducer was outside the acceptable range for 15 seconds: 0.50 > (PC-PI)/(PC-PE) during the first 2.5 minutes, and 0.25 > (PC-PI)/(PC-PE) thereafter. | ID: p115.b19
- nota:

### Ramo R108
- problema: Low Oil Flow - Compressor 1B | ID: p115.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: With compressor energized and delta pressure above 35 psid, the intermediate oil-pressure transducer was outside the acceptable range for 15 seconds: 0.50 > (PC-PI)/(PC-PE) during the first 2.5 minutes, and 0.25 > (PC-PI)/(PC-PE) thereafter. | ID: p115.b22
- nota:

### Ramo R109
- problema: Low Oil Flow - Compressor 2A | ID: p115.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: With compressor energized and delta pressure above 35 psid, the intermediate oil-pressure transducer was outside the acceptable range for 15 seconds: 0.50 > (PC-PI)/(PC-PE) during the first 2.5 minutes, and 0.25 > (PC-PI)/(PC-PE) thereafter. | ID: p115.b25
- nota:

### Ramo R110
- problema: Low Oil Flow - Compressor 2B | ID: p115.b29
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: With compressor energized and delta pressure above 35 psid, the intermediate oil-pressure transducer was outside the acceptable range for 15 seconds: 0.50 > (PC-PI)/(PC-PE) during the first 2.5 minutes, and 0.25 > (PC-PI)/(PC-PE) thereafter. | ID: p115.b28
- nota:

### Ramo R111
- problema: Low Suction Refrigerant Pressure - Circuit 1 | ID: p115.b32
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Suction refrigerant pressure fell below 10 psia just before compressor start (after EXV preposition), or fell below 16 psia while running after the ignore time, or below 10 psia (5 psia in software before October 2002) before the ignore time expired. Ignore time depends on outdoor-air temperature. | ID: p115.b31
- nota:

### Ramo R112
- problema: Low Suction Refrigerant Pressure - Circuit 2 | ID: p115.b35
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Suction refrigerant pressure fell below 10 psia just before compressor start (after EXV preposition), or fell below 16 psia while running after the ignore time, or below 10 psia (5 psia in software before October 2002) before the ignore time expired. Ignore time depends on outdoor-air temperature. | ID: p115.b34
- nota:

### Ramo R113
- problema: Low Suction Refrigerant Pressure - Compressor 1B | ID: p116.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Suction refrigerant pressure fell below 10 psia just before compressor start (after EXV preposition), or fell below 16 psia while running after the ignore time, or below 10 psia (5 psia in software before October 2002) before the ignore time expired. Ignore time depends on outdoor-air temperature. | ID: p116.b5
- nota:

### Ramo R114
- problema: Low Suction Refrigerant Pressure - Compressor 2B | ID: p116.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Suction refrigerant pressure fell below 10 psia just before compressor start (after EXV preposition), or fell below 16 psia while running after the ignore time, or below 10 psia (5 psia in software before October 2002) before the ignore time expired. Ignore time depends on outdoor-air temperature. | ID: p116.b8
- nota:

### Ramo R115
- problema: MP Application Memory CRC Error | ID: p116.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Memory-error criteria are listed as TBD. | ID: p116.b11
- nota:

### Ramo R116
- problema: MP: Could Not Store Starts and Hours | ID: p116.b12
- codice: 
- causa: The MP found an error with the previous power-down store. | ID: p116.b12
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Starts and hours for the last 24 hours may have been lost. | ID: p116.b12
- nota:

### Ramo R117
- problema: MP: Invalid Configuration | ID: p116.b13
- codice: 
- causa: The MP has an invalid configuration based on the current software installed. | ID: p116.b13
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: 
- nota:

### Ramo R118
- problema: MP: Non-Volatile Block Test Error | ID: p116.b14
- codice: 
- causa: The MP found an error with a block in non-volatile memory. | ID: p116.b14
- azione: Check settings. | tipo: controllo | ID: p116.b14
- componente: Non-volatile memory block | ID: p116.b14
- condizioni: 
- nota:

### Ramo R119
- problema: MP: Non-Volatile Memory Reformat | ID: p116.b15
- codice: 
- causa: The MP found an error in a non-volatile-memory sector and reformatted it. | ID: p116.b15
- azione: Check settings. | tipo: controllo | ID: p116.b15
- componente: Non-volatile memory sector | ID: p116.b15
- condizioni: 
- nota:

### Ramo R120
- problema: MP: Reset Has Occurred | ID: p116.b17
- codice: 
- causa: The main processor came out of reset and built its application; reset may follow power-up, new software, or a new configuration. | ID: p116.b16
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The diagnostic clears immediately and automatically and is visible only in the TechView historic diagnostic list. | ID: p116.b16
- nota:

### Ramo R121
- problema: Oil Flow Fault - Compressor 1A | ID: p116.b20
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: For 30 continuous seconds, the intermediate oil-pressure transducer read at least 15 psia above circuit condenser pressure or at least 10 psia below suction pressure. | ID: p116.b19
- nota:

### Ramo R122
- problema: Oil Flow Fault - Compressor 1B | ID: p116.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: For 30 continuous seconds, the intermediate oil-pressure transducer read at least 15 psia above circuit condenser pressure or at least 10 psia below suction pressure. | ID: p116.b22
- nota:

### Ramo R123
- problema: Oil Flow Fault - Compressor 2A | ID: p116.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: For 30 continuous seconds, the intermediate oil-pressure transducer read at least 15 psia above circuit condenser pressure or at least 10 psia below suction pressure. | ID: p116.b25
- nota:

### Ramo R124
- problema: Oil Flow Fault - Compressor 2B | ID: p116.b29
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: For 30 continuous seconds, the intermediate oil-pressure transducer read at least 15 psia above circuit condenser pressure or at least 10 psia below suction pressure. | ID: p116.b28
- nota:

### Ramo R125
- problema: Oil Temperature Sensor - Compressor 1B | ID: p116.b31
- codice: 
- causa: Bad Sensor or LLID | ID: p116.b31
- azione:  | tipo: riparazione | ID: 
- componente: Oil-temperature sensor; LLID | ID: p116.b31
- condizioni: 
- nota:

### Ramo R126
- problema: Oil Temperature Sensor - Compressor 2B | ID: p116.b32
- codice: 
- causa: Bad Sensor or LLID | ID: p116.b32
- azione:  | tipo: riparazione | ID: 
- componente: Oil-temperature sensor; LLID | ID: p116.b32
- condizioni: 
- nota:

### Ramo R127
- problema: Oil Temperature Sensor - Compressor 1A | ID: p116.b33
- codice: 
- causa: Bad Sensor or LLID | ID: p116.b33
- azione:  | tipo: riparazione | ID: 
- componente: Oil-temperature sensor; LLID | ID: p116.b33
- condizioni: 
- nota:

### Ramo R128
- problema: Oil Temperature Sensor - Compressor 2A | ID: p116.b34
- codice: 
- causa: Bad Sensor or LLID | ID: p116.b34
- azione:  | tipo: riparazione | ID: 
- componente: Oil-temperature sensor; LLID | ID: p116.b34
- condizioni: 
- nota:

### Ramo R129
- problema: Outdoor Air Temperature Sensor | ID: p116.b35
- codice: 
- causa: Bad Sensor or LLID | ID: p116.b35
- azione:  | tipo: riparazione | ID: 
- componente: Outdoor-air temperature sensor; LLID | ID: p116.b35
- condizioni: If this diagnostic occurs, operational pumpdown is performed regardless of the last valid temperature. | ID: p116.b35
- nota:

### Ramo R130
- problema: Pumpdown Terminated - Circuit 1 | ID: p116.b36
- codice: 
- causa: The pumpdown cycle ended abnormally due to excessive time or a specific diagnostic criterion, without associated latching diagnostics. | ID: p116.b36
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Active during pumpdown mode. | ID: p116.b36
- nota:

### Ramo R131
- problema: Pumpdown Terminated - Circuit 2 | ID: p117.b5
- codice: 
- causa: The pumpdown cycle ended abnormally due to excessive time or a specific diagnostic criterion, without associated latching diagnostics. | ID: p117.b5
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Active during pumpdown mode. | ID: p117.b5
- nota:

### Ramo R132
- problema: Software Error 1001: Call Trane Service (beginning with Rev 29) | ID: p117.b6
- codice: 1001 | ID: p117.b6
- causa: A compressor was reported running without chilled-water flow for three minutes; before Rev 29 the threshold was five minutes. | ID: p117.b7
- azione: Call Trane Service. | tipo: assistenza | ID: p117.b6
- componente:  | ID: 
- condizioni: Reported in all modes. | ID: p117.b7
- nota:

### Ramo R133
- problema: Software Error 1002: Call Trane Service (beginning with Rev 29) | ID: p117.b8
- codice: 1002 | ID: p117.b8
- causa: State-chart misalignment occurred in the stopped or inactive state. | ID: p117.b9
- azione: Call Trane Service. | tipo: assistenza | ID: p117.b8
- componente:  | ID: 
- condizioni: Reported in all modes. | ID: p117.b9
- nota:

### Ramo R134
- problema: Software Error 1003: Call Trane Service (beginning with Rev 29) | ID: p117.b10
- codice: 1003 | ID: p117.b10
- causa: State-chart misalignment occurred in the stopping state. | ID: p117.b11
- azione: Call Trane Service. | tipo: assistenza | ID: p117.b10
- componente:  | ID: 
- condizioni: Reported in all modes. | ID: p117.b11
- nota:

### Ramo R135
- problema: Software Error Number 1001 (Rev 28) | ID: p117.b13
- codice: 1001 | ID: p117.b13
- causa: A high-level software watchdog detected five continuous minutes of compressor operation without chilled-water flow and without a Contactor Interrupt Failure diagnostic; this suggests an internal software state-chart misalignment. | ID: p117.b16
- azione: Record the events that led to the failure, if known, and transmit them to Trane Controls Engineering. | tipo: assistenza | ID: p117.b16
- componente:  | ID: 
- condizioni: The manual requires a power-down reset. | ID: p117.b12, p117.b30, p117.b32
- nota:

### Ramo R136
- problema: Starter Failed to Arm/Start - Compressor 1A | ID: p117.b17
- codice: 
- causa: The starter failed to arm or start within the allotted time. | ID: p117.b17
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Allotted time is 15 seconds. | ID: p117.b17
- nota:

### Ramo R137
- problema: Starter Failed to Arm/Start - Compressor 1B | ID: p117.b18
- codice: 
- causa: The starter failed to arm or start within the allotted time. | ID: p117.b18
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Allotted time is 15 seconds. | ID: p117.b18
- nota:

### Ramo R138
- problema: Starter Failed to Arm/Start - Compressor 2A | ID: p117.b19
- codice: 
- causa: The starter failed to arm or start within the allotted time. | ID: p117.b19
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Allotted time is 15 seconds. | ID: p117.b19
- nota:

### Ramo R139
- problema: Starter Failed to Arm/Start - Compressor 2B | ID: p117.b20
- codice: 
- causa: The starter failed to arm or start within the allotted time. | ID: p117.b20
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Allotted time is 15 seconds. | ID: p117.b20
- nota:

### Ramo R140
- problema: Starter Module Memory Error Type 1 - Starter 2A | ID: p117.b21
- codice: 
- causa: Checksum on the RAM copy of the Starter LLID configuration failed; configuration was recalled from EEPROM. | ID: p117.b21
- azione:  | tipo: riparazione | ID: 
- componente: RAM copy of Starter LLID configuration | ID: p117.b21
- condizioni: 
- nota:

### Ramo R141
- problema: Starter Module Memory Error Type 1 - Starter 2B | ID: p117.b22
- codice: 
- causa: Checksum on the RAM copy of the Starter LLID configuration failed; configuration was recalled from EEPROM. | ID: p117.b22
- azione:  | tipo: riparazione | ID: 
- componente: RAM copy of Starter LLID configuration | ID: p117.b22
- condizioni: 
- nota:

### Ramo R142
- problema: Starter Module Memory Error Type 1 - Starter 1A | ID: p117.b23
- codice: 
- causa: Checksum on the RAM copy of the Starter LLID configuration failed; configuration was recalled from EEPROM. | ID: p117.b23
- azione:  | tipo: riparazione | ID: 
- componente: RAM copy of Starter LLID configuration | ID: p117.b23
- condizioni: 
- nota:

### Ramo R143
- problema: Starter Module Memory Error Type 1 - Starter 1B | ID: p117.b24
- codice: 
- causa: Checksum on the RAM copy of the Starter LLID configuration failed; configuration was recalled from EEPROM. | ID: p117.b24
- azione:  | tipo: riparazione | ID: 
- componente: RAM copy of Starter LLID configuration | ID: p117.b24
- condizioni: 
- nota:

### Ramo R144
- problema: Starter Module Memory Error Type 2 - Starter 1A | ID: p117.b25
- codice: 
- causa: Checksum on the EEPROM copy of the Starter LLID configuration failed; factory default values were used. | ID: p117.b25
- azione:  | tipo: riparazione | ID: 
- componente: EEPROM copy of Starter LLID configuration | ID: p117.b25
- condizioni: 
- nota:

### Ramo R145
- problema: Starter Module Memory Error Type 2 - Starter 1B | ID: p117.b26
- codice: 
- causa: Checksum on the EEPROM copy of the Starter LLID configuration failed; factory default values were used. | ID: p117.b26
- azione:  | tipo: riparazione | ID: 
- componente: EEPROM copy of Starter LLID configuration | ID: p117.b26
- condizioni: 
- nota:

### Ramo R146
- problema: Starter Module Memory Error Type 2 - Starter 2A | ID: p117.b27
- codice: 
- causa: Checksum on the EEPROM copy of the Starter LLID configuration failed; factory default values were used. | ID: p117.b27
- azione:  | tipo: riparazione | ID: 
- componente: EEPROM copy of Starter LLID configuration | ID: p117.b27
- condizioni: 
- nota:

### Ramo R147
- problema: Starter Module Memory Error Type 2 - Starter 2B | ID: p117.b28
- codice: 
- causa: Checksum on the EEPROM copy of the Starter LLID configuration failed; factory default values were used. | ID: p117.b28
- azione:  | tipo: riparazione | ID: 
- componente: EEPROM copy of Starter LLID configuration | ID: p117.b28
- condizioni: 
- nota:

### Ramo R148
- problema: Starter Panel High Temperature Limit - Panel 1, Compressor 1B | ID: p117.b29
- codice: 
- causa: Starter Panel High Limit Thermostat (170°F) trip was detected. | ID: p117.b31
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Other diagnostics that may result from this panel-temperature trip are suppressed: Phase Loss, Power Loss, and Transition Complete Input Open. | ID: p117.b31
- nota:

### Ramo R149
- problema: Starter Panel High Temperature Limit - Panel 1, Compressor 2A | ID: p117.b30
- codice: 
- causa: Starter Panel High Limit Thermostat (170°F) trip was detected. | ID: p117.b33
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Other diagnostics that may result from this panel-temperature trip are suppressed: Phase Loss, Power Loss, and Transition Complete Input Open. | ID: p117.b33
- nota:

### Ramo R150
- problema: Starter Panel High Temperature Limit - Panel 2, Compressor 2B | ID: p118.b6
- codice: 
- causa: Starter Panel High Limit Thermostat (170°F) trip was detected. | ID: p118.b5
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Other diagnostics that may result from this panel-temperature trip are suppressed: Phase Loss, Power Loss, and Transition Complete Input Open. | ID: p118.b5
- nota:

### Ramo R151
- problema: Suction Refrigerant Pressure Transducer - Circuit 1, Compressor 1A | ID: p118.b9
- codice: 
- causa: Bad Sensor or LLID | ID: p118.b8
- azione:  | tipo: riparazione | ID: 
- componente: Suction refrigerant pressure transducer; LLID | ID: p118.b9, p118.b8
- condizioni: For manifolded compressors without isolation valves, this diagnostic also generates a communication loss for the nonexistent Suction Pressure Compressor 1B to shut down the circuit. | ID: p118.b8
- nota:

### Ramo R152
- problema: Suction Refrigerant Pressure Transducer - Circuit 1, Compressor 1B | ID: p118.b12
- codice: 
- causa: Bad Sensor or LLID | ID: p118.b13
- azione:  | tipo: riparazione | ID: 
- componente: Suction refrigerant pressure transducer; LLID | ID: p118.b12, p118.b13
- condizioni: For manifolded compressors without isolation valves, the diagnostic may occur with the preceding diagnostic even though this transducer is not required or installed. | ID: p118.b13
- nota:

### Ramo R153
- problema: Suction Refrigerant Pressure Transducer - Circuit 2, Compressor 2A | ID: p118.b17
- codice: 
- causa: Bad Sensor or LLID | ID: p118.b16
- azione:  | tipo: riparazione | ID: 
- componente: Suction refrigerant pressure transducer; LLID | ID: p118.b17, p118.b16
- condizioni: For manifolded compressors without isolation valves, this diagnostic also generates a communication loss for the nonexistent Suction Pressure Compressor 2B to shut down the circuit. | ID: p118.b16
- nota:

### Ramo R154
- problema: Suction Refrigerant Pressure Transducer - Circuit 2, Compressor 2B | ID: p118.b20
- codice: 
- causa: Bad Sensor or LLID | ID: p118.b21
- azione:  | tipo: riparazione | ID: 
- componente: Suction refrigerant pressure transducer; LLID | ID: p118.b20, p118.b21
- condizioni: For manifolded compressors without isolation valves, the diagnostic may occur with the preceding diagnostic even though this transducer is not required or installed. | ID: p118.b21
- nota:

### Ramo R155
- problema: Very Low Evaporator Refrigerant Pressure - Circuit 1 | ID: p118.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Evaporator pressure fell below 8 psia (5 psia in software before October 2002), whether or not compressors are running. The whole chiller shuts down to prevent compressor failure due to cross-binding; transducers for a locked-out compressor or circuit are excluded. | ID: p118.b24
- nota:

### Ramo R156
- problema: Very Low Evaporator Refrigerant Pressure - Circuit 2 | ID: p118.b30
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Evaporator pressure fell below 8 psia (5 psia in software before October 2002), whether or not compressors are running. The whole chiller shuts down to prevent compressor failure due to cross-binding; transducers for a locked-out compressor or circuit are excluded. | ID: p118.b28
- nota:

### Ramo R157
- problema: Comm Loss: Chilled Water Flow Switch | ID: p118.b39
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p118.b39
- nota:

### Ramo R158
- problema: Comm Loss: Condenser Refrigerant Pressure, Circuit #1 | ID: p118.b40
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p118.b40
- nota:

### Ramo R159
- problema: Comm Loss: Condenser Refrigerant Pressure, Circuit #2 | ID: p118.b41
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p118.b41
- nota:

### Ramo R160
- problema: Comm Loss: Electronic Expansion Valve, Circuit #1 | ID: p119.b5
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b5
- nota:

### Ramo R161
- problema: Comm Loss: Electronic Expansion Valve, Circuit #2 | ID: p119.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b6
- nota:

### Ramo R162
- problema: Comm Loss: Emergency Stop | ID: p119.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b7
- nota:

### Ramo R163
- problema: Comm Loss: Evaporator Oil Return Valve, Compressor 1A | ID: p119.b8
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b8
- nota:

### Ramo R164
- problema: Comm Loss: Evaporator Oil Return Valve, Compressor 1B | ID: p119.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b9
- nota:

### Ramo R165
- problema: Comm Loss: Evaporator Oil Return Valve, Compressor 2A | ID: p119.b10
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b10
- nota:

### Ramo R166
- problema: Comm Loss: Evaporator Oil Return Valve, Compressor 2B | ID: p119.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b11
- nota:

### Ramo R167
- problema: Comm Loss: Evaporator Entering Water Temperature | ID: p119.b13
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The chiller removes Return or Constant Return Chilled Water Reset, if active, and applies the specified slew rates. | ID: p119.b12
- nota:

### Ramo R168
- problema: Comm Loss: Evaporator Leaving Water Temperature | ID: p119.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b17
- nota:

### Ramo R169
- problema: Comm Loss: Evaporator Refrigerant Drain Valve - Circuit 1 | ID: p119.b18
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b18
- nota:

### Ramo R170
- problema: Comm Loss: Evaporator Refrigerant Drain Valve - Circuit 2 | ID: p119.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b19
- nota:

### Ramo R171
- problema: Comm Loss: Evaporator Refrigerant Liquid Level, Circuit #1 | ID: p119.b20
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b20
- nota:

### Ramo R172
- problema: Comm Loss: Evaporator Refrigerant Liquid Level, Circuit #2 | ID: p119.b21
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b21
- nota:

### Ramo R173
- problema: Comm Loss: Evaporator Refrigerant Pressure, Circuit #1 | ID: p119.b22
- codice: 5FB | ID: p119.b23
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b23
- nota:

### Ramo R174
- problema: Comm Loss: Evaporator Refrigerant Pressure, Circuit #2 | ID: p119.b24
- codice: 5FD | ID: p119.b25
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b25
- nota:

### Ramo R175
- problema: Comm Loss: Evaporator Water Pump Control | ID: p119.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b26
- nota:

### Ramo R176
- problema: Comm Loss: External Auto/Stop | ID: p119.b27
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p119.b27
- nota:

### Ramo R177
- problema: Comm Loss: External Chilled Water Setpoint | ID: p119.b30
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The chiller discontinues use of this setpoint and reverts to the next higher-priority source. | ID: p119.b29
- nota:

### Ramo R178
- problema: Comm Loss: External Circuit Lockout, Circuit #1 | ID: p119.b34
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The MP nonvolatily holds the lockout state (enabled or disabled) that was in effect when communication was lost. | ID: p119.b33
- nota:

### Ramo R179
- problema: Comm Loss: External Circuit Lockout, Circuit #2 | ID: p119.b37
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The MP nonvolatily holds the lockout state (enabled or disabled) that was in effect when communication was lost. | ID: p119.b36
- nota:

### Ramo R180
- problema: Comm Loss: External Current Limit Setpoint | ID: p119.b41
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The chiller discontinues use of this setpoint and reverts to the next higher-priority current-limit setpoint source. | ID: p119.b40
- nota:

### Ramo R181
- problema: Comm Loss: Fan Control Circuit #1, Stage #1 | ID: p120.b5
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b5
- nota:

### Ramo R182
- problema: Comm Loss: Fan Control Circuit #1, Stage #2 | ID: p120.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b6
- nota:

### Ramo R183
- problema: Comm Loss: Fan Control Circuit #1, Stage #3 | ID: p120.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b7
- nota:

### Ramo R184
- problema: Comm Loss: Fan Control Circuit #1, Stage #4 | ID: p120.b8
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b8
- nota:

### Ramo R185
- problema: Comm Loss: Fan Control Circuit #2, Stage #1 | ID: p120.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b9
- nota:

### Ramo R186
- problema: Comm Loss: Fan Control Circuit #2, Stage #2 | ID: p120.b10
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b10
- nota:

### Ramo R187
- problema: Comm Loss: Fan Control Circuit #2, Stage #3 | ID: p120.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b11
- nota:

### Ramo R188
- problema: Comm Loss: Fan Control Circuit #2, Stage #4 | ID: p120.b12
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b12
- nota:

### Ramo R189
- problema: Comm Loss: Fan Inverter Fault, Circuit #1, Drive 1 | ID: p120.b13
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b13
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b13
- nota:

### Ramo R190
- problema: Comm Loss: Fan Inverter Fault, Circuit #1, Drive 2 | ID: p120.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b14
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b14
- nota:

### Ramo R191
- problema: Comm Loss: Fan Inverter Fault, Circuit #2, Drive 1 | ID: p120.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b15
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b15
- nota:

### Ramo R192
- problema: Comm Loss: Fan Inverter Fault, Circuit #2, Drive 2 | ID: p120.b16
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b16
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b16
- nota:

### Ramo R193
- problema: Comm Loss: Fan Inverter Power, Circuit #1 / Drive 1 and 2 | ID: p120.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b17
- nota:

### Ramo R194
- problema: Comm Loss: Fan Inverter Power, Circuit #2 / Drive 1 and 2 | ID: p120.b18
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b18
- nota:

### Ramo R195
- problema: Comm Loss: Fan Inverter Speed Command, Circuit #1 / Drive 1 and 2 | ID: p120.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b20
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b20
- nota:

### Ramo R196
- problema: Comm Loss: Fan Inverter Speed Command, Circuit #2 / Drive 1 and 2 | ID: p120.b21
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Operate the remaining fans as a fixed-speed fan deck. | tipo: controllo | ID: p120.b22
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operate the remaining fans as a fixed-speed fan deck. | ID: p120.b22
- nota:

### Ramo R197
- problema: Comm Loss: Female Step Load Compressor 1A | ID: p120.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b23
- nota:

### Ramo R198
- problema: Comm Loss: Female Step Load Compressor 1B | ID: p120.b24
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b24
- nota:

### Ramo R199
- problema: Comm Loss: Female Step Load Compressor 2A | ID: p120.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b25
- nota:

### Ramo R200
- problema: Comm Loss: Female Step Load Compressor 2B | ID: p120.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b26
- nota:

### Ramo R201
- problema: Comm Loss: High Pressure Cutout Switch, Compressor 1A | ID: p120.b27
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b27
- nota:

### Ramo R202
- problema: Comm Loss: High Pressure Cutout Switch, Compressor 1B | ID: p120.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p120.b28
- nota:

### Ramo R203
- problema: Comm Loss: High Pressure Cutout Switch, Compressor 2A | ID: p121.b5
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b5
- nota:

### Ramo R204
- problema: Comm Loss: High Pressure Cutout Switch, Compressor 2B | ID: p121.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b6
- nota:

### Ramo R205
- problema: Comm Loss: Ice-Machine Control | ID: p121.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The chiller reverts to normal (non-ice-building) mode regardless of its last state. | ID: p121.b10
- nota:

### Ramo R206
- problema: Comm Loss: Ice-Making Status | ID: p121.b10
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. The chiller reverts to normal (non-ice-building) mode regardless of its last state. | ID: p121.b10
- nota:

### Ramo R207
- problema: Comm Loss: Intermediate Oil Pressure, Compressor 1A | ID: p121.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b11
- nota:

### Ramo R208
- problema: Comm Loss: Intermediate Oil Pressure, Compressor 1B | ID: p121.b12
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b12
- nota:

### Ramo R209
- problema: Comm Loss: Intermediate Oil Pressure, Compressor 2A | ID: p121.b13
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b13
- nota:

### Ramo R210
- problema: Comm Loss: Intermediate Oil Pressure, Compressor 2B | ID: p121.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b14
- nota:

### Ramo R211
- problema: Comm Loss: Local BAS Interface | ID: p121.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b15
- nota:

### Ramo R212
- problema: Comm Loss: Male Port Load Compressor 1A | ID: p121.b16
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b16
- nota:

### Ramo R213
- problema: Comm Loss: Male Port Load Compressor 1B | ID: p121.b17
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b17
- nota:

### Ramo R214
- problema: Comm Loss: Male Port Load Compressor 2A | ID: p121.b18
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b18
- nota:

### Ramo R215
- problema: Comm Loss: Male Port Load Compressor 2B | ID: p121.b19
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b19
- nota:

### Ramo R216
- problema: Comm Loss: Male Port Unload Compressor 1A | ID: p121.b20
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b20
- nota:

### Ramo R217
- problema: Comm Loss: Male Port Unload Compressor 1B | ID: p121.b21
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b21
- nota:

### Ramo R218
- problema: Comm Loss: Male Port Unload Compressor 2A | ID: p121.b22
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b22
- nota:

### Ramo R219
- problema: Comm Loss: Male Port Unload Compressor 2B | ID: p121.b23
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b23
- nota:

### Ramo R220
- problema: Comm Loss: Oil Temperature Circuit #1 or Compressor 1A | ID: p121.b24
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b24, p121.b58
- nota:

### Ramo R221
- problema: Comm Loss: Oil Temperature Circuit #2 or Compressor 2A | ID: p121.b25
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b25, p121.b61
- nota:

### Ramo R222
- problema: Comm Loss: Oil Temperature Compressor 1B | ID: p121.b26
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b26
- nota:

### Ramo R223
- problema: Comm Loss: Oil Temperature Compressor 2B | ID: p121.b27
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p121.b27
- nota:

### Ramo R224
- problema: Comm Loss: Outdoor Air Temperature | ID: p121.b28
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. Operational pumpdown is performed regardless of the last valid temperature. | ID: p121.b29
- nota:

### Ramo R225
- problema: Comm Loss: Starter 1A | ID: p121.b31
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The MP continually lost communication with the Starter 1A for 30 seconds. | ID: p121.b31
- nota:

### Ramo R226
- problema: Comm Loss: Starter 1B | ID: p122.b5
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The MP continually lost communication with the Starter 1B for 30 seconds. | ID: p122.b5
- nota:

### Ramo R227
- problema: Comm Loss: Starter 2A | ID: p122.b6
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The MP continually lost communication with the Starter 2A for 30 seconds. | ID: p122.b6
- nota:

### Ramo R228
- problema: Comm Loss: Starter 2B | ID: p122.b7
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The MP continually lost communication with the Starter 2B for 30 seconds. | ID: p122.b7
- nota:

### Ramo R229
- problema: Comm Loss: Starter Panel High Temperature Limit - Panel 1, Compressor 2A | ID: p122.b8
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p122.b8
- nota:

### Ramo R230
- problema: Comm Loss: Starter Panel High Temperature Limit - Panel 1, Compressor 1B | ID: p122.b9
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p122.b9
- nota:

### Ramo R231
- problema: Comm Loss: Starter Panel High Temperature Limit - Panel 2, Compressor 2B | ID: p122.b10
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p122.b10
- nota:

### Ramo R232
- problema: Comm Loss: Status/Annunciation Relays | ID: p122.b11
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. | ID: p122.b11
- nota:

### Ramo R233
- problema: Comm Loss: Suction Pressure Compressor 1A | ID: p122.b12
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. With manifolded compressors without isolation valves, this also generates a loss for the nonexistent Suction Pressure Compressor 1B to shut down the circuit. | ID: p122.b17
- nota:

### Ramo R234
- problema: Comm Loss: Suction Pressure Compressor 1B | ID: p122.b13
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. With manifolded compressors without isolation valves, this can occur with the preceding diagnostic even though this transducer is not required or installed. | ID: p122.b19
- nota:

### Ramo R235
- problema: Comm Loss: Suction Pressure Compressor 2A | ID: p122.b14
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. With manifolded compressors without isolation valves, this also generates a loss for the nonexistent Suction Pressure Compressor 2B to shut down the circuit. | ID: p122.b21
- nota:

### Ramo R236
- problema: Comm Loss: Suction Pressure Compressor 2B | ID: p122.b15
- codice: 
- causa: non indicata nel manuale | ID: 
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication between the MP and the Functional ID was continually lost for 30 seconds. With manifolded compressors without isolation valves, this can occur with the preceding diagnostic even though this transducer is not required or installed. | ID: p122.b19
- nota:

### Ramo R237
- problema: Excessive Loss of Comm | ID: p122.b16
- codice: 
- causa: Communication was lost with 75% or more of configured LLIDs (10% in Rev 18 and earlier). | ID: p122.b25
- azione: Check the power supplies. | tipo: controllo | ID: p122.b25
- azione: Check the power disconnects. | tipo: controllo | ID: p122.b25
- azione: Troubleshoot the LLIDS bus using TechView. | tipo: controllo | ID: p122.b25
- componente:  | ID: 
- condizioni: This diagnostic suppresses the callout of all subsequent communication-loss diagnostics. | ID: p122.b25
- nota:

### Ramo R238
- problema: Starter 1A Comm Loss: MP | ID: p122.b27
- codice: 
- causa: The starter lost communication with the MP for 15 seconds. | ID: p122.b27
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication loss between the starter and MP lasted 15 seconds. | ID: p122.b27
- nota:

### Ramo R239
- problema: Starter 1B Comm Loss: MP | ID: p122.b28
- codice: 
- causa: The starter lost communication with the MP for 15 seconds. | ID: p122.b28
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication loss between the starter and MP lasted 15 seconds. | ID: p122.b28
- nota:

### Ramo R240
- problema: Starter 2A Comm Loss: MP | ID: p122.b29
- codice: 
- causa: The starter lost communication with the MP for 15 seconds. | ID: p122.b29
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication loss between the starter and MP lasted 15 seconds. | ID: p122.b29
- nota:

### Ramo R241
- problema: Starter 2B Comm Loss: MP | ID: p122.b30
- codice: 
- causa: The starter lost communication with the MP for 15 seconds. | ID: p122.b30
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Communication loss between the starter and MP lasted 15 seconds. | ID: p122.b30
- nota:

### Ramo R242
- problema: A Valid Configuration is Present | ID: p123.b6
- codice: 
- causa: A valid configuration is present in the MP nonvolatile memory. | ID: p123.b5
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: Temporary display during the normal power-up sequence. | ID: p123.b5
- nota:

### Ramo R243
- problema: App Present. Running Selftest… — Selftest Passed | ID: p123.b7
- codice: 
- causa: The application was detected in MP nonvolatile memory and the boot code completed and passed the CRC test. | ID: p123.b8
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The display is temporary during the normal power-up sequence. | ID: p123.b8
- nota:

### Ramo R244
- problema: App Present. Running Selftest… — Err3: CRC Failure | ID: p123.b10
- codice: Err3 | ID: p123.b10
- causa: The boot code completed its check of the application but the CRC test failed. | ID: p123.b9
- azione: Connect a TechView service tool to the MP serial port. | tipo: controllo | ID: p123.b9
- azione: Provide the chiller model number and download the configuration if TechView prompts for it. | tipo: controllo | ID: p123.b9
- azione: Download the most recent RTAC application or the version recommended by Technical Service. | tipo: riparazione | ID: p123.b9
- azione: If the problem persists, replace the MP. | tipo: riparazione | ID: p123.b9
- componente: Main Processor (MP) | ID: p123.b9
- condizioni: This display may also occur during programming if the MP had no valid application before the download. | ID: p123.b9
- nota:

### Ramo R245
- problema: Boot Software Part Numbers | ID: p123.b12
- codice: 
- causa: non indicata nel manuale | ID: 
- azione: Provide the displayed part numbers when contacting Technical Service about power-up problems. | tipo: assistenza | ID: p123.b11
- componente:  | ID: 
- condizioni: This is normal. Provide the displayed part numbers when contacting Technical Service about power-up problems. | ID: p123.b11
- nota:

### Ramo R246
- problema: Converter Mode | ID: p123.b13
- codice: 
- causa: The MP received a TechView command to stop the running application and enter converter mode. | ID: p123.b13
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: In this mode the MP is a gateway that lets the TechView service computer communicate with LLIDs on the IPC3 bus. | ID: p123.b13
- nota:

### Ramo R247
- problema: Err2: RAM Address Test #1 Failure | ID: p123.b14
- codice: Err2 | ID: p123.b14
- causa: RAM errors were detected in RAM Address Test #1. | ID: p123.b14
- azione: Recycle power. | tipo: controllo | ID: p123.b14
- azione: If the error persists, replace the MP. | tipo: riparazione | ID: p123.b14
- componente: Main Processor RAM | ID: p123.b14
- condizioni: 
- nota:

### Ramo R248
- problema: Err2: RAM Address Test #2 Failure | ID: p123.b15
- codice: Err2 | ID: p123.b15
- causa: RAM errors were detected in RAM Address Test #2. | ID: p123.b15
- azione: Recycle power. | tipo: controllo | ID: p123.b15
- azione: If the error persists, replace the MP. | tipo: riparazione | ID: p123.b15
- componente: Main Processor RAM | ID: p123.b15
- condizioni: 
- nota:

### Ramo R249
- problema: Err2: RAM Pattern 1 Failure | ID: p123.b16
- codice: Err2 | ID: p123.b16
- causa: RAM errors were detected in RAM Pattern 1. | ID: p123.b16
- azione: Recycle power. | tipo: controllo | ID: p123.b16
- azione: If the error persists, replace the MP. | tipo: riparazione | ID: p123.b16
- componente: Main Processor RAM | ID: p123.b16
- condizioni: 
- nota:

### Ramo R250
- problema: Err2: RAM Pattern 2 Failure | ID: p123.b17
- codice: Err2 | ID: p123.b17
- causa: RAM errors were detected in RAM Pattern 2. | ID: p123.b17
- azione: Recycle power. | tipo: controllo | ID: p123.b17
- azione: If the error persists, replace the MP. | tipo: riparazione | ID: p123.b17
- componente: Main Processor RAM | ID: p123.b17
- condizioni: 
- nota:

### Ramo R251
- problema: Err4: UnHandled Interrupt | ID: p123.b19
- codice: Err4 | ID: p123.b19
- causa: An unhandled interrupt occurred while the application code was running; this normally causes a safe chiller shutdown, processor reset, diagnostic clearing, and restart attempt. | ID: p123.b18.1
- azione: If the error recurs, try replacing the MP. | tipo: riparazione | ID: p123.b18.1
- azione: If replacing the MP is ineffective, contact Technical Service about possible high radiated or conducted EMI. | tipo: assistenza | ID: p123.b18.2
- azione: If the message appears immediately after a software download, reload both the configuration and application. | tipo: riparazione | ID: p123.b18.2
- azione: If reloading fails, contact Technical Service. | tipo: assistenza | ID: p123.b18.2
- componente: Main Processor (MP) | ID: p123.b18.1, p123.b18.2
- condizioni: The restart timer is a 3-second countdown. The condition may follow a severe electromagnetic transient such as a nearby lightning strike. | ID: p123.b18.1, p123.b19
- nota:

### Ramo R252
- problema: Err5: Operating System Error | ID: p123.b21
- codice: Err5 | ID: p123.b21
- causa: An operating-system error occurred while the application code was running. | ID: p123.b20
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The chiller normally shuts down safely; when the 30-second countdown ends, the processor resets, clears diagnostics, and attempts to restart. The manual refers to Err4 for further guidance. | ID: p123.b20, p123.b21
- nota:

### Ramo R253
- problema: Err6: Watch Dog Timer Error | ID: p123.b22
- codice: Err6 | ID: p123.b22
- causa: A Watch Dog Timer Error occurred while the application code was running. | ID: p123.b23
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The chiller normally shuts down safely; after the 30-second countdown the processor resets, clears diagnostics, and attempts to restart. | ID: p123.b23, p123.b22
- nota:

### Ramo R254
- problema: Err7: Unknown Error | ID: p123.b24
- codice: Err7 | ID: p123.b24
- causa: An unknown error occurred while the application code was running. | ID: p123.b25
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: The chiller normally shuts down safely; after the 30-second countdown the processor resets, clears diagnostics, and attempts to restart. | ID: p123.b25, p123.b24
- nota:

### Ramo R255
- problema: Err8: Held in Boot by User Key Press | ID: p123.b26
- codice: Err8 | ID: p123.b26
- causa: The boot code detected a key press in the center of DynaView while the MP was in boot code. | ID: p123.b26
- azione: Use TechView to connect to the MP to perform a software download or another service-tool function. | tipo: controllo | ID: p123.b26
- componente:  | ID: 
- condizioni: 
- nota:

### Ramo R256
- problema: No Application Present — Please Load Application | ID: p123.b28
- codice: 
- causa: No Main Processor application is present; no RAM test errors were detected. | ID: p123.b27
- azione: Connect a TechView service tool to the MP serial port. | tipo: controllo | ID: p123.b27
- azione: Provide the chiller model number and download the configuration if TechView prompts for it. | tipo: controllo | ID: p123.b27
- azione: Download the most recent RTAC application or the version recommended by Technical Service. | tipo: riparazione | ID: p123.b27
- componente: Main Processor (MP) | ID: p123.b27
- condizioni: 
- nota:

### Ramo R257
- problema: Programming Mode | ID: p123.b30
- codice: 
- causa: The MP received a TechView command and is erasing and then writing program code to its internal flash memory. | ID: p123.b29
- azione:  | tipo: riparazione | ID: 
- componente:  | ID: 
- condizioni: If the MP had no prior application in memory, Err3 appears instead during the download. | ID: p123.b29
- nota:
