# Revisione della precisione del grafo

48 affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi
cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi
al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `chiave_non_aprire.json`:
contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.

Revisore: 
Data: 
Tempo totale impiegato (minuti): 

### R001 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «No wire feed, weld output or gas flow; fan operates normally» **può indicare la causa** «Thermostat tripped due to overheating»

- Giudizio: `?`
- Nota: 

### R002 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 4. The fluid pumped contains too much entrained air or gas.

> Pump does not deliver any liquid at start-up 1*2*3*4*5*6*7*8*9*10*11*14*16*17*22*23*24*34

**Il grafo afferma:** «Pump delivers no liquid at start-up» **può indicare la causa** «Pumped fluid contains too much entrained air or gas»

- Giudizio: `?`
- Nota: 

### R003 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 3. The suction head (NPSHR) required by the pump is too high, or the net positive suction head available (NPSHA) at your facility is too low.

> Insufficient flow rate 2*3*4*5*6*7*8*9*10*11*14*16*17*20*21*22*23*24*25*26*34

**Il grafo afferma:** «Insufficient flow rate» **può indicare la causa** «Required NPSH too high or available NPSH too low»

- Giudizio: `?`
- Nota: 

### R004 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump runs rough and noisily 2*3*4*5*6*7*8*9*10*11*15*17*18*21*23*24*27*28*29*30*31*32*33*34*40

> 29. The pump may run rough due to improper balancing of the impeller.

**Il grafo afferma:** «Pump runs rough and noisily» **può indicare la causa** «Impeller improperly balanced»

- Giudizio: `?`
- Nota: 

### R005 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Communication error between display P.C. board and power control board» **si affronta con** «Contact service facility»

- Giudizio: `?`
- Nota: 

### R006 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 31. The impeller may be rubbing against the inside of the case.

**Il grafo afferma:** «Impeller rubbing against inside of case» **riguarda il componente** «Pump case»

- Giudizio: `?`
- Nota: 

### R007 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 39. The mechanical seal may have been damaged by running dry.

**Il grafo afferma:** «Mechanical seal damaged by running dry» **riguarda il componente** «Mechanical seal»

- Giudizio: `?`
- Nota: 

### R008 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Thermostat tripped due to overheating» **si affronta con** «Contact a Lincoln Authorized Field Service Facility if the problem persists» (contattare l'assistenza)

Condizioni: If all recommended possible areas of misadjustment have been checked and the problem persists

- Giudizio: `?`
- Nota: 

### R009 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 010» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R010 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> The capacitors must be reformed if the drive has not been powered (either in storage or unused) for a year or more. The manufacturing date is on the type designation label. For information on reforming the capacitors, see Capacitor reforming instructions (3BFE64059629 [English]) in the ABB Library (https://library.abb.com/en).

**Il grafo afferma:** «Capacitors require reforming after at least a year without power» **si affronta con** «Reform the capacitors» (riparazione)

Condizioni: If the drive has not been powered for a year or more

- Giudizio: `?`
- Nota: 

### R011 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> Low or no gas flow when gun trigger is pulled. Wire feed, weld output and fan operate normally. | 1. Check gas supply, flow regulator and gas hoses. 2. Check gun connection to machine for obstruction or leaky machine. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Obstruction at the gun connection to the machine» **si affronta con** «Check the gas supply, flow regulator, and gas hoses» (controllo o test)

- Giudizio: `?`
- Nota: 

### R012 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

> Panel has no power | Green | Drive functioning normally. Connection between the drive and control panel may be faulty or lost, or the panel and drive may be incompatible. Check the control panel display. | Green | Blinking: Active warning in the drive Flickering: Data transferred between the PC tool and drive through the USB connection of the control panel

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Il grafo afferma:** «Faulty or lost connection between drive and control panel» **si affronta con** «Check the control panel display» (controllo o test)

- Giudizio: `?`
- Nota: 

### R013 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

**Il grafo afferma:** «Overtemperature warnings and faults» **può indicare la causa** «Heatsink not clean»

- Giudizio: `?`
- Nota: 

### R014 · ABB ACS580-01 variable speed drive, pagina 361

**Il manuale dice:**

