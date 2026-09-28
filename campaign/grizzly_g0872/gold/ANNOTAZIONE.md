# Annotazione del gold: Grizzly G0872 CNC laser cutter/engraver

- Annotatore: Fabio Daniele
- Data: 2026-09-28
- Tempo impiegato (minuti): 150 (stima)
- Pagine annotate: 9, 26–27, 32, 35, 37, 39–40, 42, 46, 48–52, 54, 60–62, 64

## Criterio del perimetro

Ho sfogliato tutte le 80 pagine del file. Ho incluso i codici macchina, i test di sicurezza con esito anomalo, l'allarme del chiller, l'avviso sull'amperometro, gli errori TrackFrame, le condizioni di guasto con rimedio esplicito (ottiche, circuito acqua, filtri, condotti, cinghie, cablaggio e allineamento del fascio) e tutte le righe diagnostiche delle tabelle. Ho lasciato fuori le procedure ordinarie di installazione, pulizia e regolazione prive di un problema o di un esito anomalo. I rimandi di pagina sono conservati nelle condizioni.

## Rami

### Ramo R1
- problema: Frame Slop: travel exceeds working envelope of X- and Y-axes. | ID: p9.b19, p9.b20
- codice: Frame Slop | ID: p9.b19, p9.b20
- causa: non indicata nel manuale | ID: p9.b19, p9.b20
- azione:  | tipo:  | ID: p9.b19, p9.b20
- componente:  | ID: p9.b19, p9.b20
- condizioni:  | ID: p9.b19, p9.b20
- nota:

### Ramo R2
- problema: Name Over Lap: file with same name is detected in destination memory location. | ID: p9.b23, p9.b24, p35.b2, p35.b3
- codice: Name Over Lap | ID: p9.b23, p9.b24, p35.b2, p35.b3
- causa: non indicata nel manuale | ID: p9.b23, p9.b24
- azione:  | tipo:  | ID: p9.b23, p9.b24, p35.b2, p35.b3
- componente:  | ID: p9.b23, p9.b24
- condizioni: file with the same name is detected in machine memory | ID: p35.b2, p35.b3
- nota:

### Ramo R3
- problema: XSlop Over: travel exceeds working envelope of X-axis. | ID: p9.b43, p9.b44
- codice: XSlop Over | ID: p9.b43, p9.b44
- causa: non indicata nel manuale | ID: p9.b43, p9.b44
- azione:  | tipo:  | ID: p9.b43, p9.b44
- componente:  | ID: p9.b43, p9.b44
- condizioni:  | ID: p9.b43, p9.b44
- nota:

### Ramo R4
- problema: YSlop Over: travel exceeds working envelope of Y-axis. | ID: p9.b45, p9.b46
- codice: YSlop Over | ID: p9.b45, p9.b46
- causa: non indicata nel manuale | ID: p9.b45, p9.b46
- azione:  | tipo:  | ID: p9.b45, p9.b46
- componente:  | ID: p9.b45, p9.b46
- condizioni:  | ID: p9.b45, p9.b46
- nota:

### Ramo R5
- problema: Unusual problem during the test run. | ID: p26.b3
- codice: - | ID: p26.b3
- causa: non indicata nel manuale | ID: p26.b3
- azione: Immediately stop the machine. | tipo: controllo | ID: p26.b3
- azione: Disconnect the machine from power. | tipo: controllo | ID: p26.b3
- azione: Fix the problem before operating the machine again. | tipo: riparazione | ID: p26.b3
- azione: Review the Troubleshooting table in the SERVICE section for help. | tipo: controllo | ID: p26.b3
- componente:  | ID: p26.b3
- condizioni: during the test run; before operating the machine again | ID: p26.b3
- nota:

### Ramo R6
- problema: Laser head assembly moves while the limit switch lever is held in place. | ID: p27.b5, p27.b8
- codice: - | ID: p27.b5, p27.b8
- causa: The limit switch safety feature is NOT working properly. | ID: p27.b9
- azione: Test movement by holding the limit switch lever in place and pressing the arrow navigation buttons. | tipo: controllo | ID: p27.b5
- azione: Repeat Steps 8–9 on the y-axis limit switch. | tipo: controllo | ID: p27.b10
- azione: Disconnect the machine from power. | tipo: controllo | ID: p27.b9
- azione: Replace the limit switch before operating the machine. | tipo: riparazione | ID: p27.b9
- componente: limit switch | ID: p27.b9, p27.b10
- condizioni: if the laser head assembly moves; before operating the machine | ID: p27.b8, p27.b9
- nota:

### Ramo R7
- problema: Laser audibly beeps and briefly pulses ON while the top loading door is open. | ID: p27.b14, p27.b17
- codice: - | ID: p27.b14, p27.b17
- causa: The top loading door interlock switch safety feature is NOT working properly. | ID: p27.b18
- azione: Press the Pulse button with the top loading door open to test fire the laser. | tipo: controllo | ID: p27.b14
- azione: Disconnect the machine from power. | tipo: controllo | ID: p27.b18
- azione: Replace the top loading door interlock switch before operating the machine. | tipo: riparazione | ID: p27.b18
- componente: top loading door interlock switch | ID: p27.b18
- condizioni: if the laser audibly beeps and briefly pulses ON; before operating the machine | ID: p27.b17, p27.b18
- nota:

