# Revisione di Fabio: lg_lmh2235st (gold v2, fatto da un'AI)

Campione casuale (seme 20261113), stratificato per categoria. Per ogni elemento apri la pagina del PDF
e scrivi una X: serve a stimare l'errore del gold. Finché non è compilato, `human_review` resta `false`.

## Elementi

### 1. B085 · diagnostic_test · pagina 29

- problema: Primary interlock switch test
- causa: non indicata nel manuale
- azione 1 (inspection): Open the door slowly: an audible click should be heard and the latches should activate the switches with an audible click — atteso: audible click at the same time or successively at intervals
- azione 2 (repair): Adjust the switches in accordance with the adjustment procedure — condizione: If the latches do not activate the switches when the door is closed
- azione 3 (repair): Disconnect the wire lead from the switch
- azione 4 (inspection): Connect the ohmmeter leads to the common (COM) and normally open (NO) terminals of the switch; door open condition — atteso: open circuit
- azione 5 (inspection): Door closed — atteso: closed circuit
- azione 6 (repair): Make the necessary adjustment — condizione: If the primary switch operation is abnormal
- azione 7 (repair): or replace the switch, making sure to replace it with the same type of switch — condizione: If the primary switch operation is abnormal
- citazione: «Connect the ohmmeter leads to the common (COM) and normally open (NO) terminal of the switch»
- sezione: 9. INTERLOCK SYSTEM > 9-2. Interlock Continuity Test > A. PRIMARY INTERLOCK SWITCH TEST
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 2. B028 · diagnostic_test · pagina 12

- problema: Self diagnosis (humidity Sensor and PCB thermistor check)
- causa: non indicata nel manuale
- azione 1 (inspection): Press “Defrost weight/time” for 2 seconds — atteso: unit will display “TEST” and Beep once
- azione 2 (inspection): The unit will check if the PCB humidity sensor and PCB thermistor are short or open. — atteso: it will beep and display "PASS"
- azione 3 (inspection): If it has an error, it will beep and display an error code. — condizione: If it has an error
- azione 4 (repair): Press “ Clear” to return to Standby mode.
- citazione: «The unit will check if the PCB humidity sensor and PCB thermistor are short or open.»
- sezione: 6-3 Self diagnosis (humidity Sensor and PCB thermistor check) & Error code
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 3. B084 · diagnostic_test · pagina 28

- problema: Test the microwave energy leakage (after interlock adjustment)
- causa: non indicata nel manuale
- azione 1 (inspection): Measure the microwave energy leakage with a survey meter (275 ml water load) — atteso: below the limit of 1mW/cm2
- azione 2 (inspection): Measure the microwave energy leakage with a survey meter (275 ml water load without the cabinet) — atteso: below 5mW/cm2
- citazione: «Make sure the microwave energy leakage is below the limit of 1mW/cm2»
- sezione: 9. INTERLOCK SYSTEM > 9-1. Interlock Mechanism > ADJUSTMENT PROCEDURES > TEST THE MICROWAVE ENERGY LEAKAGE
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 4. B096 · diagnostic_test · pagina 31

- problema: Diode test
- causa: non indicata nel manuale
- azione 1 (inspection): Measure continuity. Forward. (ohm meter scale: Rx1000) - Abnormal: Infinite — atteso: Normal: Below 100 ohms
- azione 2 (inspection): Measure continuity. Reverse. (ohm meter scale: Rx1000) - Abnormal: Below 100 ohms — atteso: Normal: Infinite.
- citazione: «Normal: Below 100 ohms Abnormal:Infinite»
- sezione: 10. COMPONENT TESTING INFORMATION > A. TEST PROCEDURES > DIODE
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 5. B108 · diagnostic_test · pagina 38

- problema: Interlock switch check after replacing the door
- causa: non indicata nel manuale
- azione 1 (inspection): Check that the primary interlock switch, the secondary interlock switch and the interlock monitor switch are in good operating condition — atteso: in good operating condition
- citazione: «be sure to check that the primary interlock switch, the secondary interlock switch and the interlock monitor switch are in good operating condition»
- sezione: 11. DISASSEMBLY INSTRUCTIONS > F. REMOVING DOOR > NOTES
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 6. B030 · error_code · pagina 12

- problema: PCB thermistor open (codice F-2)
- causa: non indicata nel manuale
- citazione: «F-2 PCB thermistor open»
- sezione: 6-3 Self diagnosis (humidity Sensor and PCB thermistor check) & Error code
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 7. B038 · fault · pagina 13

- problema: No key, Not started, Operating O.L, V.M, T.T.M.
- causa: non indicata nel manuale
- azione 1 (inspection): Check: Open/Short when the door is closed. (Switch)
- citazione: «Check: Open/Short when the door is closed. (Switch)»
- sezione: 6-3. Basic Check Summary
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 8. B041 · fault · pagina 13

- problema: Operating V.M, T.T.M. automatically
- causa: non indicata nel manuale
- azione 1 (inspection): Check: Open/Short when the door is open. (Switch)
- citazione: «Symptom #2(Door is open): Operating V.M, T.T.M. automatically»
- sezione: 6-3. Basic Check Summary
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 9. B051 · flowchart · pagina 16, 17

- problema: Keypad Failure
- causa: non indicata nel manuale
- azione 1 (inspection): Do the keys operate? — atteso: No
- azione 2 (inspection): Do only the START key and EZ-ON keys operate? (Door should be closed.) — atteso: No — condizione: Power ON; Do the keys operate? NO
- azione 3 (inspection): Check PWB Go to No. 4 of this flow chart. — condizione: Do only the START key and EZ-ON keys operate? (Door should be closed.) NO
- azione 4 (inspection): Is the connector connected to the PCB disconnected or disassembled? — atteso: Yes — condizione: Go to No. 4 of this flow chart
- azione 5 (repair): Reconnect or repair the connector. — condizione: Is the connector connected to the PCB disconnected or disassembled? YES
- citazione: «Is the connector connected to the PCB disconnected or disassembled? Reconnect or repair the connector.»
- sezione: 6-4. Troubleshooting > Keypad Failure
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 10. B049 · flowchart · pagina 16, 17

- problema: Keypad Failure
- causa: non indicata nel manuale
- azione 1 (inspection): Do the keys operate? — atteso: No
- azione 2 (inspection): Do only the START key and EZ-ON keys operate? (Door should be closed.) — atteso: Yes — condizione: Power ON
- azione 3 (inspection): Is there a beeping sound in the continuity test between the ends of the latch board? - Secondary switch (Door should be closed.) — atteso: No — condizione: Do only the START key and EZ-ON keys operate? (Door should be closed.) YES
- azione 4 (repair): Adjust latch board (Refer to section 9-1,9-2) — condizione: if no beeping sound across the secondary switch (No)
- citazione: «Is there a beeping sound in the continuity test between the ends of the latch board?»
- sezione: 6-4. Troubleshooting > Keypad Failure
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 11. B045 · flowchart · pagina 14, 15

- problema: No Display or Dead
- causa: non indicata nel manuale
- azione 1 (inspection): Does the display operate? — atteso: No
- azione 2 (inspection): When you push any Key, is there any beeping sound? — atteso: Yes — condizione: Does the display operate? NO
- azione 3 (repair): Replace the PCB. (EBR75341201) — condizione: if beeping sound when pushing any key (Yes): Go to No. 6 of this flow chart
- citazione: «Go to No. 6 of this flow chart. Replace the PCB.»
- sezione: 6-4. Troubleshooting > No Display or Dead
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 12. B065 · flowchart · pagina 23, 19

- problema: Turns on automatically
- causa: If something is caught in the door or in the sealing area, the microwave oven cannot operate safely. The latch switches and monitor switch will prevent operation.
- azione 1 (inspection): Does the product turn on automatically without pushing the start key? — atteso: Yes
- azione 2 (inspection): Repeat door open and close at least three times. Does the product operate? — atteso: Yes — condizione: Does the product turn on automatically without pushing the start key? YES
- citazione: «Alternate explanation (refer to the Note on p. 19)»
- sezione: 6-4. Troubleshooting > Turns on automatically
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 13. B043 · flowchart · pagina 14, 15