> Test the operation of the failure detection of the drive. The motor can be stopped or running. • Open the 1st channel of the STO circuit. If the motor was running, it should coast to a stop. The drive generates a FA81 Safe Torque Off 1 loss fault indication (see the firmware manual). • Give a start command to verify that the STO function blocks the drive's operation. The motor should not start. • Close the STO circuit. • Reset any active faults. Restart the drive and check that the motor runs normally. • Open the 2nd channel of the STO circuit. If the motor was running, it should coast to a stop. The drive generates a FA82 Safe Torque Off 2 loss fault indication (see the firmware manual). • Give a start command to verify that the STO function blocks the drive's operation. The motor should not start. • Close the STO circuit. • Reset any active faults. Restart the drive and check that the motor runs normally.

**Il grafo afferma:** «Safe Torque Off 2 loss» **(codice) indica la causa** «Loss of the second STO circuit channel»

Condizioni: When the second STO circuit channel is opened

- Giudizio: `?`
- Nota: 

### R015 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Arc is unstable and starting is poor» **può indicare la causa** «Work cable has loose or faulty connections»

- Giudizio: `?`
- Nota: 

### R016 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed when gun trigger is pulled. Fan runs, gas flows and machine has correct open circuit volt- age (33V) - weld output. | 1. If the wire drive motor is running make sure that the correct drive rolls are installed in the machine. 2. Check for clogged cable liner or con- tact tip. 3. Check for proper size cable liner and contact tip. 4. Check if the spool gun switch, locat- ed in the wire drive compartment, is set to the desired location. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Incorrect cable liner size» **riguarda il componente** «Cable liner»

- Giudizio: `?`
- Nota: 

### R017 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 36. The shaft sleeve may be scored or pitted in the region of the packing due to dirt or abrasive matter in the flushing fluid.

**Il grafo afferma:** «Shaft sleeve scored or pitted by dirt or abrasive flushing fluid» **riguarda il componente** «Shaft sleeve»

- Giudizio: `?`
- Nota: 

### R018 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «Thermostat tripped due to overheating» **si affronta con** «Let machine cool»

- Giudizio: `?`
- Nota: 

### R019 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed when gun trigger is pulled. Fan runs, gas flows and machine has correct open circuit volt- age (33V) - weld output. | 1. If the wire drive motor is running make sure that the correct drive rolls are installed in the machine. 2. Check for clogged cable liner or con- tact tip. 3. Check for proper size cable liner and contact tip. 4. Check if the spool gun switch, locat- ed in the wire drive compartment, is set to the desired location. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Clogged contact tip» **riguarda il componente** «Contact tip»

- Giudizio: `?`
- Nota: 

### R020 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 16. Pump rotation wrong or impeller installed backwards.

> Discharge pressure is too high 4*14*16*18*20*22*23*24*25*26*34

**Il grafo afferma:** «Discharge pressure is too high» **può indicare la causa** «Pump rotation wrong or impeller installed backwards»

- Giudizio: `?`
- Nota: 

### R021 · ABB ACS580-01 variable speed drive, pagina 231, 232

**Il manuale dice:**

> No power | Red (FAULT) | Active fault in the drive. To reset the fault, press RESET from the control panel or switch off the drive power. | Red (FAULT) | Active fault in the drive. To reset the fault, switch off the drive power.

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

> Panel has no power | column 2: | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Blue | Panels with a Bluetooth interface only. Blinking: Bluetooth interface is enabled. It is in discoverable mode and ready for pairing. Flickering: Data is transfered through the Bluetooth interface of the control panel.

**Il grafo afferma:** «Active fault in the drive» **si affronta con** «Reset the active drive fault» (riparazione)

Condizioni: Active fault in the drive; If the fault is in the drive

- Giudizio: `?`
- Nota: 

### R022 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «No wire feed, weld output, or gas flow when the gun trigger is pulled; fan operates normally» **può indicare la causa** «Thermostat tripped due to overheating»

- Giudizio: `?`
- Nota: 

### R023 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 23. The impeller may be clogged with debris.

> Insufficient flow rate 2*3*4*5*6*7*8*9*10*11*14*16*17*20*21*22*23*24*25*26*34

**Il grafo afferma:** «Insufficient flow rate» **può indicare la causa** «Impeller clogged with debris»