### Ramo R8
- problema: Machine does not turn OFF when the Emergency Stop button is pressed. | ID: p27.b19, p27.b22
- codice: - | ID: p27.b19, p27.b22
- causa: The safety feature of the Emergency Stop button is NOT working properly. | ID: p27.b23
- azione: Press the Emergency Stop button to turn the machine OFF. | tipo: controllo | ID: p27.b19
- azione: Immediately disconnect the machine from power. | tipo: controllo | ID: p27.b22, p27.b23
- azione: Replace the Emergency Stop button before operating the machine. | tipo: riparazione | ID: p27.b23
- componente: Emergency Stop button | ID: p27.b23
- condizioni: if the machine does not turn OFF; before operating the machine | ID: p27.b22, p27.b23
- nota:

### Ramo R9
- problema: Water chiller sounds an audible alarm and suspends circulating water. | ID: p32.b4
- codice: - | ID: p32.b4
- causa: non indicata nel manuale | ID: p32.b4
- azione: A larger water chiller system may be required. | tipo: riparazione | ID: p32.b4
- azione: A refrigeration-type water chiller may have to be installed. | tipo: riparazione | ID: p32.b4
- componente:  | ID: p32.b4
- condizioni: Keep water temperature below 122º F (50º C); a larger system may be required if an overheat alarm occurs regularly; a refrigeration-type chiller may have to be installed in environments susceptible to extreme heat. | ID: p32.b4
- nota:

### Ramo R10
- problema: Ammeter indication exceeds the mA rating listed above the ammeter. | ID: p37.b19, p37.b20
- codice: - | ID: p37.b19, p37.b20
- causa: impending laser tube failure, or electrical faults | ID: p37.b20
- azione: During operation, verify that the ammeter indicator does not exceed the mA rating listed above the ammeter. | tipo: controllo | ID: p37.b19
- componente:  | ID: p37.b19, p37.b20
- condizioni: when the indication exceeds the mA rating | ID: p37.b19, p37.b20
- nota:

### Ramo R11
- problema: "XSlop Over," "YSlop Over," or "Frame slop" error displayed during TrackFrame. | ID: p40.b8, p40.b9, p40.b12
- codice: XSlop Over; YSlop Over; Frame slop | ID: p40.b8, p40.b9
- causa: the currently queued image is outside the working envelope, based on current origin | ID: p40.b12
- azione: Press Menu, select "File manage+", and press Enter. | tipo: controllo | ID: p39.b18
- azione: Highlight "TrackFrame" in the job setup screen. | tipo: controllo | ID: p39.b19
- azione: Review the .RD file using RDCam. | tipo: controllo | ID: p40.b1
- azione: Position the workpiece so the queued image fits within the working envelope. | tipo: riparazione | ID: p40.b1
- azione: Move the laser head assembly to the origin defined in RDCam, in reference to the working envelope. | tipo: riparazione | ID: p40.b2
- azione: Press the Origin button. | tipo: controllo | ID: p40.b4
- azione: Press Enter to trace the perimeter of the toolpaths. | tipo: controllo | ID: p40.b5
- azione: Observe the perimeter traced by laser head movement. | tipo: controllo | ID: p40.b5
- azione: Verify the display shows "Tracking Frame" during operation. | tipo: controllo | ID: p40.b5
- componente: laser head assembly; workpiece | ID: p40.b1, p40.b2
- condizioni: if one of the listed errors is displayed, repeat Steps 1–6; based on current origin | ID: p40.b8, p40.b9, p40.b12
- nota:

### Ramo R12
- problema: Loose mounting bolts. | ID: p42.b4, p42.b5
- codice: - | ID: p42.b4, p42.b5
- causa: non indicata nel manuale | ID: p42.b5
- azione: Shut down the machine immediately. | tipo: controllo | ID: p42.b4
- azione: Fix the problem before continuing operations. | tipo: riparazione | ID: p42.b4
- componente: mounting bolts | ID: p42.b5
- condizioni: if observed | ID: p42.b4, p42.b5
- nota:

### Ramo R13
- problema: Damaged laser optics. | ID: p42.b4, p42.b5
- codice: - | ID: p42.b4, p42.b5
- causa: non indicata nel manuale | ID: p42.b5
- azione: Shut down the machine immediately. | tipo: controllo | ID: p42.b4
- azione: Fix the problem before continuing operations. | tipo: riparazione | ID: p42.b4
- componente: laser optics | ID: p42.b5
- condizioni: if observed | ID: p42.b4, p42.b5
- nota:

### Ramo R14
- problema: Worn or damaged wires. | ID: p42.b4, p42.b5
- codice: - | ID: p42.b4, p42.b5
- causa: non indicata nel manuale | ID: p42.b5
- azione: Shut down the machine immediately. | tipo: controllo | ID: p42.b4
- azione: Fix the problem before continuing operations. | tipo: riparazione | ID: p42.b4
- componente: wires | ID: p42.b5
- condizioni: if observed | ID: p42.b4, p42.b5
- nota:

### Ramo R15
- problema: Any other unsafe condition. | ID: p42.b4, p42.b5
- codice: - | ID: p42.b4, p42.b5
- causa: non indicata nel manuale | ID: p42.b5
- azione: Shut down the machine immediately. | tipo: controllo | ID: p42.b4
- azione: Fix the problem before continuing operations. | tipo: riparazione | ID: p42.b4
- componente:  | ID: p42.b5
- condizioni: if observed | ID: p42.b4, p42.b5
- nota:

### Ramo R16
- problema: Binding may occur. | ID: p46.b1, p46.b2
- codice: - | ID: p46.b1, p46.b2
- causa: non indicata nel manuale | ID: p46.b2
- azione: Verify that left and right belts (where used) have the same deflection. | tipo: controllo | ID: p46.b2
- componente: left and right belts | ID: p46.b2
- condizioni: if left and right belts do not have the same deflection, binding may occur; where left and right belts are used | ID: p46.b2
- nota:

### Ramo R17
- problema: A bump or notch in a cutting path. | ID: p46.b3, p46.b4
- codice: - | ID: p46.b3, p46.b4
- causa: Material build-up on cogs or teeth. | ID: p46.b4
- azione: Remove contaminants in the crevices of cogs or teeth using a firm-bristled toothbrush. | tipo: riparazione | ID: p46.b3
- azione: Support the underside of the belt with a finger to prevent stretching while removing contaminants. | tipo: controllo | ID: p46.b3
- componente: cogs; teeth; belt | ID: p46.b3, p46.b4
- condizioni: if material has built up on cogs or teeth | ID: p46.b3, p46.b4
- nota:

### Ramo R18
- problema: Belts have cracks or damaged teeth. | ID: p46.b5
- codice: - | ID: p46.b5
- causa: non indicata nel manuale | ID: p46.b5
- azione: Replace the belts. | tipo: riparazione | ID: p46.b5
- componente: belts | ID: p46.b5
- condizioni: see Adjusting/Replacing Synchronous Belts on Page 51 | ID: p46.b5
- nota:

### Ramo R19
- problema: Particulates or surface stains remain on the lens/mirror surface after cleaning. | ID: p48.b2, p48.b3, p48.b4
- codice: - | ID: p48.b2, p48.b3, p48.b4
- causa: non indicata nel manuale | ID: p48.b3, p48.b4
- azione: Repeat Steps 2–5. | tipo: riparazione | ID: p48.b4
- azione: Replace the optics if particulates or stains are still present after the second cleaning. | tipo: riparazione | ID: p48.b5, p48.b6
- componente: lens; mirror; optics | ID: p48.b2, p48.b6
- condizioni: if any particulates or surface stains remain; if they remain after a second cleaning, they are most likely permanently burned into the surface; see Page 61 | ID: p48.b3, p48.b5, p48.b6
- nota:

### Ramo R20
- problema: Particulates or surface stains remain on removed laser optics after cleaning. | ID: p48.b23, p48.b24, p48.b25
- codice: - | ID: p48.b23, p48.b24, p48.b25
- causa: non indicata nel manuale | ID: p48.b24, p48.b25
- azione: Repeat Steps 2–4 using a clean sheet of lens cleaning paper for every pass. | tipo: riparazione | ID: p48.b25
- azione: Replace the optics if particulates or stains are still present after the second cleaning. | tipo: riparazione | ID: p48.b26, p48.b27
- componente: lens; mirror; optics | ID: p48.b23, p48.b27
- condizioni: if any particulates or surface stains remain; if they remain after a second cleaning, they are most likely permanently burned into the surface; see Page 61 | ID: p48.b24, p48.b26, p48.b27
- nota:

### Ramo R21
- problema: Radiator fan intake screen is blocked. | ID: p49.b5, p49.b6
- codice: - | ID: p49.b5, p49.b6
- causa: non indicata nel manuale | ID: p49.b6
- azione: Inspect the radiator fan intake screen for blockage. | tipo: controllo | ID: p49.b6
- azione: Clean the intake screen. | tipo: riparazione | ID: p49.b6
- componente: radiator fan intake screen | ID: p49.b6
- condizioni: clean as required | ID: p49.b6
- nota:

### Ramo R22
- problema: Leaks or damage in water chiller hoses and connections. | ID: p49.b7
- codice: - | ID: p49.b7
- causa: non indicata nel manuale | ID: p49.b7
- azione: Inspect hoses and connections for leaks or damage. | tipo: controllo | ID: p49.b7
- azione: Repair the hoses or connections. | tipo: riparazione | ID: p49.b7
- azione: Replace the hoses or connections. | tipo: riparazione | ID: p49.b7
- componente: water chiller hoses; connections | ID: p49.b7
- condizioni: repair or replace as required | ID: p49.b7
- nota:

### Ramo R23
- problema: Water is discolored or shows evidence of algae; water is contaminated. | ID: p49.b8
- codice: - | ID: p49.b8
- causa: non indicata nel manuale | ID: p49.b8
- azione: Inspect the water for discoloration and evidence of algae. | tipo: controllo | ID: p49.b8
- azione: Drain the water. | tipo: riparazione | ID: p49.b8
- azione: Clean the reservoir. | tipo: riparazione | ID: p49.b8
- azione: Refill the reservoir with distilled water. | tipo: riparazione | ID: p49.b8
- componente: water; reservoir | ID: p49.b8
- condizioni: drain, clean and refill if contaminated | ID: p49.b8
- nota:

### Ramo R24
- problema: Foam filter has holes, rips, or tears. | ID: p49.b23
- codice: - | ID: p49.b23
- causa: non indicata nel manuale | ID: p49.b23
- azione: Inspect the foam filter for holes, rips, or tears. | tipo: controllo | ID: p49.b23
- azione: Replace the foam filter. | tipo: riparazione | ID: p49.b23
- componente: foam filter | ID: p49.b23
- condizioni: replace as required | ID: p49.b23
- nota:

### Ramo R25
- problema: Tubing or filter cover has cracks or leakage. | ID: p49.b24
- codice: - | ID: p49.b24
- causa: non indicata nel manuale | ID: p49.b24
- azione: Inspect the tubing and filter cover for cracks and leakage. | tipo: controllo | ID: p49.b24
- azione: Replace the tubing or filter cover. | tipo: riparazione | ID: p49.b24
- componente: tubing; filter cover | ID: p49.b24
- condizioni: replace as required | ID: p49.b24
- nota:

### Ramo R26
- problema: Exhaust ducting has leaks. | ID: p50.b5, p50.b6
- codice: - | ID: p50.b5, p50.b6
- causa: non indicata nel manuale | ID: p50.b6
- azione: Inspect ducting for evidence of leaks. | tipo: controllo | ID: p50.b6
- azione: Patch the ducts. | tipo: riparazione | ID: p50.b6
- azione: Replace the ducts. | tipo: riparazione | ID: p50.b6
- componente: exhaust ducts | ID: p50.b6
- condizioni: patch or replace as required | ID: p50.b6
- nota:

### Ramo R27
- problema: Table is out-of-square with laser head rack. | ID: p54.o1
- codice: - | ID: p54.o1
- causa: Z-Axis belt becomes loose. | ID: p54.o1
- azione: Using a dial indicator at each corner, alternately rotate each leadscrew to square the table with the laser rack. | tipo: riparazione | ID: p54.o1
- azione: Re-install the synchronous belt on the pulleys once all leadscrews are synced and the table is square. | tipo: riparazione | ID: p54.o1
- componente: Z-Axis belt; leadscrews; table | ID: p54.o1
- condizioni: if the belt becomes loose; the belt is a low-usage component and is NOT adjustable | ID: p54.o1
- nota:

### Ramo R28
- problema: Laser beam falls outside the center of the crosshairs at the upper-left position. | ID: p60.b19, p60.b26
- codice: - | ID: p60.b19, p60.b26
- causa: non indicata nel manuale | ID: p60.b26
- azione: Move the laser head assembly to the upper-left corner of the table. | tipo: controllo | ID: p60.b3
- azione: Insert a 1-inch piece of paper or manila folder into the alignment gauge and install the gauge in the laser head beam inlet. | tipo: controllo | ID: p60.b9
- azione: Close the top loading door and check alignment by pressing Pulse; compare the result with Figure 97. | tipo: controllo | ID: p60.b19
- azione: Loosen the lock nuts on the three brass thumbscrews behind Mirror #1. | tipo: riparazione | ID: p60.b28
- azione: Adjust beam direction by tightening the thumbscrews for the desired direction of travel. | tipo: riparazione | ID: p61.b1
- azione: Verify mirror adjustment by pressing Pulse and compare the result with Figure 97. | tipo: controllo | ID: p61.b7
- componente: laser head assembly; alignment gauge; Mirror #1; lock nuts; thumbscrews | ID: p60.b3, p60.b9, p60.b28, p61.b1
- condizioni: if the beam falls outside the center of the crosshairs, adjustment is required; if it remains outside, repeat Steps 16–18; Pulse operates only with the top loading door closed | ID: p60.b19, p60.b26, p61.b7, p61.b10
- nota:

### Ramo R29
- problema: Laser beam falls outside the center of the crosshairs or mirror at the lower-left position. | ID: p61.b18, p61.b21, p61.b30, p61.b33
- codice: - | ID: p61.b18, p61.b21, p61.b30, p61.b33
- causa: non indicata nel manuale | ID: p61.b21, p61.b33
- azione: Move the laser head assembly to the lower-left corner of the table. | tipo: controllo | ID: p61.b12
- azione: Check alignment by pressing Pulse and compare the result with Figure 97. | tipo: controllo | ID: p61.b18
- azione: Place the mirror alignment gauge in front of Mirror #2 and hold it in place with masking tape. | tipo: controllo | ID: p61.b23
- azione: Verify Mirror #1 and Mirror #2 alignment by pressing Pulse. | tipo: controllo | ID: p61.b30
- azione: Loosen the lock nuts on the three brass thumbscrews behind the Mirror #1 assembly. | tipo: riparazione | ID: p61.b35
- azione: Adjust beam direction by tightening the thumbscrews for the desired direction of travel. | tipo: riparazione | ID: p61.b36
- azione: Repeat Step 22 to verify alignment. | tipo: controllo | ID: p61.b37
- componente: laser head assembly; Mirror #1; Mirror #2; alignment gauge; masking tape; lock nuts; thumbscrews | ID: p61.b12, p61.b23, p61.b35, p61.b36
- condizioni: adjust if the beam is outside the crosshairs or outside the center of the mirror; if still outside, repeat Step 22 | ID: p61.b18, p61.b21, p61.b30, p61.b33, p61.b37
- nota:

### Ramo R30
- problema: Laser beam falls outside the center of the crosshairs at the lower-right position. | ID: p62.b7, p62.b10
- codice: - | ID: p62.b7, p62.b10
- causa: non indicata nel manuale | ID: p62.b10
- azione: Move the laser head assembly to the lower-right corner of the table. | tipo: controllo | ID: p62.b1
- azione: Verify Mirror #2 and Mirror #3 alignment by pressing Pulse. | tipo: controllo | ID: p62.b7
- azione: Loosen the lock nuts on the three brass thumbscrews behind the Mirror #2 assembly. | tipo: riparazione | ID: p62.b12
- azione: Adjust beam direction by tightening the thumbscrews for the desired direction of travel. | tipo: riparazione | ID: p62.b17
- azione: Repeat Step 27 to verify alignment. | tipo: controllo | ID: p62.b23
- azione: Tighten all loose lock nuts on the mirror assemblies; do not tighten the thumbscrews. | tipo: riparazione | ID: p62.b24
- componente: laser head assembly; Mirror #2; Mirror #3; lock nuts; thumbscrews | ID: p62.b1, p62.b7, p62.b12, p62.b17, p62.b24
- condizioni: if the beam falls outside the center of the crosshairs, adjustment is required; after alignment is complete | ID: p62.b7, p62.b10, p62.b24
- nota:

### Ramo R31
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Emergency stop button depressed/at fault. | ID: p51.t1.r2
- azione: Rotate the emergency stop button head to reset. | tipo: riparazione | ID: p51.t1.r2
- azione: Replace the emergency stop button. | tipo: riparazione | ID: p51.t1.r2
- componente: Emergency stop button | ID: p51.t1.r2
- condizioni: replace only if at fault | ID: p51.t1.r2
- nota:

### Ramo R32
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Incorrect power supply voltage or circuit size. | ID: p51.t1.r2
- azione: Ensure the correct power supply voltage and circuit size. | tipo: controllo | ID: p51.t1.r2
- componente:  | ID: p51.t1.r2
- condizioni:  | ID: p51.t1.r2
- nota:

### Ramo R33
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Power supply circuit breaker tripped or fuse blown. | ID: p51.t1.r2
- azione: Ensure the circuit is sized correctly and free of shorts. | tipo: controllo | ID: p51.t1.r2
- azione: Reset the circuit breaker. | tipo: riparazione | ID: p51.t1.r2
- azione: Replace the fuse. | tipo: riparazione | ID: p51.t1.r2
- componente: power supply circuit breaker; fuse | ID: p51.t1.r2
- condizioni: reset if tripped; replace if blown | ID: p51.t1.r2
- nota:

### Ramo R34
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Air pump, water chiller, or exhaust fan have a short. | ID: p51.t1.r2
- azione: Inspect the air pump, water chiller, or exhaust fan. | tipo: controllo | ID: p51.t1.r2
- azione: Replace the affected part. | tipo: riparazione | ID: p51.t1.r2
- componente: air pump; water chiller; exhaust fan | ID: p51.t1.r2
- condizioni: replace if at fault | ID: p51.t1.r2
- nota:

### Ramo R35
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Wiring broken, disconnected, or corroded. | ID: p51.t1.r2
- azione: Fix broken wires or disconnected/corroded connections. | tipo: riparazione | ID: p51.t1.r2
- componente: wiring; connections | ID: p51.t1.r2
- condizioni:  | ID: p51.t1.r2
- nota:

### Ramo R36
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Machine chassis ground at fault. | ID: p51.t1.r2
- azione: Connect the machine to a dedicated ground rod at or near the machine. | tipo: riparazione | ID: p51.t1.r2
- componente: machine chassis ground; ground rod | ID: p51.t1.r2
- condizioni: see Page 15 | ID: p51.t1.r2
- nota:

### Ramo R37
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Laser tube at fault. | ID: p51.t1.r2
- azione: Inspect for evidence of arcing at laser tube connections. | tipo: controllo | ID: p51.t1.r2
- azione: Verify wire insulation is preventing arcing and discharge to the machine frame. | tipo: controllo | ID: p51.t1.r2
- componente: laser tube; laser tube connections; wire insulation | ID: p51.t1.r2
- condizioni:  | ID: p51.t1.r2
- nota:

### Ramo R38
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Power supply or controller at fault. | ID: p51.t1.r2
- azione: Inspect the power supply or controller. | tipo: controllo | ID: p51.t1.r2
- azione: Replace the power supply or controller. | tipo: riparazione | ID: p51.t1.r2
- componente: power supply; controller | ID: p51.t1.r2
- condizioni: only if at fault; see Page 63 | ID: p51.t1.r2
- nota:

### Ramo R39
- problema: Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | ID: p51.t1.r2
- codice: - | ID: p51.t1.r2
- causa: Computer board at fault. | ID: p51.t1.r2
- azione: Inspect the computer board. | tipo: controllo | ID: p51.t1.r2
- azione: Replace the computer board. | tipo: riparazione | ID: p51.t1.r2
- componente: computer board | ID: p51.t1.r2
- condizioni: only if at fault; see Page 63 | ID: p51.t1.r2
- nota:

### Ramo R40
- problema: Machine has vibration or noisy operation. | ID: p51.t1.r3
- codice: - | ID: p51.t1.r3
- causa: Stepper motor or component loose. | ID: p51.t1.r3
- azione: Replace damaged or missing bolts/nuts. | tipo: riparazione | ID: p51.t1.r3
- azione: Tighten bolts/nuts if loose. | tipo: riparazione | ID: p51.t1.r3
- componente: stepper motor or component; bolts/nuts | ID: p51.t1.r3
- condizioni: tighten if loose | ID: p51.t1.r3
- nota:

### Ramo R41
- problema: Machine has vibration or noisy operation. | ID: p51.t1.r3
- codice: - | ID: p51.t1.r3
- causa: Belt(s) worn, loose, pulleys misaligned or belt slapping cover. | ID: p51.t1.r3
- azione: Inspect the belts. | tipo: controllo | ID: p51.t1.r3
- azione: Replace the belts with a new matched set. | tipo: riparazione | ID: p51.t1.r3
- azione: Realign the pulleys. | tipo: riparazione | ID: p51.t1.r3
- componente: belts; pulleys | ID: p51.t1.r3
- condizioni: realign pulleys if necessary | ID: p51.t1.r3
- nota:

### Ramo R42
- problema: Machine has vibration or noisy operation. | ID: p51.t1.r3
- codice: - | ID: p51.t1.r3
- causa: Incorrectly mounted to workbench. | ID: p51.t1.r3
- azione: Adjust the feet. | tipo: riparazione | ID: p51.t1.r3
- azione: Shim the machine. | tipo: riparazione | ID: p51.t1.r3
- azione: Tighten the mounting hardware. | tipo: riparazione | ID: p51.t1.r3
- componente: feet; mounting hardware | ID: p51.t1.r3
- condizioni:  | ID: p51.t1.r3
- nota:

### Ramo R43
- problema: Machine has vibration or noisy operation. | ID: p51.t1.r3
- codice: - | ID: p51.t1.r3
- causa: Workpiece loose. | ID: p51.t1.r3
- azione: Use the correct holding fixture. | tipo: riparazione | ID: p51.t1.r3
- azione: Reclamp the workpiece. | tipo: riparazione | ID: p51.t1.r3
- componente: workpiece; holding fixture | ID: p51.t1.r3
- condizioni:  | ID: p51.t1.r3
- nota:

### Ramo R44
- problema: Machine has vibration or noisy operation. | ID: p51.t1.r3
- codice: - | ID: p51.t1.r3
- causa: Stepper motor bearings at fault. | ID: p51.t1.r3
- azione: Test by rotating the shaft. | tipo: controllo | ID: p51.t1.r3
- azione: Replace the bearing. | tipo: riparazione | ID: p51.t1.r3
- componente: stepper motor bearings; shaft | ID: p51.t1.r3
- condizioni: rotational grinding or loose shaft requires bearing replacement | ID: p51.t1.r3
- nota:

### Ramo R45
- problema: Flash drive is not read by laser machine, or file unable to load from flash drive. | ID: p52.t1.r2
- codice: - | ID: p52.t1.r2
- causa: Incorrect file structure or wrong file format. | ID: p52.t1.r2
- azione: Use a formatted flash drive with artwork files saved in RDCam Ruby Document (.RD) format. | tipo: riparazione | ID: p52.t1.r2
- componente:  | ID: p52.t1.r2
- condizioni: file format must be RDCam Ruby Document (.RD) | ID: p52.t1.r2
- nota:

### Ramo R46
- problema: Flash drive is not read by laser machine, or file unable to load from flash drive. | ID: p52.t1.r2
- codice: - | ID: p52.t1.r2
- causa: Artwork file not saved using included RDCam software. | ID: p52.t1.r2
- azione: Save the artwork file to the flash drive using the included RDCam software. | tipo: riparazione | ID: p52.t1.r2
- componente:  | ID: p52.t1.r2
- condizioni: see Page 28 | ID: p52.t1.r2
- nota:

### Ramo R47
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser speed, path, or other CNC error exists. | ID: p52.t1.r3
- azione: Review RDCam path settings. | tipo: controllo | ID: p52.t1.r3
- azione: Verify that the software is free of errors. | tipo: controllo | ID: p52.t1.r3
- componente:  | ID: p52.t1.r3
- condizioni:  | ID: p52.t1.r3
- nota:

### Ramo R48
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Incorrect laser speed or laser power setting. | ID: p52.t1.r3
- azione: Review RDCam power settings. | tipo: controllo | ID: p52.t1.r3
- azione: Verify that speed/power is set as desired. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust laser speed/power at the machine. | tipo: riparazione | ID: p52.t1.r3
- componente:  | ID: p52.t1.r3
- condizioni: see Pages 28 and 35 | ID: p52.t1.r3
- nota:

### Ramo R49
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Focus is not set to correct height. | ID: p52.t1.r3
- azione: Inspect the focal length. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust the focal length. | tipo: riparazione | ID: p52.t1.r3
- azione: Inspect table parallelism. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust table parallelism. | tipo: riparazione | ID: p52.t1.r3
- componente: table | ID: p52.t1.r3
- condizioni: see Pages 36 and 52 | ID: p52.t1.r3
- nota:

### Ramo R50
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser is skewed or off-center. | ID: p52.t1.r3
- azione: Verify mirrors are secure. | tipo: controllo | ID: p52.t1.r3
- azione: Verify the reflective side of the mirrors is facing outward. | tipo: controllo | ID: p52.t1.r3
- azione: Align the laser beam. | tipo: riparazione | ID: p52.t1.r3
- azione: Clean the laser optics. | tipo: riparazione | ID: p52.t1.r3
- componente: mirrors; laser optics | ID: p52.t1.r3
- condizioni: see Pages 61, 57 and 45 | ID: p52.t1.r3
- nota:

### Ramo R51
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser path is obstructed by smoke or material. | ID: p52.t1.r3
- azione: Verify the air supply hose is unobstructed and connected to the air nozzle. | tipo: controllo | ID: p52.t1.r3
- azione: Inspect the air pump. | tipo: controllo | ID: p52.t1.r3
- azione: Replace the air pump. | tipo: riparazione | ID: p52.t1.r3
- azione: Verify the exhaust ducting is unobstructed and functional. | tipo: controllo | ID: p52.t1.r3
- componente: air supply hose; air nozzle; air pump; exhaust ducting | ID: p52.t1.r3
- condizioni: see Page 22 | ID: p52.t1.r3
- nota:

### Ramo R52
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser unable to cut or scan workpiece. | ID: p52.t1.r3
- azione:  | tipo:  | ID: p52.t1.r3
- componente:  | ID: p52.t1.r3
- condizioni: Workpiece material beyond machine capability. | ID: p52.t1.r3
- nota:

### Ramo R53
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser kerf too wide, and material is poorly cut. | ID: p52.t1.r3
- azione: Verify mirrors are secure. | tipo: controllo | ID: p52.t1.r3
- azione: Verify the reflective side of the mirrors is facing outward. | tipo: controllo | ID: p52.t1.r3
- azione: Align the laser beam. | tipo: riparazione | ID: p52.t1.r3
- azione: Inspect the focal length. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust the focal length. | tipo: riparazione | ID: p52.t1.r3
- azione: Inspect table parallelism. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust table parallelism. | tipo: riparazione | ID: p52.t1.r3
- componente: mirrors; table | ID: p52.t1.r3
- condizioni: see Pages 61, 57, 36 and 52 | ID: p52.t1.r3
- nota:

### Ramo R54
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser head has vibration or lash (workpiece path shows distortion/overlap). | ID: p52.t1.r3
- azione: Adjust the belts. | tipo: riparazione | ID: p52.t1.r3
- azione: Replace the belts. | tipo: riparazione | ID: p52.t1.r3
- azione: Inspect the linkage, tracks, and guides for loose fasteners or binding. | tipo: controllo | ID: p52.t1.r3
- azione: Adjust the linkage, tracks, and guides. | tipo: riparazione | ID: p52.t1.r3
- azione: Reset the origin. | tipo: riparazione | ID: p52.t1.r3
- componente: belts; linkage; tracks; guides | ID: p52.t1.r3
- condizioni: see Pages 51 and 34; inspect/adjust linkage, tracks and guides for loose fasteners or binding | ID: p52.t1.r3
- nota:

### Ramo R55
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Workpiece buckling or moving. | ID: p52.t1.r3
- azione: Use the honeycomb table for thin workpiece support. | tipo: riparazione | ID: p52.t1.r3
- azione: Use clamps to secure large or irregular workpieces. | tipo: riparazione | ID: p52.t1.r3
- componente: workpiece | ID: p52.t1.r3
- condizioni: honeycomb table for thin workpieces; clamps for large or irregular workpieces | ID: p52.t1.r3
- nota:

### Ramo R56
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser output creating sawtooth pattern on cuts or engravings. | ID: p52.t1.r3
- azione: Increase laser power. | tipo: riparazione | ID: p52.t1.r3
- componente:  | ID: p52.t1.r3
- condizioni: see Page 35; workpiece may contain impurities that ignite and eject particles of molten material | ID: p52.t1.r3
- nota:

### Ramo R57
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Laser tube at fault. | ID: p52.t1.r3
- azione: Replace the laser tube. | tipo: riparazione | ID: p52.t1.r3
- azione: Replace the laser tube power supply. | tipo: riparazione | ID: p52.t1.r3
- componente: laser tube; laser tube power supply | ID: p52.t1.r3
- condizioni: see Page 52 | ID: p52.t1.r3
- nota:

### Ramo R58
- problema: Machine laser has poor cutting or engraving results. | ID: p52.t1.r3
- codice: - | ID: p52.t1.r3
- causa: Transformer, power supply, or controller at fault. | ID: p52.t1.r3
- azione: Inspect the transformer, power supply, or controller. | tipo: controllo | ID: p52.t1.r3
- azione: Replace the transformer, power supply, or controller. | tipo: riparazione | ID: p52.t1.r3
- componente: transformer; power supply; controller | ID: p52.t1.r3
- condizioni: as required | ID: p52.t1.r3
- nota:

### Ramo R59
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: Water chiller system not cooling laser tube; thermal kill switch activates or alarm sounds. | ID: p52.t1.r4
- azione: Inspect the water chiller system. | tipo: controllo | ID: p52.t1.r4
- azione: Replace the water chiller system. | tipo: riparazione | ID: p52.t1.r4
- azione: Reduce ambient temperature of the machine operating environment. | tipo: riparazione | ID: p52.t1.r4
- azione: Add ice to the reservoir. | tipo: riparazione | ID: p52.t1.r4
- azione: Add additional water chilling equipment. | tipo: riparazione | ID: p52.t1.r4
- componente: water chiller system; reservoir | ID: p52.t1.r4
- condizioni: see Page 21; add ice and additional water chilling equipment as required | ID: p52.t1.r4
- nota:

### Ramo R60
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: Air pump, water pump, or exhaust fan have a short. | ID: p52.t1.r4
- azione: Inspect the air pump, water pump, or exhaust fan. | tipo: controllo | ID: p52.t1.r4
- azione: Replace the affected part. | tipo: riparazione | ID: p52.t1.r4
- componente: air pump; water pump; exhaust fan | ID: p52.t1.r4
- condizioni: replace if at fault | ID: p52.t1.r4
- nota:

### Ramo R61
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: One or more laser tube power supply components have failed. | ID: p52.t1.r4
- azione: Replace the laser tube power supply and machine electrical components. | tipo: riparazione | ID: p52.t1.r4
- componente: laser tube power supply; machine electrical components | ID: p52.t1.r4
- condizioni: as required; see Page 63 | ID: p52.t1.r4
- nota:

### Ramo R62
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: Laser tube electrical connections at fault. | ID: p52.t1.r4
- azione: Verify laser tube electrical connections are correct and secure. | tipo: controllo | ID: p52.t1.r4
- componente: laser tube electrical connections | ID: p52.t1.r4
- condizioni:  | ID: p52.t1.r4
- nota:

### Ramo R63
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: Electrical system at fault. | ID: p52.t1.r4
- azione: Test electrical system components. | tipo: controllo | ID: p52.t1.r4
- azione: Replace electrical system components. | tipo: riparazione | ID: p52.t1.r4
- componente: electrical system components | ID: p52.t1.r4
- condizioni: as required; see Page 63 | ID: p52.t1.r4
- nota:

### Ramo R64
- problema: Laser tube inoperative or laser powers down while machine is operating. | ID: p52.t1.r4
- codice: - | ID: p52.t1.r4
- causa: Laser tube at fault. | ID: p52.t1.r4
- azione: Replace the laser tube. | tipo: riparazione | ID: p52.t1.r4
- componente: laser tube | ID: p52.t1.r4
- condizioni: see Page 52 | ID: p52.t1.r4
- nota:


### Ramo R65
- problema: Wires or components are damaged while performing a wiring task. | ID: p64.b9
- codice: - | ID: p64.b9
- causa: non indicata nel manuale | ID: p64.b9
- azione: Replace the damaged wires or components. | tipo: riparazione | ID: p64.b9
- componente: wires; components | ID: p64.b9
- condizioni: if damage is noticed while performing a wiring task | ID: p64.b9
- nota:

### Ramo R66
- problema: Wiring differs from what is shown in the manual. | ID: p64.b3
- codice: - | ID: p64.b3
- causa: non indicata nel manuale | ID: p64.b3
- azione: Call Technical Support at (570) 546-9663 for assistance. | tipo: assistenza | ID: p64.b3
- componente: wiring | ID: p64.b3
- condizioni: before making any changes; gather the machine serial number and manufacture date before calling | ID: p64.b3
- nota:
