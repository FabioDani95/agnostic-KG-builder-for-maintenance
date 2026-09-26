# Revisione della precisione del grafo

96 affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi
cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi
al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `chiave_non_aprire.json`:
contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.

Revisore: Codex (assistente AI; chiave non consultata, già esposto allo sviluppo della pipeline)
Data: 2026-09-27 (Europe/Zurich)
Tempo totale impiegato (minuti): 4.7 (tempo trascorso della revisione AI)

### R001 · Hypertherm Powermax30 AIR, pagina 95

**Il manuale dice:**

> 6. If the fan does not operate, replace the fan. See Replace the fan on page 164.

**Il grafo afferma:** «Fan does not operate» **può indicare la causa** «Fan does not operate»

- Giudizio: `S`
- Nota: Ripete il mancato funzionamento come propria causa: a p. 95 il manuale prescrive un test e la sostituzione, non questa relazione causale autoreferenziale.

### R002 · Hypertherm Powermax30 AIR, pagina 71

**Il manuale dice:**

> The arc goes out during cutting or intermittently will not fire. | • The work lead connection is poor. The work lead may be damaged or not properly connected to the workpiece. | • Inspect for loose connections at the ground clamp and at the power supply, and repair if necessary. • Reposition the work lead on the workpiece. • Clean the cutting surface to make a better connection with the work lead.

**Il grafo afferma:** «Poor work lead connection» **si affronta con** «Clean the cutting surface»

- Giudizio: `C`
- Nota: 

### R003 · Hypertherm Powermax30 AIR, pagina 77

**Il manuale dice:**

> 3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.

**Il grafo afferma:** «Faulty power board or control board» **si affronta con** «Replace the power board»

- Giudizio: `P`
- Nota: La sostituzione della power board dipende dagli esiti dei Test 3 o 2; non vale indistintamente per entrambe le schede possibili.

### R004 · Hypertherm Powermax30 AIR, pagina 96, 100

**Il manuale dice:**

>  Faulty power board (PCB2)

> b. If neither VBUS nor compressor-enable voltage are present on the power board, replace the power board.

**Il grafo afferma:** «Faulty power board (PCB2)» **riguarda il componente** «Power board (PCB2)»

- Giudizio: `C`
- Nota: 

### R005 · Danfoss APF, pagina 64

**Il manuale dice:**

> 6 | No current compensation/Bad current compensation | The CT is not well connected. | Check if the CT wiring is cor- rect.

**Il grafo afferma:** «CT not well connected» **si affronta con** «Check whether the CT wiring is correct» (controllo o test)

- Giudizio: `C`
- Nota: 

### R006 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Restricted line or inadequate air supply»

- Giudizio: `C`
- Nota: 

### R007 · Hypertherm Powermax30 AIR, pagina 94

**Il manuale dice:**

> 9. If the torch parts mentioned in step 7 and step 8 are working properly, the cap-sensor switch is faulty or the torch lead has a broken wire. Replace the faulty part. See Replace the cap-sensor switch on page 204 or Replace the torch lead and strain relief on page 153.

**Il grafo afferma:** «Cap-sensor switch faulty or torch lead has a broken wire» **si affronta con** «Replace the faulty part»

- Giudizio: `C`
- Nota: 

### R008 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Pump fails to operate. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

> Pump fails to operate. | Fluid dried on the displacement rod. | Clean; see Service on pages 12–19.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Fluid dried on the displacement rod»

- Giudizio: `C`
- Nota: 

### R009 · Eastman E-554, pagina 38

**Il manuale dice:**

> c) Check flow control valves on the pen air cylinder.

**Il grafo afferma:** «Pen air cylinder flow control valves need checking» **riguarda il componente** «Pen air cylinder flow control valves»

- Giudizio: `C`
- Nota: 

### R010 · Danfoss APF, pagina 64

**Il manuale dice:**

> 2 | Fuse blowout | The input fuse is broken. | Contact service personnel.

**Il grafo afferma:** «Input fuse is broken» **si affronta con** «Contact service personnel»

- Giudizio: `C`
- Nota: 

### R011 · Eastman E-554, pagina 39

**Il manuale dice:**

> Troubleshooting: 1. Damaged or dirty lens. Check for damage or dirt on the focusing lens. Clean or replace lens as required.

**Il grafo afferma:** «Damaged or dirty focusing lens» **riguarda il componente** «Focusing lens»

- Giudizio: `C`
- Nota: 

### R012 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «The air vents ate blocked» **si affronta con** «Contact service personnel»

- Giudizio: `C`
- Nota: 

### R013 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> * To determine if the fluid hose or gun is obstructed, follow the Pressure Relief Procedure on page 8. Disconnect the fluid hose and place a container at the pump fluid outlet to catch any fluid. Turn on the air just enough to start the pump (about 20–40 psi [0.14–0.3 MPa, 1.4–2.8 bar]). If the pump starts when the air is turned on, the obstruc- tion is in the fluid hose or gun.

**Il grafo afferma:** «Obstruction in the fluid hose or gun» **si affronta con** «Turn on the air just enough to start the pump (about 20–40 psi [0.14–0.3 MPa, 1.4–2.8 bar])» (controllo o test)

- Giudizio: `C`
- Nota: Corretto come singolo passo del test descritto nella nota di p. 11; non è giudicato come procedura autonoma né come riparazione.

### R014 · Hypertherm Powermax30 AIR, pagina 70

**Il manuale dice:**