- Giudizio: `?`
- Nota: 

### R024 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> LEDs off | LED lit and steady | column 3: | LED blinking

> No power | Red (FAULT) | Active fault in the drive. To reset the fault, press RESET from the control panel or switch off the drive power. | Red (FAULT) | Active fault in the drive. To reset the fault, switch off the drive power.

**Il grafo afferma:** «Drive FAULT LED blinking» **può indicare la causa** «Active fault in the drive»

- Giudizio: `?`
- Nota: 

### R025 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan does NOT operate. | 1. Make sure correct voltage is applied to the machine. 2. Make certain that power switch is in the ON position. 3. Make sure circuit breaker is reset. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Incorrect input voltage to the machine» **si affronta con** «Contact a Lincoln Authorized Field Service Facility if the problem persists» (contattare l'assistenza)

Condizioni: If all recommended possible areas of misadjustment have been checked and the problem persists

- Giudizio: `?`
- Nota: 

### R026 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 2. The pump suction line has not been completely primed.

> Pump does not deliver any liquid at start-up 1*2*3*4*5*6*7*8*9*10*11*14*16*17*22*23*24*34

**Il grafo afferma:** «Pump delivers no liquid at start-up» **può indicare la causa** «Pump suction line not completely primed»

- Giudizio: `?`
- Nota: 

### R027 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 1. The pump has not been properly bled of air.

> Pump overheats and/or ceases to deliver liquid 1*3*9*10*11*21*22*27*29*30*31*33*34*40*41

**Il grafo afferma:** «Pump overheats and/or ceases to deliver liquid» **può indicare la causa** «Pump not properly bled of air»

- Giudizio: `?`
- Nota: 

### R028 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

> 3. Blow dry, clean and oil-free compressed air from bottom to top and simultaneously use a vacuum cleaner at the air outlet to trap the dust. If there is a risk of dust entering adjoining equipment, do the cleaning in another room.

**Il grafo afferma:** «Heatsink not clean» **si affronta con** «Clean the heatsink»

- Giudizio: `?`
- Nota: 

### R029 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump runs rough and noisily 2*3*4*5*6*7*8*9*10*11*15*17*18*21*23*24*27*28*29*30*31*32*33*34*40

> 15. Pump drive rotational speed too high.

**Il grafo afferma:** «Pump runs rough and noisily» **può indicare la causa** «Pump drive rotational speed too high»

- Giudizio: `?`
- Nota: 

### R030 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 003» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R031 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Arc is unstable and starting is poor» **può indicare la causa** «Gun damaged or broken»

- Giudizio: `?`
- Nota: 

### R032 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Shaft seal leaks appreciably, or the packing leaks excessively 27*28*29*30*33*34*35*36*39

> 36. The shaft sleeve may be scored or pitted in the region of the packing due to dirt or abrasive matter in the flushing fluid.

**Il grafo afferma:** «Shaft seal leaks appreciably or packing leaks excessively» **può indicare la causa** «Shaft sleeve scored or pitted by dirt or abrasive flushing fluid»

- Giudizio: `?`
- Nota: 

### R033 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «No wire feed, weld output or gas flow when gun trigger is pulled; fan operates normally» **può indicare la causa** «Thermostat tripped due to overheating»

- Giudizio: `?`
- Nota: 

### R034 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «No wire feed, weld output, or gas flow when the gun trigger is pulled; fan operates normally» **può indicare la causa** «Faulty gun trigger»

- Giudizio: `?`
- Nota: 

### R035 · ABB ACS580-01 variable speed drive, pagina 375

**Il manuale dice:**

> There is no communication with the drive control unit or the adapter module has detected an error. Red

> Red | There is no communication with the drive control unit or the adapter module has detected an error.

**Il grafo afferma:** «Red adapter module diagnostic LED» **può indicare la causa** «No communication with the drive control unit»

- Giudizio: `?`
- Nota: 

### R036 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Communication error between display P.C. board and power control board» **si affronta con** «Cycle power to the machine» (riparazione)

- Giudizio: `?`
- Nota: 

### R037 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> Capacitor failure is usually followed by damage to the unit and an input cable fuse failure, or a fault trip. If you think that any capacitors in the drive have failed, contact ABB.