- problema: No Display or Dead
- causa: non indicata nel manuale
- azione 1 (inspection): Does the display operate? — atteso: No
- azione 2 (inspection): When you push any Key, is there any beeping sound? — atteso: No — condizione: Does the display operate? NO
- azione 3 (inspection): Is the connector connected to the PCB? — atteso: Yes — condizione: Power Off
- azione 4 (inspection): Is there any beeping sound in the continuity test between the power cord and the connector ? - Code "L" to Pin1 - Code "N" to Pin3 — atteso: No — condizione: Is the connector connected to the PCB? YES
- azione 5 (inspection): Is there any beeping sound in the continuity test between the ends of the fuse? — atteso: No — condizione: Is there any beeping sound in the continuity test between the power cord and the connector ? - Code "L" to Pin1 - Code "N" to Pin3 NO
- azione 6 (repair): Replace the Fuse. — condizione: if no beeping sound across the fuse (No)
- citazione: «Is there any beeping sound in the continuity test between the ends of the fuse? No Replace the Fuse.»
- sezione: 6-4. Troubleshooting > No Display or Dead
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 14. B057 · flowchart · pagina 18, 19, 20

- problema: No Heat / No Cook
- causa: non indicata nel manuale
- azione 1 (inspection): After power on, does the product operate? — atteso: No
- azione 2 (inspection): Repeat Door Open and close at least three times. Does product operate? — atteso: No — condizione: After power on, does the product operate? NO
- azione 3 (inspection): Is there any beeping sound in the continuity test between TAB1 and TAB2? — atteso: Yes — condizione: Repeat Door Open and close at least three times. Does product operate? NO
- azione 4 (inspection): Is there any beeping sound in the continuity test between the ends of the latch board? (Door should be closed) — atteso: No — condizione: Power Off
- azione 5 (repair): Adjust the latch board (Refer to section 9-1,9-2) — condizione: if Is there any beeping sound in the continuity test between the ends of the latch board? No
- citazione: «Adjust the latch board (Refer to section 9-1,9-2)»
- sezione: 6-4. Troubleshooting > No Heat / No Cook
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 15. B072 · flowchart · pagina 23

- problema: Turns on automatically
- causa: non indicata nel manuale
- azione 1 (inspection): Does the product turn on automatically without pushing the start key? — atteso: Yes
- azione 2 (inspection): Repeat door open and close at least three times. Does the product operate? — atteso: No — condizione: Does the product turn on automatically without pushing the start key? YES
- azione 3 (inspection): Is there any beeping sound in the continuity test between the ends of the latch board? - Secondary switch (Door should be closed.) — atteso: Yes — condizione: Repeat door open and close at least three times. Does the product operate? NO
- azione 4 (inspection): When the door is closed, does the oven lamp turn on? — atteso: Yes — condizione: Power ON
- azione 5 (inspection): When the door is opened, Is the voltage of the door sensing part over 4 V? (Pin 11 to Pin 12) — atteso: No — condizione: When the door is closed, does the oven lamp turn on? YES
- azione 6 (repair): Replace the PCB (EBR75341201) — condizione: if the door sensing voltage is not over 4 V (No)
- citazione: «When the door is opened, Is the voltage of the door sensing part over 4 V? No Replace the PCB»
- sezione: 6-4. Troubleshooting > Turns on automatically
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 16. B059 · flowchart · pagina 18, 19, 20

- problema: No Heat / No Cook
- causa: non indicata nel manuale
- azione 1 (inspection): After power on, does the product operate? — atteso: No
- azione 2 (inspection): Repeat Door Open and close at least three times. Does product operate? — atteso: No — condizione: After power on, does the product operate? NO
- azione 3 (inspection): Is there any beeping sound in the continuity test between TAB1 and TAB2? — atteso: Yes — condizione: Repeat Door Open and close at least three times. Does product operate? NO
- azione 4 (inspection): Is there any beeping sound in the continuity test between the ends of the latch board? (Door should be closed) — atteso: Yes — condizione: Power Off
- azione 5 (inspection): Is the connector connected to High Voltage Transformer assembly disconnected or disassembled? — atteso: No — condizione: Is there any beeping sound in the continuity test between the ends of the latch board? (Door should be closed) YES
- azione 6 (inspection): Is the resistance of the high voltage Transformer out of range? Test Point 1. Primary winding: 0.2 ~ 0.5 Ohm 2. Secondary: 50 ~ 120 Ohm 3. Filament winding: 0 Ohm — atteso: Yes — condizione: Is the connector connected to High Voltage Transformer assembly disconnected or disassembled? NO
- azione 7 (repair): Replace the High Voltage Transformer. — condizione: if Is the resistance of the high voltage Transformer out of range? Yes
- citazione: «Replace the High Voltage Transformer.»
- sezione: 6-4. Troubleshooting > No Heat / No Cook
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 17. P010 · procedure · pagina 36

- procedura: Removing the door interlock switches
- passi: 3
  1. Disconnect the wire leads from the interlock switches.
  2. Remove the two screws securing the Latch Board.
  3. Make any necessary replacements and check for microwave energy leakage according to ADJUSTMENT PROCEDURES on page 7-12.
- citazione: «Disconnect the wire leads from the interlock»
- sezione: 11. DISASSEMBLY INSTRUCTIONS > C. REMOVING THE DOOR INTERLOCK SWITCHES (Figures 9, 10)
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 18. P003 · procedure · pagina 24, 25

- procedura: Measuring microwave energy leakage
- passi: 10
  1. Equipment: tester (volts-DC, AC, ohmmeter); microwave survey meter (Holaday HI-1500, HI-1501; Narda 8100, 8200); 600 cc non conductive material beaker (glass or plastic), inside diameter approx. 8.5 cm (3 1/2 in.); glass thermometer 100 °C or 212 °F (1 deg scale).
  2. Pour 275±15cc of 20±5°C (68±9°F) water in a beaker which is graduated to 600 cc, and place the beaker in the oven.
  3. Set the energy leakage monitor to 2,450 MHz and use it following the manufacturer's recommended test procedure to assure correct result.
  4. When measuring the leakage, always use the 2-inch (5cm) spacer supplied with the probe.
  5. Operate the oven at its maximum output.
  6. Measure the microwave radiation using an electromagnetic radiation monitor by holding the probe perpendicular to the surface being measured. Move probe along shaded area. Probe scanning speed less than 2.5 cm/sec (1 in/sec).
  7. Measurement with the outer case removed: when you replace the magnetron, measure for microwave energy leakage before the outer case is installed and after all necessary components are replaced or adjusted. Special care should be taken in measuring around the magnetron and the waveguide. WARNING: avoid contacting any high voltage parts.
  8. Measurement with a fully assembled oven: after all components, including the outer panels, are fully assembled, measure for microwave energy leakage around the door viewing window, the exhaust opening and air inlet openings.
  9. Microwave energy leakage must not exceed the values prescribed: leakage with the outer panels removed than 5 mW/cm2; leakage for a fully assembled oven (before the latch switch [primary] is interrupted) with the door in a slightly opened position - less than 1 mW/cm2.
  10. Note when measuring: (1) Do not exceed meter full scale deflection. (2) The test probe must be removed no faster than 1 inch/sec (2.5cm/sec) along the shaded area, otherwise a false reading may result. (3) The test probe must be held with the grip portion of the handle; a false reading may result if the operator's hand is between the handle and the probe. (4) When testing near a corner of the door, keep the probe perpendicular to the surface making sure to move the probe horizontally along the oven surface, to avoid possible damage to the probe.
- citazione: «Set the energy leakage monitor to 2,450 MHz»
- sezione: 7. MICROWAVE LEAKAGE TEST > MEASURING MICROWAVE ENERGY LEAKAGE
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 19. P018 · procedure · pagina 47

- procedura: Replacing the base plate assembly (one assembly)
- passi: 3
  1. Remove the 8 screws
  2. Disconnect the wire connector
  3. Replace with the new base assembly, plate - connect wire connector - replace the 8 screws