>  The consumables are stuck in an open or closed position because they are installed incorrectly, worn, or damaged.  The nozzle and electrode are not touching when the torch trigger is pulled. The torch plunger is stuck.  The torch or torch lead has a broken or short-circuited wire. |  Inspect the torch lead. If it is twisted or kinked, straighten it out and try to fire the torch again.  Make sure the consumables are installed correctly. See Step 1 – Install the consumables on page 45.  Inspect the consumables for wear, and replace if necessary. Always replace the nozzle and electrode together.  Perform Test 5 – torch stuck open or torch stuck closed on page 90.

**Il grafo afferma:** «Torch or torch lead has a broken or short-circuited wire» **si affronta con** «Inspect the torch lead and straighten it if twisted or kinked» (controllo o test)

Condizioni: If the lead is twisted or kinked, straighten it and try firing again; if twisted or kinked, straighten and try to fire again

- Giudizio: `C`
- Nota: 

### R015 · Danfoss APF, pagina 64

**Il manuale dice:**

> 5 | Fan Fail | Fan failure. | Contact service personnel.

**Il grafo afferma:** «Fan failure» **(codice) indica la causa** «Fan failure»

- Giudizio: `C`
- Nota: 

### R016 · Eastman E-554, pagina 39

**Il manuale dice:**

> 3. Damage or debris in laser nozzle. Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.

> Loss of laser cutting power Description of Problem: The laser cutting power decreases causing non-cut edges.

**Il grafo afferma:** «Loss of laser cutting power» **può indicare la causa** «Damage or debris in laser nozzle»

- Giudizio: `C`
- Nota: 

### R017 · Eastman E-554, pagina 39

**Il manuale dice:**

> 2. Check for brass laser nozzle alignment. If the tube or nozzle is bent, the laser beam will reflect off the inside wall of the nozzle causing a wide path. To verify, perform a test pulse on a piece of card board. If the dot has a ring or partial ring around it, the nuzzle is bent or the mirrors may need to be adjusted.

**Il grafo afferma:** «Mirrors may need adjustment» **si affronta con** «Perform a test pulse on cardboard and inspect the dot for a ring or partial ring» (controllo o test)

Condizioni: If the mirrors need adjustment

- Giudizio: `P`
- Nota: Il test serve a verificare ugello piegato o specchi da regolare; la necessità di regolare gli specchi non è una precondizione già accertata.

### R018 · Eastman E-554, pagina 38

**Il manuale dice:**

> Laser Fume Extractor has reduced vacuum

> 1. Check the laser fume extractor for power and is turned ON.

> 2. Increase vacuum pressure using the fume extractor control panel.

**Il grafo afferma:** «Unspecified cause of reduced or no laser fume extractor vacuum» **si affronta con** «Clean the vacuum hose and funnel» (riparazione)

- Giudizio: `C`
- Nota: Verificato nel PDF p. 38: nella stessa sezione, il punto 4 prescrive la pulizia del tubo e dell’imbuto.

### R019 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Held open or worn priming piston. | Clear; service.

**Il grafo afferma:** «Held open or worn priming piston» **si affronta con** «Clear and service priming piston»

- Giudizio: `C`
- Nota: 

### R020 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Erratic or accelerated pump speed. | Exhausted fluid supply. | Refill and prime.

**Il grafo afferma:** «Exhausted fluid supply» **si affronta con** «Refill the fluid supply and prime the pump» (riparazione)

- Giudizio: `C`
- Nota: 

### R021 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Worn packings in displacement pump. | Replace packings.

**Il grafo afferma:** «Worn packings in displacement pump» **riguarda il componente** «packings in displacement pump»

- Giudizio: `C`
- Nota: 

### R022 · Eastman E-554, pagina 37

**Il manuale dice:**

> The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off. This is typically caused by an intermittent pause circuit, usually in thestop discs.

> 1.Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure. Remove gantry side cover. Check the pause plunger. Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.

**Il grafo afferma:** «Intermittent pause circuit, usually in the stop discs» **si affronta con** «Loosen the pause plunger to decrease activation pressure» (riparazione)

Condizioni: To decrease activation pressure

- Giudizio: `C`
- Nota: 

### R023 · Eastman E-554, pagina 38

**Il manuale dice:**

> Laser Fume Extractor has reduced vacuum

> An odor is present when cutting with the laser tool or Laser cutting path is wider than normal

> 1. Check the laser fume extractor for power and is turned ON.

**Il grafo afferma:** «Laser cutting path is too wide» **può indicare la causa** «Unspecified cause of reduced or no laser fume extractor vacuum»

- Giudizio: `C`
- Nota: Il PDF p. 38 include il taglio più largo tra i sintomi del vuoto ridotto o assente; non viene qui attribuita una causa specifica.

### R024 · Hypertherm Powermax30 AIR, pagina 94

**Il manuale dice:**

> 7. Make sure the torch plunger moves smoothly. If it does not, replace the torch body. See Replace the torch body on page 201.

**Il grafo afferma:** «Torch plunger does not move smoothly» **può indicare la causa** «Torch plunger does not move smoothly»

- Giudizio: `S`
- Nota: Il manuale collega il movimento anomalo alla sostituzione del corpo torcia, non afferma che il movimento anomalo sia causa di sé stesso.

### R025 · Danfoss APF, pagina 64

**Il manuale dice:**

> 4 | BUS OVP/UVP | BUS capacitor failure. | Contact service personnel.

**Il grafo afferma:** «BUS capacitor failure» **riguarda il componente** «BUS capacitor»

- Giudizio: `C`
- Nota: 

### R026 · Eastman E-554, pagina 38

**Il manuale dice:**

> The Cutting Tool or Pen does not move down Description of Problem: The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut. This can be caused by an electrical short, tool mapping in software or a problem with the power supply.

> 2.Verify the mapping of your tools and layers are mapped properly under each tool.

> a)Look at the tool bar at the bottom of the Cut window to