**Il grafo afferma:** «Drive fault trip» **può indicare la causa** «Failed drive capacitors»

- Giudizio: `?`
- Nota: 

### R038 · ABB ACS580-01 variable speed drive, pagina 169

**Il manuale dice:**

> 2. Make sure that the resistor cable is connected to the resistor and disconnected from the drive output terminals.

> 3. At the drive end, connect the R+ and R- conductors of the resistor cable together. Measure the insulation resistance between the conductors and the PE conductor with a measuring voltage of 1000 V DC. The insulation resistance must be more than 1 Mohm.

**Il grafo afferma:** «Unspecified cause of resistor insulation resistance at or below 1 Mohm» **si affronta con** «Measure resistor cable insulation resistance between the conductors and PE» (controllo o test)

Condizioni: The insulation resistance must be more than 1 Mohm

- Giudizio: `?`
- Nota: 

### R039 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Obstruction in machine airflow» **si affronta con** «Check for obstructions in the airflow» (controllo o test)

- Giudizio: `?`
- Nota: 

### R040 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Error Code 013» **(codice) indica la causa** «Communication error between display P.C. board and power control board»

- Giudizio: `?`
- Nota: 

### R041 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> Capacitor failure is usually followed by damage to the unit and an input cable fuse failure, or a fault trip. If you think that any capacitors in the drive have failed, contact ABB.

**Il grafo afferma:** «Input cable fuse failure» **può indicare la causa** «Failed drive capacitors»

- Giudizio: `?`
- Nota: 

### R042 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan oper- ates normally. | 1. The thermostat may be tripped due to overheating. Let machine cool. Weld at lower duty cycle. 2. Check for obstructions in air flow. Check Gun Trigger connections. See installation section. 3. Gun trigger may be faulty.

**Il grafo afferma:** «Thermostat tripped due to overheating» **si affronta con** «Let machine cool; weld at lower duty cycle»

- Giudizio: `?`
- Nota: 

### R043 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

> Panel has no power | Green | Drive functioning normally. Connection between the drive and control panel may be faulty or lost, or the panel and drive may be incompatible. Check the control panel display. | Green | Blinking: Active warning in the drive Flickering: Data transferred between the PC tool and drive through the USB connection of the control panel

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Il grafo afferma:** «Control panel and drive are incompatible» **si affronta con** «Check the control panel display» (controllo o test)

- Giudizio: `?`
- Nota: 

### R044 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

**Il grafo afferma:** «Heatsink not clean» **riguarda il componente** «Drive module heatsink»

- Giudizio: `?`
- Nota: 

### R045 · ABB ACS580-01 variable speed drive, pagina 396

**Il manuale dice:**

> If the warning A7AB Extension I/O configuration failure is shown,

> • make sure that the value of parameter 15.02 is CMOD-02.

> Warning A7AB Extension I/O configuration failure.

**Il grafo afferma:** «Unspecified cause of extension I/O configuration failure» **si affronta con** «Check that parameter 15.02 is set to CMOD-02» (controllo o test)

Condizioni: If warning A7AB is shown; When warning A7AB is shown

- Giudizio: `?`
- Nota: 

### R046 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Communication error between display P.C. board and power control board» **si affronta con** «Cycle power to machine»

- Giudizio: `?`
- Nota: 

### R047 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

> LED off | LED lit and steady | column 3: | LED blinking/flickering

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

> Panel has no power | column 2: | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Blue | Panels with a Bluetooth interface only. Blinking: Bluetooth interface is enabled. It is in discoverable mode and ready for pairing. Flickering: Data is transfered through the Bluetooth interface of the control panel.

**Il grafo afferma:** «Control panel red LED lit steadily» **può indicare la causa** «Active fault in another drive on the panel bus»

Condizioni: Active fault in another drive on the panel bus; If the display identifies an active fault in another drive on the panel bus

- Giudizio: `?`
- Nota: 

### R048 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan does NOT operate. | 1. Make sure correct voltage is applied to the machine. 2. Make certain that power switch is in the ON position. 3. Make sure circuit breaker is reset. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Incorrect input voltage to the machine» **si affronta con** «Check that the correct voltage is applied to the machine» (controllo o test)

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
