# Revisione della precisione del grafo

108 affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi
cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi
al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `chiave_non_aprire_2.json`:
contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.

Revisore: 
Data: 
Tempo totale impiegato (minuti): 

### R001 · Haas vertical mill (2023 operator's manual), pagina 99

**Il manuale dice:**

> In certain cases the pressure against the part may not have been relieved by the Safe Run back-off. In the worse case, an additional crash may be generated after you have reset the alarm. If this happens, turn Safe Run off and jog the axis away from the crash location.

**Il grafo afferma:** «Additional crash after alarm reset» **può indicare la causa** «Pressure against the part not relieved by Safe Run back-off»

- Giudizio: `?`
- Nota: 

### R002 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Incorrect drive roll orientation or alignment» **si affronta con** «Check drive roll orientation and alignment» (controllo o test)

Contesto: [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If you do not understand the test procedures or cannot perform tests or repairs safely, contact the Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs may endanger the technician and machine operator and invalidate the factory warranty; observe the manual's safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R003 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump does not start up. | Motor incorrectly connected. Pressure switch is defective. Oil is too thick. Motor defective. Pump has seized: defective rotors, bearings or toothed gears. | Connect motor correctly. 4 Replace the pressure switch. 4 Exchange the oil or warm up oil and pump. 6 Replace the motor. 4 Atlas Copco Service. - | .4 .4 .3 .5

**Il grafo afferma:** «Pump does not start up» **può indicare la causa** «Motor defective»

- Giudizio: `?`
- Nota: 

### R004 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> Plugged hose, or hose too small | Relieve pressure, page 6. Flush hose with clean water, or try a 1-1/4 in. hose.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Plugged hose, or hose too small»

- Giudizio: `?`
- Nota: 

### R005 · ABB ACS580-01 variable speed drive, pagina 385, 386

**Il manuale dice:**

> If warning the A7AB Extension I/O configuration failure is shown,

> • make sure that the value of parameter 15.02 is CHDI-01.

> Warning A7AB Extension I/O configuration failure.

**Il grafo afferma:** «Incorrect extension I/O configuration» **si affronta con** «Check that parameter 15.02 is CHDI-01» (controllo o test)

Contesto: [if] If warning A7AB is shown

- Giudizio: `?`
- Nota: 

### R006 · Haas vertical mill (2023 operator's manual), pagina 144

**Il manuale dice:**

> Low Voltage (Warning) | The PFDM detects low incoming voltage. If the condition continues, the machine cannot continue to operate.

> Low Voltage (Alarm) | The Power Fault Detect Module (PDFM) detects incoming voltage that is too low to operate. The machine will not operate until the condition is corrected.

**Il grafo afferma:** «Low Voltage Warning» **può indicare la causa** «Incoming voltage is low»

- Giudizio: `?`
- Nota: 

### R007 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «Material too thick» **si affronta con** «Thin the material»

- Giudizio: `?`
- Nota: 

### R008 · Graco GTX 2000EX texture sprayer, pagina 9

**Il manuale dice:**

> Pattern too coarse | Material too thick | Thin material. Material must be mixed thoroughly to a consistency that imme- diately folds back in as you draw your finger through the surface of the mate- rial.

**Il grafo afferma:** «Pattern too coarse» **può indicare la causa** «Material too thick»

- Giudizio: `?`
- Nota: 

### R009 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> Nozzle too small | Increase nozzle size.

**Il grafo afferma:** «Speed of application too slow» **può indicare la causa** «Nozzle too small»

- Giudizio: `?`
- Nota: 

### R010 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 010» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R011 · ABB ACS580-01 variable speed drive, pagina 168, 169

**Il manuale dice:**

> WARNING! Obey the safety instructions of the drive. If you ignore them, injury or death, or damage to the equipment can occur. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.

> 1. Do the steps in section Electrical safety precautions (page 22) before you start the work.

> 2. Make sure that the motor cable is disconnected from the drive output terminals.

**Il grafo afferma:** «Moisture inside the motor» **si affronta con** «Measure the motor insulation resistance again» (controllo o test)

Contesto: [expected] For an ABB motor, insulation resistance must be more than 100 Mohm at 25 °C [77 °F]; [order] After drying the motor; [prerequisite] Do the electrical safety precautions before starting the work, and disconnect the motor cable from the drive output terminals before measuring.; [warning] Obey the drive safety instructions. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.

- Giudizio: `?`
- Nota: 

### R012 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

> Panel has no power | Green | Drive functioning normally. Connection between the drive and control panel may be faulty or lost, or the panel and drive may be incompatible. Check the control panel display. | Green | Blinking: Active warning in the drive Flickering: Data transferred between the PC tool and drive through the USB connection of the control panel

**Il grafo afferma:** «Incompatible control panel and drive» **si affronta con** «Check the control-panel display» (controllo o test)

- Giudizio: `?`
- Nota: 

### R013 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 003» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R014 · Haas vertical mill (2023 operator's manual), pagina 99

**Il manuale dice:**

> In certain cases the pressure against the part may not have been relieved by the Safe Run back-off. In the worse case, an additional crash may be generated after you have reset the alarm. If this happens, turn Safe Run off and jog the axis away from the crash location.

**Il grafo afferma:** «Pressure against the part not relieved by Safe Run back-off» **riguarda il componente** «axis»

- Giudizio: `?`
- Nota: 

### R015 · Haas vertical mill (2023 operator's manual), pagina 144

**Il manuale dice:**

> Low Voltage (Warning) | The PFDM detects low incoming voltage. If the condition continues, the machine cannot continue to operate.

> Low Voltage (Alarm) | The Power Fault Detect Module (PDFM) detects incoming voltage that is too low to operate. The machine will not operate until the condition is corrected.

**Il grafo afferma:** «Incoming voltage too low to operate» **si affronta con** «Correct the low incoming-voltage condition» (riparazione)

- Giudizio: `?`
- Nota: 

### R016 · Graco GTX 2000EX texture sprayer, pagina 8, 9

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Pattern too fine or too much overspray | Fluid delivery too low | Increase nozzle size.

> Pattern too fine or too much overspray | Fluid delivery too low | Increase air pressure to pump, or decrease air to gun at gun fitting and/or regulator.

**Il grafo afferma:** «Fluid delivery too low» **si affronta con** «Turn fluid knob out on gun» (riparazione)

Contesto: [prerequisite] Before performing any troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R017 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

**Il grafo afferma:** «Pump is distorted, making housing-to-rotor clearance too small» **riguarda il componente** «Pump housing and rotors»

- Giudizio: `?`
- Nota: 

### R018 · Graco GTX 2000EX texture sprayer, pagina 8, 9

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Pattern too coarse | Fluid delivery too high | Decrease air pressure to pump, or increase air to gun at gun fitting and/or regulator.

> Pattern too coarse | Fluid delivery too high | Turn fluid knob in on gun. See Spray Techniques in Operation Manual 309915.

**Il grafo afferma:** «Fluid delivery too high» **si affronta con** «Decrease pump air pressure or increase air to gun at gun fitting and/or regulator» (riparazione)

Contesto: [prerequisite] Before performing any troubleshooting procedures, follow the Pressure Relief procedure on page 6.; [prerequisite] Before performing troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R019 · Haas vertical mill (2023 operator's manual), pagina 97

**Il manuale dice:**

> Press SHIFT + F4 to display the last line of G-code that generated the error.

> Locate the Last Program Error

> Starting in software version 100.19.000.1100 the control can find the last error in a program.

**Il grafo afferma:** «Unspecified cause of program error» **si affronta con** «Display the last G-code line that generated the error» (controllo o test)

Contesto: [if] Starting in software version 100.19.000.1100; [prerequisite] Press SHIFT + F4

- Giudizio: `?`
- Nota: 

### R020 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> APC E-Stop | [EMERGENCY STOP] on the pallet changer has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «Pallet changer emergency stop pressed» **si affronta con** «Release pallet changer emergency stop»

- Giudizio: `?`
- Nota: 

### R021 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

**Il grafo afferma:** «Overtemperature warnings and faults» **può indicare la causa** «Heatsink not clean»

- Giudizio: `?`
- Nota: 

### R022 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Do not operate with panels removed. Before servicing or installing kits, disconnect machine from power and wait a minimum of two minutes prior to removing sheet metal.

**Il grafo afferma:** «Incorrect input voltage» **si affronta con** «Contact a Lincoln Authorized Field Service Facility if the problem persists» (contattare l'assistenza)

Contesto: [if] If all recommended possible areas of misadjustment have been checked and the problem persists.; [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If test procedures are not understood or tests/repairs cannot be performed safely, contact the local Lincoln Authorized Field Service Facility for troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel; unauthorized repairs may endanger the technician and operator and invalidate the factory warranty. Observe all safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R023 · ABB ACS580-01 variable speed drive, pagina 365

**Il manuale dice:**

> The diagnostics of the Safe torque off function cross-compare the status of the two STO channels. In case the channels are not in the same state, a fault reaction function is performed and the drive trips on an “STO hardware failure” fault. An attempt to use the STO in a non-redundant manner, for example activating only one channel, will trigger the same reaction.

**Il grafo afferma:** «STO used in a non-redundant manner» **riguarda il componente** «Safe torque off channels»

- Giudizio: `?`
- Nota: 

### R024 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

**Il grafo afferma:** «Not enough air pressure to pump» **si affronta con** «Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.»

- Giudizio: `?`
- Nota: 

### R025 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump uses too much power 15*16*18*19*20*23*25*27*28*31*33*34*35*37*38

> 34. The operating conditions of the installation do not agree with the data specified when the pump was purchased.

**Il grafo afferma:** «Pump uses too much power» **può indicare la causa** «Installation operating conditions differ from purchase specifications»

- Giudizio: `?`
- Nota: 

### R026 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • Keep all safety glass and machine windows clean to allow proper viewing of the machine during operations.

**Il grafo afferma:** «Safety glass and machine windows are not clean enough for proper viewing» **riguarda il componente** «Safety glass and machine windows»

- Giudizio: `?`
- Nota: 

### R027 · Graco GTX 2000EX texture sprayer, pagina 8, 9

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Speed of application too slow | Nozzle too small | Increase nozzle size.

> Pattern too fine or too much overspray | Fluid delivery too low | Increase nozzle size.

**Il grafo afferma:** «Nozzle too small» **si affronta con** «Increase nozzle size» (riparazione)

Contesto: [prerequisite] Before performing any troubleshooting procedures, follow the Pressure Relief procedure on page 6.; [prerequisite] Before performing troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R028 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 44

**Il manuale dice:**

> Oil in the pump chamber.

> il in the pump amber. | Oil level is too high. Oil is ejected from the system. Pump is not standing horizontally. Pump has a gas leak towards the outside. Pump has an internal leak. Piston rings are defective. | Drain the oil down to the correct level. Check system. Place the pump correctly. Check to see that the oil fill and oil drain plugs are correctly seated, if required replace gaskets. Replace the O-ring of the gear cover. Atlas Copco Service. Atlas Copco Service. | 6.3 - 4.1 6.3 - -

**Il grafo afferma:** «Oil in the pump chamber» **può indicare la causa** «Oil is ejected from the system»

- Giudizio: `?`
- Nota: 

### R029 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • Inspect the door interlock, verify the door interlock key is not bent, misaligned, and that all fasteners are installed.

**Il grafo afferma:** «Door interlock fasteners missing» **si affronta con** «Inspect the door interlock key for bending or misalignment and verify all fasteners are installed» (controllo o test)

- Giudizio: `?`
- Nota: 

### R030 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

> 3. Blow dry, clean and oil-free compressed air from bottom to top and simultaneously use a vacuum cleaner at the air outlet to trap the dust. If there is a risk of dust entering adjoining equipment, do the cleaning in another room.

**Il grafo afferma:** «Heatsink not clean» **si affronta con** «Clean the heatsink»

- Giudizio: `?`
- Nota: 

### R031 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump uses too much power 15*16*18*19*20*23*25*27*28*31*33*34*35*37*38

> 35. The shaft seal may be incorrectly installed, or the stuffing box has not been packed correctly.

**Il grafo afferma:** «Pump uses too much power» **può indicare la causa** «Shaft seal incorrectly installed or stuffing box incorrectly packed»

- Giudizio: `?`
- Nota: 

### R032 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> Capacitor failure is usually followed by damage to the unit and an input cable fuse failure, or a fault trip. If you think that any capacitors in the drive have failed, contact ABB.

**Il grafo afferma:** «Input cable fuse failure after capacitor failure» **può indicare la causa** «Failed drive capacitors»

- Giudizio: `?`
- Nota: 

### R033 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 25. The casing and impeller wear rings may be excessively worn.

**Il grafo afferma:** «Casing and impeller wear rings excessively worn» **riguarda il componente** «Casing and impeller wear rings»

- Giudizio: `?`
- Nota: 

### R034 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Install the pump at a suitable place or ensure a sufficient flow of cooling air. Check the pressure levels within the system. Check the pressure levels within the system. Check system. Clean pumping chamber. Affix and connect the pump free of tension. Change oil. Drain oil down to the correct level. Top up oil to the correct level. Drain oil, fill in correct oil. Atlas Copco Service. Clean the valve or have it repaired.

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

**Il grafo afferma:** «Pressure balance line valve does not open» **si affronta con** «Clean or have the pressure balance line valve repaired» (riparazione)

- Giudizio: `?`
- Nota: 

### R035 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Major physical or electrical damage» **si affronta con** «Contact an Authorized Field Service Facility about physical or electrical damage» (contattare l'assistenza)

Contesto: [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If you do not understand the test procedures or cannot perform tests or repairs safely, contact the Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs may endanger the technician and machine operator and invalidate the factory warranty; observe the manual's safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R036 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

**Il grafo afferma:** «Speed of application too slow» **può indicare la causa** «Not enough air pressure to pump»

- Giudizio: `?`
- Nota: 

### R037 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> High Air (Warning) | The air pressure to the machine is too high to reliably operate pneumatic systems. Correct this condition to prevent damage to or incorrect operation of pneumatic systems. You may need to install a regulator at the machine’s air input.

**Il grafo afferma:** «Air pressure too high» **si affronta con** «Correct high air pressure condition»

- Giudizio: `?`
- Nota: 

### R038 · Graco GTX 2000EX texture sprayer, pagina 9

**Il manuale dice:**

> Air pressure at gun too high | Decrease air to gun at gun fitting and/or regulator.

> Pattern too fine or too much overspray | Material too thin | Thicken material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «Pattern too fine or too much overspray» **può indicare la causa** «Air pressure at gun too high»

- Giudizio: `?`
- Nota: 

### R039 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Unstable arc and poor starting» **può indicare la causa** «Drive rolls have improper orientation or alignment»

- Giudizio: `?`
- Nota: 

### R040 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> Auxiliary E-Stop | [EMERGENCY STOP] on an auxiliary device has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «Auxiliary device emergency stop pressed» **riguarda il componente** «auxiliary device»

- Giudizio: `?`
- Nota: 

### R041 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «Material too thick» **si affronta con** «Thin and thoroughly mix the material to a consistency that immediately folds back when finger-drawn» (riparazione)

Contesto: [prerequisite] Before performing any troubleshooting procedures, follow the Pressure Relief procedure on page 6.; [prerequisite] Before performing troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R042 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 013» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R043 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 2. The pump suction line has not been completely primed.

> Pump stops delivering liquid after start-up 2*3*4*5*6*7*8*9*10*11*12*13*22*23*24*34

**Il grafo afferma:** «Pump stops delivering liquid after start-up» **può indicare la causa** «Pump suction line not completely primed»

- Giudizio: `?`
- Nota: 

### R044 · Haas vertical mill (2023 operator's manual), pagina 99

**Il manuale dice:**

> In certain cases the pressure against the part may not have been relieved by the Safe Run back-off. In the worse case, an additional crash may be generated after you have reset the alarm. If this happens, turn Safe Run off and jog the axis away from the crash location.

**Il grafo afferma:** «Pressure against the part not relieved by Safe Run back-off» **si affronta con** «Turn Safe Run off»

- Giudizio: `?`
- Nota: 

### R045 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 34. The operating conditions of the installation do not agree with the data specified when the pump was purchased.

> Pump does not deliver any liquid at start-up 1*2*3*4*5*6*7*8*9*10*11*14*16*17*22*23*24*34

**Il grafo afferma:** «Pump does not deliver liquid at start-up» **può indicare la causa** «Installation operating conditions differ from purchase specifications»

- Giudizio: `?`
- Nota: 

### R046 · Graco GTX 2000EX texture sprayer, pagina 8, 9

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Pattern too coarse | Fluid delivery too high | Turn fluid knob in on gun. See Spray Techniques in Operation Manual 309915.

> Pattern too coarse | Fluid delivery too high | Decrease nozzle size.

**Il grafo afferma:** «Fluid delivery too high» **si affronta con** «Turn the fluid knob in on the gun; see Spray Techniques in Operation Manual 309915» (riparazione)

Contesto: [prerequisite] Before performing troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R047 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump is too loud. | Motor defective. Distances between housing and rotors is too small due to - contamination - distortion of the pump Bearing or gear damage. Pistons make contact with the housing. Rotor is running untrue. Oil slinger disc makes contact with the gear housing or the oil pipe. Oil pump is blocked or defective. | Replace the motor. 4 Clean pumping chamber. 6 Affix and connect the pump free of tensions. 4 Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service. - Atlas Copco Service, shutdown pump - immediately. | .5 .5 .1/4.5

**Il grafo afferma:** «Pump is too loud» **può indicare la causa** «Pistons contact the housing»

- Giudizio: `?`
- Nota: 

### R048 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Plugged gun or nozzle | Relieve Pressure, page 6. Remove gun from material hose, and cycle pump. NOTE: A plugged gun or nozzle may cause the hose and pump to plug. If necessary, flush hose and pump with clean water before cycling material through the hose with the gun removed.

**Il grafo afferma:** «Plugged gun or nozzle» **riguarda il componente** «Gun and nozzle»

- Giudizio: `?`
- Nota: 

### R049 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Motor protection switch trips. | Motor defective. Motor protection switch incorrectly set. Pump seizes mechanically. | Replace the motor. 4 Set Motor protection correctly. 4 Atlas Copco Service. - | .5 .3

**Il grafo afferma:** «Motor protection switch trips» **può indicare la causa** «Pump seizes mechanically»

- Giudizio: `?`
- Nota: 

### R050 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Material too thick»

- Giudizio: `?`
- Nota: 

### R051 · Graco GTX 2000EX texture sprayer, pagina 9

**Il manuale dice:**

> Fluid delivery too high | Decrease nozzle size.

**Il grafo afferma:** «Fluid delivery too high» **si affronta con** «Decrease nozzle size.»

- Giudizio: `?`
- Nota: 

### R052 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «Thermostat tripped due to overheating» **si affronta con** «Let machine cool; weld at lower duty cycle»

- Giudizio: `?`
- Nota: 

### R053 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> The DC link of the drive contains several electrolytic capacitors. Operating time, load, and surrounding air temperature have an effect on the life of the capacitors. Capacitor life can be extended by decreasing the surrounding air temperature.

> Capacitor failure is usually followed by damage to the unit and an input cable fuse failure, or a fault trip. If you think that any capacitors in the drive have failed, contact ABB.

> The capacitors must be reformed if the drive has not been powered (either in storage or unused) for a year or more. The manufacturing date is on the type designation label. For information on reforming the capacitors, see Capacitor reforming instructions (3BFE64059629 [English]) in the ABB Library (https://library.abb.com/en).

**Il grafo afferma:** «Drive capacitors require reforming» **riguarda il componente** «DC-link electrolytic capacitors»

- Giudizio: `?`
- Nota: 

### R054 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

**Il grafo afferma:** «Heatsink not clean» **riguarda il componente** «Drive module heatsink»

- Giudizio: `?`
- Nota: 

### R055 · ABB ACS580-01 variable speed drive, pagina 169

**Il manuale dice:**

> 3. Measure the insulation resistance between each phase conductor and the protective earth conductor. Use a measuring voltage of 1000 V DC. The insulation resistance of an ABB motor must be more than 100 Mohm (reference value at 25 °C [77 °F]). For the insulation resistance of other motors, refer to the manufacturer’s instructions.

> Moisture inside the motor reduces the insulation resistance. If you think that there is moisture in the motor, dry the motor and do the measurement again.

**Il grafo afferma:** «Motor insulation resistance is reduced» **può indicare la causa** «Moisture inside the motor»

- Giudizio: `?`
- Nota: 

### R056 · ABB ACS580-01 variable speed drive, pagina 168, 169

**Il manuale dice:**

> WARNING! Obey the safety instructions of the drive. If you ignore them, injury or death, or damage to the equipment can occur. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.

> 1. Do the steps in section Electrical safety precautions (page 22) before you start the work.

> 2. Make sure that the motor cable is disconnected from the drive output terminals.

**Il grafo afferma:** «Moisture inside the motor» **si affronta con** «Dry the motor» (riparazione)

Contesto: [if] If moisture in the motor is suspected; [prerequisite] Do the electrical safety precautions before starting the work, and disconnect the motor cable from the drive output terminals before measuring.; [warning] Obey the drive safety instructions. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.

- Giudizio: `?`
- Nota: 

### R057 · Haas vertical mill (2023 operator's manual), pagina 19, 20

**Il manuale dice:**

> • If the person is pinched or entangled the machine should be powered off; then the machine axes can be moved by use of a large external force in the direction required to free the person.

> • Use lifting equipment or get assistance for lifting heavy and awkward parts.

> • Of a tool and material/part - Close the doors, press [RESET] to clear and displayed alarms. Jog the axis so the tool and material are clear.

**Il grafo afferma:** «Tool and material or part blockage» **si affronta con** «Jog the axis to clear the tool and material» (riparazione)

Contesto: [order] After closing the doors and pressing RESET; [prerequisite] Use lifting equipment or get assistance when lifting heavy and awkward parts.; [warning] During normal operation, keep the door closed and guards in place on non-enclosed machines.; [warning] For part loading and unloading, close the door after the task and press CYCLE START to begin automatic motion.; [warning] If a person is pinched or entangled, power off the machine; then the machine axes can be moved with a large external force in the direction required to free the person.; [warning] Use lifting equipment or get assistance when lifting heavy and awkward parts.; [warning] When machining job set-up is complete, turn the set-up key to lock out set-mode and remove the key.

- Giudizio: `?`
- Nota: 

### R058 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> Remote Jog Handle-XL (RJH-XL) E-Stop | [EMERGENCY STOP] on the RJH-XL has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «RJH-XL emergency stop pressed» **si affronta con** «Release RJH-XL emergency stop»

- Giudizio: `?`
- Nota: 

### R059 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Communication error between display P.C. board and power control board» **si affronta con** «Contact service facility»

- Giudizio: `?`
- Nota: 

### R060 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> Periodic inspection of machine safety features: • Inspect door interlock mechanism for proper fit and function.

> • If the alarms do not reset or you are unable to clear a blockage, contact your Haas Factory Outlet (HFO) for assistance. Follow these guidelines when you work with the machine: • Normal operation - Keep the door closed and guards in place (for non-enclosed machines) while the machine operates.

> • Part loading and unloading – An operator opens the door, completes the task, closes the door, and then presses [CYCLE START] (starting automatic motion).

**Il grafo afferma:** «Door interlock mechanism does not fit or function properly» **si affronta con** «Inspect the door interlock mechanism for proper fit and function» (controllo o test)

Contesto: [warning] Before entering the enclosure for maintenance or machine cleaning, press EMERGENCY STOP or POWER OFF.; [warning] During normal operation, keep the door closed and guards in place on non-enclosed machines.; [warning] For part loading and unloading, close the door after the task and press CYCLE START to begin automatic motion.; [warning] When machining job set-up is complete, turn the set-up key to lock out set-mode and remove the key.

- Giudizio: `?`
- Nota: 

### R061 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Unstable arc and poor starting» **può indicare la causa** «Incorrect gas or flow rate for the process»

Contesto: [if] For MIG only.

- Giudizio: `?`
- Nota: 

### R062 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump is too loud. | Motor defective. Distances between housing and rotors is too small due to - contamination - distortion of the pump Bearing or gear damage. Pistons make contact with the housing. Rotor is running untrue. Oil slinger disc makes contact with the gear housing or the oil pipe. Oil pump is blocked or defective. | Replace the motor. 4 Clean pumping chamber. 6 Affix and connect the pump free of tensions. 4 Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service, shutdown pump - immediately. Atlas Copco Service. - Atlas Copco Service, shutdown pump - immediately. | .5 .5 .1/4.5

**Il grafo afferma:** «Pump is too loud» **può indicare la causa** «Oil slinger disc contacts gear housing or oil pipe»

- Giudizio: `?`
- Nota: 

### R063 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 9. The suction valve is closed or only partially open.

> Pump does not deliver any liquid at start-up 1*2*3*4*5*6*7*8*9*10*11*14*16*17*22*23*24*34

**Il grafo afferma:** «Pump does not deliver liquid at start-up» **può indicare la causa** «Suction valve closed or partially open»

- Giudizio: `?`
- Nota: 

### R064 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Il grafo afferma:** «Active fault in another drive on the panel bus» **si affronta con** «Check the control-panel display» (controllo o test)

- Giudizio: `?`
- Nota: 

### R065 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Unstable arc and poor starting» **può indicare la causa** «Incorrect liner size»

- Giudizio: `?`
- Nota: 

### R066 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

**Il grafo afferma:** «Cooling air flow is obstructed» **riguarda il componente** «Pump cooling air flow»

- Giudizio: `?`
- Nota: 

### R067 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Install the pump at a suitable place or ensure a sufficient flow of cooling air. Check the pressure levels within the system. Check the pressure levels within the system. Check system. Clean pumping chamber. Affix and connect the pump free of tension. Change oil. Drain oil down to the correct level. Top up oil to the correct level. Drain oil, fill in correct oil. Atlas Copco Service. Clean the valve or have it repaired.

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

**Il grafo afferma:** «Wrong oil filled» **si affronta con** «Drain oil and fill in the correct oil» (riparazione)

- Giudizio: `?`
- Nota: 

### R068 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> Plugged gun or nozzle | Relieve Pressure, page 6. Remove gun from material hose, and cycle pump. NOTE: A plugged gun or nozzle may cause the hose and pump to plug. If necessary, flush hose and pump with clean water before cycling material through the hose with the gun removed.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Plugged gun or nozzle»

- Giudizio: `?`
- Nota: 

### R069 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 21. The pump is operating at too low a rate of flow. The discharge valve may be throttled too much.

**Il grafo afferma:** «Pump operating at too low a flow rate; discharge valve may be throttled too much» **riguarda il componente** «Discharge valve»

- Giudizio: `?`
- Nota: 

### R070 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 44

**Il manuale dice:**

> Pump is losing oil. Oil leak is apparent:

> ump is losing oil. | Oil leak is apparent: Oil drain plug is leaky. Oil level glasses leaky. Gear cover is leaky. Leaky coupling flange No oil leak is apparent: See malfunction “Oil in the pump chamber”. | Drain oil, firmly screw in a new oil drain plug with the gasket, fill in correct oil quantity. Atlas Copco Service. Replace the O-ring of the gear cover. Replace the O-ring of the coupling flange. See malfunction “Oil in the pump chamber”. | 6.3 - - -

**Il grafo afferma:** «Pump is losing oil» **può indicare la causa** «Coupling flange is leaky»

Contesto: [if] Oil leak is apparent

- Giudizio: `?`
- Nota: 

### R071 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Unspecified cause of communication error between display and power control boards» **riguarda il componente** «Display P.C. board»

- Giudizio: `?`
- Nota: 

### R072 · Graco GTX 2000EX texture sprayer, pagina 8, 9

**Il manuale dice:**

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> Pattern too coarse | Fluid delivery too high | Decrease air pressure to pump, or increase air to gun at gun fitting and/or regulator.

**Il grafo afferma:** «Pattern too coarse» **può indicare la causa** «Material too thick»

- Giudizio: `?`
- Nota: 

### R073 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> Pendant E-Stop | [EMERGENCY STOP] on the pendant has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «Pendant emergency stop pressed» **riguarda il componente** «pendant»

- Giudizio: `?`
- Nota: 

### R074 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Communication error between display P.C. board and power control board» **si affronta con** «Cycle power to machine»

- Giudizio: `?`
- Nota: 

### R075 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Pump in need of repair | See texture pump instruction manual 308479.

> No material output from pump | Damaged checkballs or seats | Replace checkballs or seats.

> Pump stops pumping | Stalled pump | Shut down system. Relieve Pressure, page 6. Restart.

**Il grafo afferma:** «Pump in need of repair» **riguarda il componente** «Pump»

- Giudizio: `?`
- Nota: 

### R076 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> Speed of application too slow | Nozzle too small | Increase nozzle size.

**Il grafo afferma:** «Speed of application too slow» **può indicare la causa** «Material too thick»

- Giudizio: `?`
- Nota: 

### R077 · Haas vertical mill (2023 operator's manual), pagina 144

**Il manuale dice:**

> Robot Battery is Low | Robot Battery is Low. Please replace the pulse coder batteries as soon as possible. Do NOT turn off the robot, otherwise it may require remastering. Reference 9156.062 ROBOT COMMAND FAILED SRVO-062 BZAL alarm in service documentation for more information.

**Il grafo afferma:** «Robot Battery is Low» **può indicare la causa** «Pulse coder batteries low»

- Giudizio: `?`
- Nota: 

### R078 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump does not start up. | Motor incorrectly connected. Pressure switch is defective. Oil is too thick. Motor defective. Pump has seized: defective rotors, bearings or toothed gears. | Connect motor correctly. 4 Replace the pressure switch. 4 Exchange the oil or warm up oil and pump. 6 Replace the motor. 4 Atlas Copco Service. - | .4 .4 .3 .5

**Il grafo afferma:** «Pump does not start up» **può indicare la causa** «Pressure switch is defective»

- Giudizio: `?`
- Nota: 

### R079 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Material too thick»

- Giudizio: `?`
- Nota: 

### R080 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump does not deliver any liquid at start-up 1*2*3*4*5*6*7*8*9*10*11*14*16*17*22*23*24*34

> 16. Pump rotation wrong or impeller installed backwards.

**Il grafo afferma:** «Pump does not deliver liquid at start-up» **può indicare la causa** «Pump rotation wrong or impeller installed backwards»

- Giudizio: `?`
- Nota: 

### R081 · ABB ACS580-01 variable speed drive, pagina 385, 386

**Il manuale dice:**

> If warning the A7AB Extension I/O configuration failure is shown,

> • make sure that the value of parameter 15.02 is CHDI-01.

> Warning A7AB Extension I/O configuration failure.

**Il grafo afferma:** «Extension I/O configuration failure» **(codice) indica la causa** «Parameter 15.02 is not set to CHDI-01»

- Giudizio: `?`
- Nota: 

### R082 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Circuit breaker is not reset» **si affronta con** «Contact Lincoln service if the no-feed, no-output, and no-gas problem persists» (contattare l'assistenza)

Contesto: [if] If all recommended possible areas of misadjustment have been checked and the problem persists.; [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If test procedures are not understood or tests/repairs cannot be performed safely, contact the local Lincoln Authorized Field Service Facility for troubleshooting assistance before proceeding.; [warning] If you do not understand the test procedures or cannot perform tests or repairs safely, contact the Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs may endanger the technician and machine operator and invalidate the factory warranty; observe the manual's safety notes and precautions to avoid electrical shock.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel; unauthorized repairs may endanger the technician and operator and invalidate the factory warranty. Observe all safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R083 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> Remote Jog Handle-XL (RJH-XL) E-Stop | [EMERGENCY STOP] on the RJH-XL has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «Remote Jog Handle-XL (RJH-XL) E-Stop» **può indicare la causa** «RJH-XL emergency stop pressed»

- Giudizio: `?`
- Nota: 

### R084 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 24. The impeller may be damaged.

> Discharge pressure is too high 4*14*16*18*20*22*23*24*25*26*34

**Il grafo afferma:** «Discharge pressure is too high» **può indicare la causa** «Impeller damaged»

- Giudizio: `?`
- Nota: 

### R085 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

> No material output from pump | Damaged checkballs or seats | Replace checkballs or seats.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Plugged gun or nozzle»

- Giudizio: `?`
- Nota: 

### R086 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «No wire feed, weld output, or gas flow when the gun trigger is pulled; fan operates normally» **può indicare la causa** «Obstructed airflow»

- Giudizio: `?`
- Nota: 

### R087 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «Thermostat tripped due to overheating» **si affronta con** «Let machine cool»

- Giudizio: `?`
- Nota: 

### R088 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «No wire feed, weld output or gas flow; fan operates normally» **può indicare la causa** «Thermostat tripped due to overheating»

- Giudizio: `?`
- Nota: 

### R089 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • Of the chip conveyor - Follow the cleaning instructions on the Haas service site (go to www.haascnc.com click on the Service tab). If necessary, close the doors and reverse the conveyor so the jammed part or material is accessible, and remove.

**Il grafo afferma:** «Chip conveyor jammed by a part or material» **riguarda il componente** «Chip conveyor»

- Giudizio: `?`
- Nota: 

### R090 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 7. An entry of air past the shaft seal into the pump has occurred.

> 35. The shaft seal may be incorrectly installed, or the stuffing box has not been packed correctly.

**Il grafo afferma:** «Shaft seal incorrectly installed or stuffing box incorrectly packed» **riguarda il componente** «Shaft seal»

- Giudizio: `?`
- Nota: 

### R091 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Do not operate with panels removed. Before servicing or installing kits, disconnect machine from power and wait a minimum of two minutes prior to removing sheet metal.

**Il grafo afferma:** «Clogged cable liner or contact tip» **si affronta con** «Contact a Lincoln Authorized Field Service Facility if the problem persists» (contattare l'assistenza)

Contesto: [if] If all recommended possible areas of misadjustment have been checked and the problem persists.; [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If test procedures are not understood or tests/repairs cannot be performed safely, contact the local Lincoln Authorized Field Service Facility for troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel; unauthorized repairs may endanger the technician and operator and invalidate the factory warranty. Observe all safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R092 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 5. There are air pockets in the suction line.

> Pump stops delivering liquid after start-up 2*3*4*5*6*7*8*9*10*11*12*13*22*23*24*34

**Il grafo afferma:** «Pump stops delivering liquid after start-up» **può indicare la causa** «Air pockets in suction line»

- Giudizio: `?`
- Nota: 

### R093 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Faulty gun trigger connections» **riguarda il componente** «Gun trigger connections»

- Giudizio: `?`
- Nota: 

### R094 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> Pendant E-Stop | [EMERGENCY STOP] on the pendant has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «Pendant emergency stop pressed» **si affronta con** «Release pendant emergency stop»

- Giudizio: `?`
- Nota: 

### R095 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Gun tip is worn, damaged, or the wrong size» **si affronta con** «Replace the gun tip» (riparazione)

Contesto: [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If test procedures are not understood or tests/repairs cannot be performed safely, contact the local Lincoln Authorized Field Service Facility for troubleshooting assistance before proceeding.; [warning] If you do not understand the test procedures or cannot perform tests or repairs safely, contact the Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs may endanger the technician and machine operator and invalidate the factory warranty; observe the manual's safety notes and precautions to avoid electrical shock.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel; unauthorized repairs may endanger the technician and operator and invalidate the factory warranty. Observe all safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R096 · Haas vertical mill (2023 operator's manual), pagina 142

**Il manuale dice:**

> Dirty TSC/HPFC Filter | Clean the Through-Spindle Coolant or High-Pressure Flood Coolant filter.

**Il grafo afferma:** «Through-Spindle Coolant or High-Pressure Flood Coolant filter is dirty» **si affronta con** «Clean the Through-Spindle Coolant or High-Pressure Flood Coolant filter» (riparazione)

- Giudizio: `?`
- Nota: 

### R097 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • Keep all safety glass and machine windows clean to allow proper viewing of the machine during operations.

> • If the alarms do not reset or you are unable to clear a blockage, contact your Haas Factory Outlet (HFO) for assistance. Follow these guidelines when you work with the machine: • Normal operation - Keep the door closed and guards in place (for non-enclosed machines) while the machine operates.

> • Part loading and unloading – An operator opens the door, completes the task, closes the door, and then presses [CYCLE START] (starting automatic motion).

**Il grafo afferma:** «Safety glass or machine windows are not clean enough for proper viewing» **si affronta con** «Keep safety glass and machine windows clean for proper viewing» (riparazione)

Contesto: [warning] Before entering the enclosure for maintenance or machine cleaning, press EMERGENCY STOP or POWER OFF.; [warning] During normal operation, keep the door closed and guards in place on non-enclosed machines.; [warning] For part loading and unloading, close the door after the task and press CYCLE START to begin automatic motion.; [warning] When machining job set-up is complete, turn the set-up key to lock out set-mode and remove the key.

- Giudizio: `?`
- Nota: 

### R098 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump runs rough and noisily 2*3*4*5*6*7*8*9*10*11*15*17*18*21*23*24*27*28*29*30*31*32*33*34*40

> 24. The impeller may be damaged.

**Il grafo afferma:** «Pump runs rough and noisily» **può indicare la causa** «Impeller damaged»

- Giudizio: `?`
- Nota: 

### R099 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «No wire feed, weld output or gas flow when gun trigger is pulled; fan operates normally» **può indicare la causa** «Thermostat tripped due to overheating»

- Giudizio: `?`
- Nota: 

### R100 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «Material too thick» **si affronta con** «Mix material thoroughly»

- Giudizio: `?`
- Nota: 

### R101 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> No material output from pump | Damaged checkballs or seats | Replace checkballs or seats.

> Pump stops pumping | Stalled pump | Shut down system. Relieve Pressure, page 6. Restart.

> Pump stops pumping | Stalled pump | Contact an authorized Graco service center.

**Il grafo afferma:** «Stalled pump» **riguarda il componente** «Pump»

- Giudizio: `?`
- Nota: 

### R102 · ABB ACS580-01 variable speed drive, pagina 168, 169

**Il manuale dice:**

> WARNING! Obey the safety instructions of the drive. If you ignore them, injury or death, or damage to the equipment can occur. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.

> 1. Do the steps in section Electrical safety precautions (page 22) before you start the work.

> 2. Make sure that the motor cable is disconnected from the drive output terminals.

**Il grafo afferma:** «Moisture inside the motor» **si affronta con** «Measure insulation resistance between each phase conductor and protective earth» (controllo o test)

Contesto: [expected] Use 1000 V DC; for an ABB motor, insulation resistance must be more than 100 Mohm at 25 °C [77 °F]. For other motors, refer to the manufacturer's instructions.; [prerequisite] Do the electrical safety precautions before starting the work, and disconnect the motor cable from the drive output terminals before measuring.; [prerequisite] Do the electrical safety precautions before starting; disconnect the motor cable from the drive output terminals; [warning] Obey the drive safety instructions. If you are not a qualified electrical professional, do not do installation, commissioning or maintenance work.; [warning] Obey the drive safety instructions. Only a qualified electrical professional may do installation, commissioning or maintenance work.

- Giudizio: `?`
- Nota: 

### R103 · Haas vertical mill (2023 operator's manual), pagina 144

**Il manuale dice:**

> Low Voltage (Warning) | The PFDM detects low incoming voltage. If the condition continues, the machine cannot continue to operate.

> Low Voltage (Alarm) | The Power Fault Detect Module (PDFM) detects incoming voltage that is too low to operate. The machine will not operate until the condition is corrected.

**Il grafo afferma:** «Low Voltage Alarm» **può indicare la causa** «Incoming voltage is low»

- Giudizio: `?`
- Nota: 

### R104 · Haas vertical mill (2023 operator's manual), pagina 145

**Il manuale dice:**

> APC E-Stop | [EMERGENCY STOP] on the pallet changer has been pressed. This icon disappears when [EMERGENCY STOP] is released.

**Il grafo afferma:** «APC E-Stop» **può indicare la causa** «Pallet changer emergency stop pressed»

- Giudizio: `?`
- Nota: 

### R105 · Haas vertical mill (2023 operator's manual), pagina 99

**Il manuale dice:**

> In certain cases the pressure against the part may not have been relieved by the Safe Run back-off. In the worse case, an additional crash may be generated after you have reset the alarm. If this happens, turn Safe Run off and jog the axis away from the crash location.

**Il grafo afferma:** «Pressure against the part not relieved by Safe Run back-off» **si affronta con** «Jog the axis away from the crash location»

- Giudizio: `?`
- Nota: 

### R106 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Pump in need of repair | See texture pump instruction manual 308479.

**Il grafo afferma:** «Pump in need of repair» **si affronta con** «See texture pump instruction manual 308479.»

- Giudizio: `?`
- Nota: 

### R107 · ABB ACS580-01 variable speed drive, pagina 231, 232

**Il manuale dice:**

> No power | Red (FAULT) | Active fault in the drive. To reset the fault, press RESET from the control panel or switch off the drive power. | Red (FAULT) | Active fault in the drive. To reset the fault, switch off the drive power.

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Il grafo afferma:** «Active fault in the drive» **si affronta con** «Reset the active drive fault» (riparazione)

Contesto: [if] The display identifies an active fault in the drive.

- Giudizio: `?`
- Nota: 

### R108 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

> Power consumption of the motor is too high. | Like “Pump gets too hot”. Incorrect mains voltage for the motor. | Like malfunction “Pump gets too hot”. - Connect the motor to the correct mains 2 voltage. | .4/4.4

**Il grafo afferma:** «Power consumption of the motor is too high» **può indicare la causa** «Bearing is defective»

- Giudizio: `?`
- Nota: 

## Istruzioni

- `C` corretto: il manuale afferma questo fatto, anche con parole diverse.
- `P` parziale: giusto ma incompleto o impreciso in modo che conta (manca una condizione,
  un'azione è più generica del manuale, un controllo è presentato come riparazione).
- `S` sbagliato: il manuale non lo dice, lo dice di un'altra riga o di un altro problema, o
  dice il contrario.
- `N` non valutabile: il testo mostrato non basta; se puoi, controlla la pagina del PDF e
  giudica, altrimenti lascia `N` e spiega nella nota.

Giudica solo il fatto mostrato, non se il grafo è completo. Una nota breve è utile per `P`, `S` e `N`.