**Il grafo afferma:** «Tool mapping in software is incorrect» **si affronta con** «Verify tool and layer mapping under each tool» (controllo o test)

- Giudizio: `C`
- Nota: 

### R027 · Hypertherm Powermax30 AIR, pagina 69

**Il manuale dice:**

> The internal compressor LED and the temperature LED illuminate while the machine is powered ON and the torch trigger is pulled.

>  The air inlet filter on the internal compressor is completely clogged. For the compressor’s air inlet filter to trigger this LED fault, the filter would have to be so blocked that no air can flow through it. | 6. Replace the compressor’s air inlet filter. See Replace the air inlet filter in the internal compressor on page 174.

**Il grafo afferma:** «The internal compressor LED and the temperature LED illuminate» **può indicare la causa** «The air inlet filter on the internal compressor is completely clogged»

- Giudizio: `P`
- Nota: Manca la condizione diagnostica: macchina accesa e grilletto della torcia premuto; la sola accensione dei due LED amplia il caso.

### R028 · Danfoss APF, pagina 64

**Il manuale dice:**

> 6 | No current compensation/Bad current compensation | The CT is not well connected. | Check if the CT wiring is cor- rect.

**Il grafo afferma:** «No current compensation/bad current compensation» **(codice) indica la causa** «CT not well connected»

- Giudizio: `C`
- Nota: 

### R029 · Danfoss APF, pagina 64

**Il manuale dice:**

> 4 | BUS OVP/UVP | BUS capacitor failure. | Contact service personnel.

**Il grafo afferma:** «BUS OVP/UVP» **(codice) indica la causa** «BUS capacitor failure»

- Giudizio: `C`
- Nota: 

### R030 · Hypertherm Powermax30 AIR, pagina 70

**Il manuale dice:**

>  The cap-sensing circuit is open due to:  The consumables are loose, incorrectly installed, or missing. OR  The cap-sensor switch, torch lead, or torch body is faulty. |  Make sure the consumables are installed correctly.  Perform Test 7 – torch cap-sensor on page 94.

**Il grafo afferma:** «Cap-sensor switch, torch lead, or torch body is faulty» **riguarda il componente** «Cap-sensor switch»

Condizioni: if faulty

- Giudizio: `C`
- Nota: 

### R031 · Eastman E-554, pagina 13

**Il manuale dice:**

> For customers using RF welders or other equipment that emits RF, Eastman Machine Company recommends that this equipment be kept at least 70 feet away from the Eastman cutting system. High levels of RF emissions may cause the electronic controls in the system to malfunction. Please note that interference and damage, caused by RF emissions from equipment that is not stationed at least 70 feet away, may not be covered under the warranty of your Eastman cutting system.

**Il grafo afferma:** «High RF emissions from nearby equipment» **si affronta con** «Keep RF-emitting equipment at least 70 feet away»

- Giudizio: `C`
- Nota: Il valore di 70 piedi è quello della raccomandazione testuale citata; il giudizio riguarda questo singolo fatto.

### R032 · Danfoss APF, pagina 20

**Il manuale dice:**

> 2 | Tri-color LED (Yellow/red flash alternately) | • (Single module connected) The device is malfunctioning and in standby mode. • Some devices are malfunctioning and others are in standby mode.

**Il grafo afferma:** «Yellow and red indicators flash alternately» **può indicare la causa** «Some devices malfunctioning and others in standby mode»

Condizioni: Some devices

- Giudizio: `C`
- Nota: 

### R033 · Eastman E-554, pagina 38

**Il manuale dice:**

> 6.The Pen or Tool delays coming down and misses the beginning of marker or cut.

> c) Check flow control valves on the pen air cylinder.

> The Cutting Tool or Pen does not move down Description of Problem: The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut. This can be caused by an electrical short, tool mapping in software or a problem with the power supply.

**Il grafo afferma:** «Cutting tool or pen does not move down, or is delayed» **può indicare la causa** «Pen air cylinder flow control valves need checking»

Condizioni: For a tool or pen delayed coming down and missing the beginning of a marker or cut; When the pen or tool delays coming down and misses the beginning of a marker or cut

- Giudizio: `S`
- Nota: A p. 38 è prescritto di controllare le valvole: il bisogno di un controllo non è una causa dichiarata del ritardo della penna o utensile.

### R034 · Eastman E-554, pagina 37

**Il manuale dice:**

> 3) Remove finger after the "Power On Setup" screen appears.

> Troubleshooting: Touch screen calibration in required. Proceed as follows. 1) Power down the cutting system.

> 4) Using the left and right arrows to navigate, go to the Calibration Screen (screen page 2). Press Touch screen to begin calibrating.

**Il grafo afferma:** «Touch screen calibration required» **si affronta con** «Calibrate the touch screen»

- Giudizio: `C`
- Nota: 

### R035 · Danfoss APF, pagina 20

**Il manuale dice:**

> 2 | Tri-color LED (Green/yellow flash alter- nately) | Multiple modules connected. Some de- vices are operating and others are in standby mode.

**Il grafo afferma:** «Green and yellow indicators flash alternately» **può indicare la causa** «Some devices operating and others in standby mode»

Condizioni: Multiple modules connected

- Giudizio: `C`
- Nota: 

### R036 · Hypertherm Powermax30 AIR, pagina 77

**Il manuale dice:**

> 3 | Faulty power board or control board | • Perform Test 3 – VBUS and voltage balance on power board on page 86. If any of the values are incorrect, replace the power board. • Perform Test 2 – power board voltage checks on page 84. If any of the values for pins 5, 7, or 12 are incorrect, remove the control board and test again. If the values are correct, replace the control board. • If the values for pins 5, 7, or 12 are correct when you perform Test 2 – power board voltage checks on page 84 but any other values from Test 2 are incorrect, replace the power board.

**Il grafo afferma:** «Faulty power board or control board» **si affronta con** «Replace the control board»

- Giudizio: `P`
- Nota: Occorre prima verificare i pin 5, 7 o 12, rimuovere la control board e ripetere il test: sostituirla solo se i valori tornano corretti.

### R037 · Danfoss APF, pagina 42

**Il manuale dice:**

> 4 | LED indicators | Module status indicator: • Green (Normal): The module operates normally. • Yellow (Standby): The module is in standby mode. • Red (Fault): The module is malfunctioning.

**Il grafo afferma:** «Red module status LED» **può indicare la causa** «Module malfunction»

- Giudizio: `C`
- Nota: 

### R038 · Eastman E-554, pagina 37

**Il manuale dice:**

> alignment Description of Problem: The touch screen buttons do not match where the screen needs to be touched to activate the command. Operator needs to push above, below, right or left of the button for the command to take effect.

> Troubleshooting: Touch screen calibration in required. Proceed as follows. 1) Power down the cutting system.

**Il grafo afferma:** «Touch screen calibration required» **riguarda il componente** «Touch screen»

- Giudizio: `C`
- Nota: 

### R039 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «Ambient OTP» **(codice) indica la causa** «The fans do not work»

- Giudizio: `C`
- Nota: 

### R040 · Hypertherm Powermax30 AIR, pagina 83

**Il manuale dice:**

> 6. If the AC voltage is incorrect, make sure you have power to the unit. If you do have power, inspect the power cord for damage, and replace if necessary. See Replace the power cord and strain relief on page 115.

**Il grafo afferma:** «Damaged power cord» **si affronta con** «Replace the damaged power cord» (riparazione)

Condizioni: If the power cord is damaged; If the power cord is damaged.

- Giudizio: `C`
- Nota: 

### R041 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «Ambient OTP» **(codice) indica la causa** «The air vents ate blocked»

- Giudizio: `C`
- Nota: 

### R042 · Eastman E-554, pagina 37

**Il manuale dice:**

> tional pause Description of Problem: The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off. This is typically caused by an intermittent pause circuit, usually in thestop discs.

**Il grafo afferma:** «Intermittent pause circuit» **riguarda il componente** «Stop discs»

- Giudizio: `C`
- Nota: 

### R043 · Hypertherm Powermax30 AIR, pagina 69

**Il manuale dice:**

> The internal compressor LED and the temperature LED blink alternately when the machine is powered ON.

>  The system was powered on with the torch trigger being pulled.  The start circuit is stuck closed. |  Release the torch trigger and reset the system by turning it OFF (O) and then turning it ON (I) again. The system automatically disables itself when the power supply is turned on while the torch trigger is pulled.  Perform Test 6 – plasma start on page 92.

**Il grafo afferma:** «Internal compressor and temperature LEDs blink alternately when powered on» **può indicare la causa** «System powered on while the torch trigger was pulled»

- Giudizio: `C`
- Nota: 

### R044 · Hypertherm Powermax30 AIR, pagina 56

**Il manuale dice:**

>  Cut quality is poor. The causes can be:

>  Worn or damaged consumables

>  Worn or damaged consumables may produce intermittent dross.

**Il grafo afferma:** «Cut quality is poor» **può indicare la causa** «Consumables are worn or damaged»

- Giudizio: `C`
- Nota: 

### R045 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Fluid dried on the displacement rod. | Clean; see Service on pages 12–19.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Fluid dried on the displacement rod»

- Giudizio: `C`
- Nota: Verificata nel PDF p. 11 l’intestazione condivisa: il fluido secco sullo stelo appartiene a “Pump fails to operate”.

### R046 · Hypertherm Powermax30 AIR, pagina 61

**Il manuale dice:**

> 3. Inspect the consumables for damage or wear.

> 4. Repair or replace components as necessary.

**Il grafo afferma:** «Consumables are worn or damaged» **si affronta con** «Repair or replace damaged or worn consumables as necessary» (controllo o test)

Condizioni: If problem persists and excess moisture is not an issue; if problem persists and excess moisture is not an issue; replace if worn or damaged

- Giudizio: `P`
- Nota: Riparare o sostituire è un intervento correttivo, non un controllo/test; l’etichetta dell’azione ne altera il significato.

### R047 · Danfoss APF, pagina 64

**Il manuale dice:**

> Regularly clean the Active Power Filter, especially the slits, openings, and filters, to ensure that the air freely flows into the Active Power

> Filter to avoid overheating. If necessary, use an air blower or vacuum cleaner to clean the slits, and openings and replace the filters

> regularly to avoid any object from blocking or covering these areas.

**Il grafo afferma:** «Airflow openings blocked or covered» **si affronta con** «Clean the slits and openings with an air blower or vacuum cleaner» (riparazione)

- Giudizio: `C`
- Nota: 

### R048 · Eastman E-554, pagina 38

**Il manuale dice:**

> a) Hit the Cut Down button on the UIT to verify the

> corresponding green LED light is on. Located on the slice output cards (non-operator gantry side plate).

> The Cutting Tool or Pen does not move down Description of Problem: The tool or Pen does not move down when cutting a file or they are delayed coming down at the beginning of a cut. This can be caused by an electrical short, tool mapping in software or a problem with the power supply.

**Il grafo afferma:** «Power supply problem» **si affronta con** «Press UIT Cut Down and verify the corresponding slice output card green LED is on» (controllo o test)

Condizioni: Press Cut Down on the UIT; verify the corresponding green LED on the slice output cards

- Giudizio: `S`
- Nota: Nel PDF p. 38 il LED delle slice output cards verifica le connessioni utensile (5a); l’alimentatore a 24 V ha controlli distinti (6a–b).

### R049 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Dirty or worn air motor parts. | Clean or repair; see separate air motor manual.

**Il grafo afferma:** «Dirty or worn air motor parts» **riguarda il componente** «air motor parts»

- Giudizio: `C`
- Nota: 

### R050 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «The fans do not work» **si affronta con** «Contact service personnel»

- Giudizio: `C`
- Nota: 

### R051 · Hypertherm Powermax30 AIR, pagina 88

**Il manuale dice:**

> 9. The values found in step 7 and step 8 should be approximately equal. If they differ by more than 30 V, replace the power board.

**Il grafo afferma:** «Power board voltage imbalance» **si affronta con** «Replace the power board»

- Giudizio: `P`
- Nota: Manca la soglia decisiva: sostituire la scheda solo se le due misure dei passi 7 e 8 differiscono di oltre 30 V.

### R052 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Pump operates, but output is low on both strokes. | Restricted line or inadequate air supply. | Clear*; see Technical Data on pages 24–27.

**Il grafo afferma:** «Restricted line or inadequate air supply» **riguarda il componente** «Air supply»

- Giudizio: `C`
- Nota: 

### R053 · Danfoss APF, pagina 64

**Il manuale dice:**

> Some components like power capacitors and fans become worn out due to long term usage, and increase the risk of failure on the Active

**Il grafo afferma:** «Worn power capacitors and fans increase failure risk» **riguarda il componente** «Power capacitors»

Condizioni: Due to long-term usage; increases risk of filter failure.; due to long-term usage

- Giudizio: `C`
- Nota: 

### R054 · Eastman E-554, pagina 37

**Il manuale dice:**

> alignment Description of Problem: The touch screen buttons do not match where the screen needs to be touched to activate the command. Operator needs to push above, below, right or left of the button for the command to take effect.

> The buttons on the Touch Screen are out of

> Troubleshooting: Touch screen calibration in required. Proceed as follows. 1) Power down the cutting system.

**Il grafo afferma:** «Touch screen buttons out of alignment» **può indicare la causa** «Touch screen calibration required»

- Giudizio: `C`
- Nota: 

### R055 · Danfoss APF, pagina 64

**Il manuale dice:**

> 1 | SYS 485 comm loss | 1 The communication wire is not well connected. 2 The Active Power Filter modules have repeated IDs. | 1 Check if the communication wire is firmly connected. 1 Check the DIP switches of the individual modules.

**Il grafo afferma:** «SYS 485 communication loss» **(codice) indica la causa** «Communication wire not firmly connected»

- Giudizio: `C`
- Nota: 

### R056 · Eastman E-554, pagina 37

**Il manuale dice:**

> tional pause Description of Problem: The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off. This is typically caused by an intermittent pause circuit, usually in thestop discs.

**Il grafo afferma:** «Machine Stop during Cut Due to Unintentional pause» **può indicare la causa** «Intermittent pause circuit»

- Giudizio: `C`
- Nota: 

### R057 · Hypertherm Powermax30 AIR, pagina 83

**Il manuale dice:**

> 6. If the AC voltage is incorrect, make sure you have power to the unit. If you do have power, inspect the power cord for damage, and replace if necessary. See Replace the power cord and strain relief on page 115.

> 9. Measure the AC voltage from J1 to J2 (labeled “AC” on the back of the power board). This value should be the same as the incoming line voltage. If it is not, check the power switch and replace if necessary. See Replace the power switch on page 124.

**Il grafo afferma:** «Incorrect AC voltage» **può indicare la causa** «Faulty power switch»

Condizioni: If voltage from J1 to J2 is not the same as incoming line voltage, after power source and power cord are confirmed functioning.

- Giudizio: `C`
- Nota: Verificato nel PDF p. 83: i passi 7–9 conservano il controllo preliminare di sorgente e cavo e la misura J1–J2.

### R058 · Danfoss APF, pagina 64

**Il manuale dice:**

> 5 | Fan Fail | Fan failure. | Contact service personnel.

**Il grafo afferma:** «Fan failure» **(codice) indica la causa** «Fan failure»

- Giudizio: `C`
- Nota: 

### R059 · Hypertherm Powermax30 AIR, pagina 68, 70

**Il manuale dice:**

>  Environmental conditions or worn consumables are adversely affecting the power supply’s performance. | 2. Make sure the louvers in the cover are not blocked. Blocking the louvers in the cover can prevent proper air circulation needed to cool internal components. 3. Place the power supply right-side up on a level surface. Do NOT lay the power supply on its side. Laying the power supply on its side can cause the air filter to divert air away from the torch. 4. Inspect and replace the consumables if they are worn or damaged. Always replace the nozzle and electrode together. 5. Was the system stored in temperatures below freezing? If so, ice might have formed in the air-flow system inside the power supply. Move the power supply to a warmer location to allow the ice to melt.

>  The torch was repeatedly fired with worn out consumables.  The inverter is saturated (is in an over-current condition). |  Install new consumables in the torch (they may be corroded or approaching end of life).  If you continue to see this error, replace the power board. See Replace the power board on page 135.

**Il grafo afferma:** «Torch repeatedly fired with worn-out consumables» **riguarda il componente** «Consumables»

- Giudizio: `C`
- Nota: 

### R060 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Dirty or worn air motor parts. | Clean or repair; see separate air motor manual.

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Dirty or worn air motor parts»

- Giudizio: `C`
- Nota: Verificata nel PDF p. 11 la riga del motore pneumatico sotto “Pump fails to operate”.

### R061 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «Ambient overtemperature» **(codice) indica la causa** «Blocked air vents»

- Giudizio: `C`
- Nota: 

### R062 · Danfoss APF, pagina 64

**Il manuale dice:**

> 2 | Fuse blowout | The input fuse is broken. | Contact service personnel.

**Il grafo afferma:** «Fuse blowout» **(codice) indica la causa** «Input fuse is broken»

- Giudizio: `C`
- Nota: 

### R063 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «Ambient OTP» **(codice) indica la causa** «Air vents are blocked»

- Giudizio: `C`
- Nota: 

### R064 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Fluid dried on the displacement rod. | Clean; see Service on pages 12–19.

**Il grafo afferma:** «Fluid dried on the displacement rod» **si affronta con** «Clean displacement rod»

- Giudizio: `C`
- Nota: 

### R065 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump operates, but output is low on down- stroke. | Fluid too heavy for pump priming. | Use bleeder valve (see page 9); use wiper plate with ram or pneumatic elevator cart.

**Il grafo afferma:** «Fluid too heavy for pump priming» **si affronta con** «Use bleeder valve and wiper plate with ram or pneumatic elevator cart»

- Giudizio: `C`
- Nota: 

### R066 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> * To determine if the fluid hose or gun is obstructed, follow the Pressure Relief Procedure on page 8. Disconnect the fluid hose and place a container at the pump fluid outlet to catch any fluid. Turn on the air just enough to start the pump (about 20–40 psi [0.14–0.3 MPa, 1.4–2.8 bar]). If the pump starts when the air is turned on, the obstruc- tion is in the fluid hose or gun.

> Pump fails to operate. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

> Pump operates, but output is low on both strokes. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

**Il grafo afferma:** «Obstructed fluid hose or gun/valve, or fluid hose ID too small» **riguarda il componente** «Gun/valve»

- Giudizio: `C`
- Nota: 

### R067 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Held open or worn intake valve or seals. | Clear valve; replace seals.

**Il grafo afferma:** «Held open or worn intake valve or seals» **si affronta con** «Clear valve and replace seals»

- Giudizio: `C`
- Nota: 

### R068 · Hypertherm Powermax30 AIR, pagina 103

**Il manuale dice:**

> Replace damaged or defective parts as needed. See page 215 for replacement kit numbers.

> 18. Also check for leaks where the drain hose connects to the base of the power supply . Tilt the power supply so that you can feel if air is escaping through the hole in the base where the drain hose lets out.

> 19. Install a different torch to see if the low pressure issue persists. See page 153.

**Il grafo afferma:** «Unspecified cause of low air pressure» **si affronta con** «Perform a test cut and check pressure gauge reading» (controllo o test)

Condizioni: During a test cut sustaining a plasma arc for several seconds; expected reading is 2.9–3.4 bar (42–50 psi); pressure is lower during postflow; During the test cut, sustain a plasma arc for several seconds; pressure should read 2.9–3.4 bar (42–50 psi); pressure is lower during postflow

- Giudizio: `C`
- Nota: Verificato nel PDF p. 103, passo 11: taglio di prova, intervallo 2,9–3,4 bar e pressione inferiore in postflow sono presenti.

### R069 · Danfoss APF, pagina 64

**Il manuale dice:**

> 3 | Ambient OTP | 1 The air vents ate blocked. 2 The fans do not work. | Contact service personnel.

**Il grafo afferma:** «Air vents are blocked» **riguarda il componente** «air vents»

- Giudizio: `C`
- Nota: 

### R070 · Eastman E-554, pagina 37

**Il manuale dice:**

> Machine Stop during Cut Due to Uninten-

> The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off. This is typically caused by an intermittent pause circuit, usually in thestop discs.

**Il grafo afferma:** «Machine stops mid-cut and displays “Machine Paused, Press Zero, Next or Abort”» **può indicare la causa** «Intermittent pause circuit, usually in the stop discs»

- Giudizio: `C`
- Nota: 

### R071 · Hypertherm Powermax30 AIR, pagina 103

**Il manuale dice:**

> 20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new air compressor. See page 169.

**Il grafo afferma:** «Low pressure persists after completing all checks» **può indicare la causa** «Faulty internal air compressor»

- Giudizio: `C`
- Nota: 

### R072 · Eastman E-554, pagina 37

**Il manuale dice:**

> Touch screen calibration in required. Proceed as follows. 1) Power down the cutting system.

> 4) Using the left and right arrows to navigate, go to the Calibration Screen (screen page 2). Press Touch screen to begin calibrating.

**Il grafo afferma:** «Touch screen calibration is incorrect» **si affronta con** «Navigate to calibration screen page 2 and press Touch screen» (riparazione)

- Giudizio: `C`
- Nota: Il PDF p. 37 prescrive questo passo per avviare la calibrazione; non lo interpreto come l’intera procedura di calibrazione.

### R073 · Eastman E-554, pagina 39

**Il manuale dice:**

> 3. Damage or debris in laser nozzle. Check for damage or debris in laser nozzle. Clean or replace laser nozzle as required.

> Loss of laser cutting power Description of Problem: The laser cutting power decreases causing non-cut edges.

**Il grafo afferma:** «Loss of laser cutting power» **può indicare la causa** «Damage or debris in laser nozzle»

- Giudizio: `C`
- Nota: 

### R074 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump operates, but output is low on down- stroke. | Held open or worn intake valve or seals. | Clear valve; replace seals.

**Il grafo afferma:** «Intake valve held open or worn, or seals worn» **si affronta con** «Replace the intake valve seals» (riparazione)

- Giudizio: `C`
- Nota: La riga prescrive “replace seals”: il singolo intervento è corretto, senza giudicare qui l’eventuale presenza degli altri passi.

### R075 · Danfoss APF, pagina 64

**Il manuale dice:**

> 4 | BUS OVP/UVP | BUS capacitor failure. | Contact service personnel.

**Il grafo afferma:** «BUS capacitor failure» **si affronta con** «Contact service personnel»

- Giudizio: `C`
- Nota: 

### R076 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Pump operates, but output is low on both strokes. | Restricted line or inadequate air supply. | Clear*; see Technical Data on pages 24–27.

**Il grafo afferma:** «Restricted line or inadequate air supply» **si affronta con** «Clear the restricted line» (riparazione)

- Giudizio: `C`
- Nota: 

### R077 · Eastman E-554, pagina 39

**Il manuale dice:**

> 2. Damaged or dirty Mirror. Check for damage, burn mark or dirt on the beam deflecting mirrors. Clean or replace mirrors as required.

> Loss of laser cutting power Description of Problem: The laser cutting power decreases causing non-cut edges.

**Il grafo afferma:** «Loss of laser cutting power» **può indicare la causa** «Damaged or dirty mirror»

- Giudizio: `C`
- Nota: 

### R078 · Eastman E-554, pagina 39

**Il manuale dice:**

> Troubleshooting: 1. Damaged or dirty lens. Check for damage or dirt on the focusing lens. Clean or replace lens as required.

> Loss of laser cutting power Description of Problem: The laser cutting power decreases causing non-cut edges.

**Il grafo afferma:** «Loss of laser cutting power» **può indicare la causa** «Damaged or dirty focusing lens»

- Giudizio: `C`
- Nota: 

### R079 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Obstructed fluid hose or gun/valve; fluid hose ID is too small»

- Giudizio: `C`
- Nota: 

### R080 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Pump fails to operate. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

> Pump fails to operate. | Fluid dried on the displacement rod. | Clean; see Service on pages 12–19.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Dirty or worn air motor parts»

- Giudizio: `C`
- Nota: Verificato nel PDF p. 11: la riga successiva all’estratto indica “Dirty or worn air motor parts” per lo stesso problema.

### R081 · Danfoss APF, pagina 64

**Il manuale dice:**

> 1 | SYS 485 comm loss | 1 The communication wire is not well connected. 2 The Active Power Filter modules have repeated IDs. | 1 Check if the communication wire is firmly connected. 1 Check the DIP switches of the individual modules.

**Il grafo afferma:** «Communication wire not firmly connected» **si affronta con** «Check that the communication wire is firmly connected» (controllo o test)

- Giudizio: `C`
- Nota: 

### R082 · Hypertherm Powermax30 AIR, pagina 89

**Il manuale dice:**

> 7. Remove the valve’s connector from J6 on the power board.

> 8. Measure the voltage between pin 1 of J6 (red wire) and ground.

> 9. If you do not hear the valve click and the voltage check reads 24 VDC, replace the solenoid valve. See Replace the solenoid valve on page 151.

**Il grafo afferma:** «Faulty solenoid valve» **si affronta con** «Test solenoid valve click and J6 pin 1 voltage» (controllo o test)

- Giudizio: `C`
- Nota: 

### R083 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Worn packings in displacement pump. | Replace packings.

**Il grafo afferma:** «Worn packings in displacement pump» **riguarda il componente** «packings in displacement pump»

- Giudizio: `C`
- Nota: 

### R084 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> * To determine if the fluid hose or gun is obstructed, follow the Pressure Relief Procedure on page 8. Disconnect the fluid hose and place a container at the pump fluid outlet to catch any fluid. Turn on the air just enough to start the pump (about 20–40 psi [0.14–0.3 MPa, 1.4–2.8 bar]). If the pump starts when the air is turned on, the obstruc- tion is in the fluid hose or gun.

> Pump fails to operate. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

> Pump operates, but output is low on both strokes. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

**Il grafo afferma:** «Obstructed fluid hose or gun/valve, or fluid hose ID too small» **si affronta con** «Use a fluid hose with a larger ID» (riparazione)

- Giudizio: `C`
- Nota: 

### R085 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Pump operates, but output is low on up- stroke. | Held open or worn piston valve or seals. | Clear valve; replace seals.

> Erratic or accelerated pump speed. | Held open or worn piston valve or seals. | Clear valve; replace seals.

**Il grafo afferma:** «Piston valve held open or worn, or seals worn» **si affronta con** «Replace the piston valve seals» (riparazione)

- Giudizio: `C`
- Nota: La sostituzione delle tenute è esplicita nelle due righe; qui si giudica questo solo intervento.

### R086 · Danfoss APF, pagina 64

**Il manuale dice:**

> 5 | Fan Fail | Fan failure. | Contact service personnel.

**Il grafo afferma:** «Fan Fail» **(codice) indica la causa** «Fan failure»

- Giudizio: `C`
- Nota: 

### R087 · Hypertherm Powermax30 AIR, pagina 77

**Il manuale dice:**

> 6 | Inverter saturation | • Install new consumables in the torch. If you continue to see this error code, replace the power board.

**Il grafo afferma:** «Inverter saturation» **si affronta con** «Install new consumables in the torch»

- Giudizio: `C`
- Nota: 

### R088 · Hypertherm Powermax30 AIR, pagina 77

**Il manuale dice:**

> 4 | Faulty fan, solenoid valve, or power board | • Perform Test 4 – solenoid valve on page 89 and Test 8 – fan on page 95. If the solenoid valve test and the fan test both pass, replace the power board. If Test 4 fails, replace the solenoid valve; if Test 8 fails, replace the fan.

**Il grafo afferma:** «Faulty fan, solenoid valve, or power board» **si affronta con** «Replace the solenoid valve»

- Giudizio: `P`
- Nota: La valvola va sostituita solo se fallisce il Test 4; il gruppo di tre possibili guasti non autorizza questa sostituzione senza tale esito.

### R089 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Erratic or accelerated pump speed. | Exhausted fluid supply. | Refill and prime.

**Il grafo afferma:** «Exhausted fluid supply» **si affronta con** «Prime the pump» (riparazione)

- Giudizio: `C`
- Nota: L’adescamento è un intervento esplicito di “Refill and prime”; non si assume che il grafo lo proponga come unica operazione.

### R090 · Hypertherm Powermax30 AIR, pagina 103

**Il manuale dice:**

> 19. Install a different torch to see if the low pressure issue persists. See page 153.

> 20. If low pressure persists after you complete all of these checks, the internal air compressor may be faulty. Install a new air compressor. See page 169.

> 16. If the air pressure was low, check the air compressor for proper voltage (15 V). See Test 9a – Check the diagnostic LED (D5) on the compressor-driver board on page 96.

**Il grafo afferma:** «Low air pressure affecting system performance» **può indicare la causa** «Low air compressor voltage»

Condizioni: If air pressure was low; If low pressure persists after all checks

- Giudizio: `P`
- Nota: La persistenza dopo tutti i controlli riguarda il sospetto sul compressore al passo 20, non la verifica dei 15 V prescritta al passo 16.

### R091 · Eastman E-554, pagina 39

**Il manuale dice:**

> Troubleshooting: 1. Damaged or dirty lens. Check for damage or dirt on the focusing lens. Clean or replace lens as required.

> Loss of laser cutting power Description of Problem: The laser cutting power decreases causing non-cut edges.

**Il grafo afferma:** «Loss of laser cutting power» **può indicare la causa** «Damaged or dirty lens»

- Giudizio: `C`
- Nota: 

### R092 · Eastman E-554, pagina 39

**Il manuale dice:**

> 2. Check for brass laser nozzle alignment. If the tube or nozzle is bent, the laser beam will reflect off the inside wall of the nozzle causing a wide path. To verify, perform a test pulse on a piece of card board. If the dot has a ring or partial ring around it, the nuzzle is bent or the mirrors may need to be adjusted.

**Il grafo afferma:** «Mirrors may need adjustment» **riguarda il componente** «Mirrors»

- Giudizio: `C`
- Nota: 

### R093 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> Erratic or accelerated pump speed. | Exhausted fluid supply. | Refill and prime.

**Il grafo afferma:** «Exhausted fluid supply» **si affronta con** «Refill and prime»

- Giudizio: `C`
- Nota: 

### R094 · Eastman E-554, pagina 37

**Il manuale dice:**

> The machine stops in middle of cut and displays message “Machine Paused, Press Zero, Next or Abort” on Touch Screen. When pressing NEXT on the keypad, the machine will continue to cut where it left off. This is typically caused by an intermittent pause circuit, usually in thestop discs.

> 1.Check stop disc activation. The stop discs should not activate by a slight touch or vibration. They should activate only when moved by minimum pressure. Remove gantry side cover. Check the pause plunger. Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.

**Il grafo afferma:** «Intermittent pause circuit, usually in the stop discs» **si affronta con** «Remove the gantry side cover and check the pause plunger» (controllo o test)

- Giudizio: `C`
- Nota: 

### R095 · Graco Check-Mate 200, pagina 11

**Il manuale dice:**

> * To determine if the fluid hose or gun is obstructed, follow the Pressure Relief Procedure on page 8. Disconnect the fluid hose and place a container at the pump fluid outlet to catch any fluid. Turn on the air just enough to start the pump (about 20–40 psi [0.14–0.3 MPa, 1.4–2.8 bar]). If the pump starts when the air is turned on, the obstruc- tion is in the fluid hose or gun.

> Pump fails to operate. | Restricted line or inadequate air supply | Clear*; see Technical Data on pages 24–27.

> Pump fails to operate. | Obstructed fluid hose or gun/valve; fluid hose ID is too small. | Clear*; use a hose with a larger ID.

**Il grafo afferma:** «Pump fails to operate» **può indicare la causa** «Obstructed fluid hose or gun/valve, or fluid hose ID too small»

- Giudizio: `C`
- Nota: 

### R096 · Hypertherm Powermax30 AIR, pagina 94

**Il manuale dice:**

> 6. Measure the resistance from the blue wire (pin 1) to the orange wire (pin 2) . It should measure less than 10 Ω. If it measures high resistance, the cap-sensor switch circuit is open.

> 8. Make sure the consumables are correctly installed. Adjust the consumables if necessary.

**Il grafo afferma:** «Cap-sensor switch circuit is open» **si affronta con** «Make sure the consumables are installed correctly» (controllo o test)

- Giudizio: `C`
- Nota: Verificato nel PDF p. 94: il controllo dei consumabili al passo 8 fa parte della diagnosi del circuito cap-sensor aperto.

## Istruzioni

- `C` corretto: il manuale afferma questo fatto, anche con parole diverse.
- `P` parziale: giusto ma incompleto o impreciso in modo che conta (manca una condizione,
  un'azione è più generica del manuale, un controllo è presentato come riparazione).
- `S` sbagliato: il manuale non lo dice, lo dice di un'altra riga o di un altro problema, o
  dice il contrario.
- `N` non valutabile: il testo mostrato non basta; se puoi, controlla la pagina del PDF e
  giudica, altrimenti lascia `N` e spiega nella nota.

Giudica solo il fatto mostrato, non se il grafo è completo. Una nota breve è utile per `P`, `S` e `N`.