- citazione: «BASE PLATE PARTS»
- sezione: 12. EXPLODED VIEW > BASE PLATE PARTS
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 20. P002 · routine · pagina 11

- procedura: TRIAL OPERATION
- passi: 7
  1. A. Put a container filled with water (about 1 liter) into the oven, and close the door tightly.
  2. B. Set cooking time for 10 minutes by touching 1 and then 0 three times. 1, 0, 0, 0 appears in the display window.
  3. C. Press the START button. Make sure the cavity light comes on. The unit will begin cooking and the display window will show the time counting down by seconds.
  4. D. After about 5 minutes, make sure the primary interlock switch, the secondary interlock switch and the interlock monitor switch operate properly by opening and closing the door several times. Press the START button each time the door is closed.
  5. E. Continue operating the unit. Two short beeps and one long beep will sound when the time is up. The unit will shut off automatically.
  6. F. Confirm the water is hot.
  7. G. Finally, measure the output power according to the POWER OUTPUT MEASUREMENT on page 8.
- citazione: «After installation, the following sequences and results should be checked carefully.»
- sezione: 6-1. General Information for Service > TRIAL OPERATION
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 21. B001 · safety_precaution · pagina 1

- problema: CAUTION: before servicing the unit, read the safety precautions in this manual
- causa: non indicata nel manuale
- azione 1 (repair): Read the safety precautions in this manual — condizione: before servicing the unit
- citazione: «BEFORE SERVICING THE UNIT, READ THE SAFETY PRECAUTIONS IN THIS MANUAL»
- sezione: Cover
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 22. B105 · safety_precaution · pagina 37

- problema: When removing the magnetron, its dome may be damaged if it hits adjacent parts
- causa: non indicata nel manuale
- azione 1 (repair): Make sure that the magnetron dome does not hit any adjacent parts when removing the magnetron
- citazione: «make sure that its dome does not hit any adjacent parts, or it may be damaged»
- sezione: 11. DISASSEMBLY INSTRUCTIONS > D. REMOVING MAGNETRON > NOTES
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 23. B110 · safety_precaution · pagina 38

- problema: If the door assembly is not mounted properly, microwaves may leak from the clearance between the door and the oven
- causa: door assembly is not mounted properly
- azione 1 (repair): When mounting the door assembly to the oven assembly, adjust the door assembly parallel to the chassis
- azione 2 (repair): Adjust it so the door has no play between the inner door surface and oven frame assembly
- citazione: «If the door assembly is not mounted properly, microwaves may leak from the clearance between the door and the oven»
- sezione: 11. DISASSEMBLY INSTRUCTIONS > H. ASSEMBLING DOOR
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 24. B112 · safety_precaution · pagina 39

- problema: Removing the lead wire from the turntable motor
- causa: non indicata nel manuale
- azione 1 (repair): Remove the lead wire from the turntable motor VERY CAREFULLY
- azione 2 (repair): Be sure to grasp the connector, not the wires, when removing
- citazione: «Be sure to grasp the connector, not the wires, when removing.»
- sezione: 11. DISASSEMBLY INSTRUCTIONS > J. REMOVING THE TURNTABLE MOTOR > NOTES
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 25. B021 · safety_precaution · pagina 5

- problema: Unlike other appliances, the microwave oven is high-voltage and high-current equipment.
- causa: non indicata nel manuale
- azione 1 (prohibition): NEVER put iron tools on the magnetron.
- citazione: «NEVER put iron tools on the magnetron»
- sezione: 2. CAUTIONS
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 26. B079 · safety_precaution · pagina 25

- problema: High voltage parts during leakage measurement with the outer case removed
- causa: non indicata nel manuale
- azione 1 (prohibition): Avoid contacting any high voltage parts
- citazione: «WARNING: AVOID CONTACTING ANY HIGH VOLTAGE PARTS»
- sezione: 7. MICROWAVE LEAKAGE TEST > MEASUREMENT WITH THE OUTER CASE REMOVED
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 27. B034 · safety_precaution · pagina 12

- problema: TO AVOID POSSIBLE EXPOSURE TO MICROWAVE ENERGY LEAKAGE (after power is applied)
- causa: non indicata nel manuale
- azione 1 (inspection): Make sure the interlock switch mechanism is operating properly by opening and closing the door.
- azione 2 (inspection): Check microwave energy leakage must be below the limit of 5 mW/cm2 . (All service adjustments should be made for minimum microwave energy leakage readings). — atteso: below the limit of 5 mW/cm2
- citazione: «Check microwave energy leakage must be below the limit of 5 mW/cm2»
- sezione: 6-2. Safety Caution
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 28. B018 · safety_precaution · pagina 5

- problema: A resulting static electric discharge may damage the P.C.B.
- causa: non indicata nel manuale
- azione 1 (prohibition): DO NOT touch any parts of the control panel circuit.
- citazione: «DO NOT touch any parts of the control panel circuit. A resulting static electric discharge»
- sezione: 2. CAUTIONS
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 29. B004 · safety_precaution · pagina 2

- problema: Precautions to be observed before and during servicing to avoid possible exposure to excessive microwave energy
- causa: non indicata nel manuale
- azione 1 (inspection): Check the magnetron, wave guide or transmission line, and cavity for proper alignment, integrity, and connections — condizione: before turning on microwave power for any service test or inspection within the microwave generating compartments
- citazione: «check the magnetron, wave guide or transmission line, and cavity for proper alignment»
- sezione: CAUTION > WARNING TO SERVICE TECHNICIANS > PRECAUTIONS TO BE OBSERVED BEFORE AND DURING SERVICING
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

### 30. B078 · safety_precaution · pagina 24

- problema: Radiation leakage to operating personnel
- causa: non indicata nel manuale
- azione 1 (inspection): Check all surface and vent openings for microwave emission testing
- azione 2 (inspection): Check for microwave energy leakage after every servicing — atteso: should not exceed 1mW/cm2.sq.
- azione 3 (repair): Always start measuring of an unknown field to assure safety for operating personnel from radiation leakage
- citazione: «Service personnel should check all surface and vent openings for microwave emission testing»
- sezione: 7. MICROWAVE LEAKAGE TEST > CAUTION
- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato
- commento:

## Pagine marcate non diagnostiche

Guarda la pagina: contiene guasti, codici, test o rimedi che mancano nel gold?

- pagina 3 (safety, toc: Foreword (b3-1) e indice; numeri di pagina stampati = pagine PDF (verificato p2-p10 e p24).) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 5 (safety: 2. Cautions: riquadro alta tensione, 9 bullet, riquadro microwave radiation, figura magnetron, servizio solo da personale qualificato (b5-1..b5-12, b2-6, b2-7).) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 6 (setup procedure, safety: 3. Installation: precautions A-D (routine p6-1), grounding instructions (b6-1) e warning sul ground prong (b6-2).) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 7 (controls: 4-1. Control Panel: figura del pannello con 25 richiami numerati. Nessun item.) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 8 (controls, operation: 4-2. Spiegazione dei 25 tasti; unica frase condizionale su START/ENTER dopo apertura porta (b8-1, routine).) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 10 (key matrix: 5-2. Key matrix 2st/1-7 x 8-13. Nessun item.) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 11 (safety, operation, specifications: Precauzioni d'uso generali, trial operation (routine), elenco sistemi di sicurezza: nessun item core/extended. Precauzioni d'uso A e B (B118, B119) aggiunte dopo il confronto con v1: sicurezza (context).) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 40 (exploded view: Cap. 12 Exploded view, introduzione: tabella modelli e vista generale con i gruppi (door, oven cavity, interior, latch board, control panel parts). Nessun item.) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 44 (exploded view: LATCH BOARD PARTS: esploso con soli numeri di posizione. Solo inventario.) — [ ] niente da aggiungere   [ ] manca qualcosa:
- pagina 49 (back cover: Retro copertina con logo LG Electronics Inc., nessun testo tecnico.) — [ ] niente da aggiungere   [ ] manca qualcosa:
