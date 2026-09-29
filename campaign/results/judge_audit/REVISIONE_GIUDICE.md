# Revisione del giudice dei KPI

40 confronti tra il tuo gold e il grafo, in ordine casuale.

Revisore: Fabio Daniele
Data: 2026-09-29
Tempo totale impiegato (minuti): 40 (stima)

## Come compilare

**Che cosa stai controllando.** Il valutatore dei KPI confronta il tuo gold con il grafo usando un
giudice automatico (tre voti). Un ramo conta come ritrovato solo se il giudice dice «stessa cosa».
Qui rileggi alcune coppie e dici tu se il grafo afferma la stessa cosa del tuo gold. Il foglio è
cieco: non sai che cosa ha risposto il giudice su ogni voce (la risposta è nella chiave, da non aprire).

**Ogni voce ha tre parti.**
- **Il manuale dice:** i segmenti del manuale citati dal gold e dal grafo, con ID e pagina.
- **Riferimento (il tuo gold):** una sola relazione del ramo: *problema → causa* oppure *causa → azione*.
  Il contesto è la tua nota di condizioni per tutto il ramo.
- **Il grafo afferma:** la relazione del grafo messa a confronto. Per *causa → azione* sono elencati
  tutti i passi che il grafo collega a quella causa nella stessa voce del manuale, ciascuno con le sue
  condizioni: valgono insieme.

**Che cosa scrivere** tra gli accenti gravi, al posto di `?`:

- `U` **uguale**: il grafo dice lo stesso fatto del riferimento, anche con parole diverse, con più
  dettagli o con un nome più corto. Un tecnico che usa il grafo arriverebbe allo stesso fatto.
- `S` **sbagliato il sistema**: il grafo dice un'altra cosa, oppure manca una parte che conta
  (un'azione, una condizione, un numero, una direzione, una negazione), oppure unisce parti di voci
  diverse del manuale.
- `G` **gold discutibile**: il grafo è fedele al manuale e la differenza viene dal riferimento
  (troppo specifico, impreciso o sbagliato rispetto al manuale). Spiega nella nota.
- `N` **non valutabile**: il testo mostrato non basta nemmeno guardando il PDF. Spiega nella nota.

**Regole utili.**
- Conta il significato, non le parole. Numeri, unità, codici, direzioni e negazioni devono coincidere.
- Se il riferimento dice «causa non indicata nel manuale» e il grafo ha una causa marcata *non scritta
  nel manuale*, quel nome è una lettura del sistema: giudica il problema e l'azione, non il nome
  della causa.
- Una condizione del tuo contesto non deve comparire su ogni passo; è `S` solo se il grafo la
  contraddice o se un'azione che nel manuale è condizionata («se persiste, contatta l'assistenza») è
  presentata senza la sua condizione.
- Se hai dubbi, apri il PDF alla pagina indicata. Una nota breve è utile per `S`, `G` e `N`.

Quando hai finito: `.venv/bin/python scripts/kg_v3_judge_audit.py --score`
(Tempo previsto: circa 30–45 minuti.)


## Voci

### A001 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

`p29.t1.r3`

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Riferimento (il tuo gold):** problema «Arc is unstable - Poor starting.» → causa non indicata nel manuale

Contesto del ramo: Se tutti i controlli raccomandati per il sintomo sono stati eseguiti e il problema persiste.

**Il grafo afferma:** problema «Arc is unstable and starting is poor» → causa «Cable liner may be the wrong size» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A002 · Haas vertical mill (2023 operator's manual), pagina 160

**Il manuale dice:**

`p160.b23`

> Check Work Probe

`p160.b24`

> Do these steps to make sure the work probe operates correctly:

**Riferimento (il tuo gold):** problema «Check that the work probe operates correctly.» → causa non indicata nel manuale

Contesto del ramo: The probe LED flashes green after activation; touching the stylus produces a beep and red LED; RESET turns the work-probe LED off.

**Il grafo afferma:** problema «Suspected work probe fault» → causa «Work probe does not operate correctly» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: Il PDF dà una procedura di verifica con esiti attesi; non afferma che il probe sia guasto.

### A003 · LG LMH2235ST over-the-range microwave oven, pagina 2, 13

**Il manuale dice:**

`p2.b4`

> a. Do not operate or allow the oven to be operated with the door open.

`p13.b43`

> No key, Not started, Operating O.L, V.M, T.T.M. Check: Open/Short when the door is closed. (Switch) Symptom #2(Door is open): Not turned on O.L Check: Open/Short when the door is open. (Switch)

**Riferimento (il tuo gold):** problema «Oven with door open.» → «The door is open.»

Contesto del ramo: quando la porta è aperta

**Il grafo afferma:** problema «Door open: not turned on O.L.» → causa «Interlock switch open or short with door open» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `G`
- Nota: Il p2 vieta l’uso a porta aperta; il grafo riporta la diagnosi dell’interlock nella tabella p13.

### A004 · LG LMH2235ST over-the-range microwave oven, pagina 16, 17

**Il manuale dice:**

`p16.b1`

> Keypad Failure

`p17.b1`

> Do the keys operate?

`p17.b4`

> 1 Do only the START key and EZ-ON keys operate? (Door should be closed.)

`p17.b5`

> Check PWB Go to No. 4 of this flow chart.

`p17.b7`

> Yes

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Check whether only the START and EZ-ON keys operate, with the door closed.» (controllo)

Ramo del gold: problema «Keypad failure; keys do not operate.». Contesto del ramo: se non operano solo START ed EZ-ON, il diagramma indica di controllare PWB e andare al punto 4

**Il grafo afferma:** causa «Unspecified cause of keys not operating» *(non scritta nel manuale)* → passi:

- «Check PCB» (controllo); condizioni: [if] Only START and EZ-ON keys operate; door closed.

Problemi collegati a questa causa nel grafo: «Keys do not operate»; «Only START and EZ-ON keys operate»

- Giudizio: `S`
- Nota: Nel diagramma, «Yes» al test delle sole START/EZ-ON porta al passo 2; Check PWB è sull’altro ramo.

### A005 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

`p8.b3`

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

`p8.t1.r12`

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

`p8.t1.r3`

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Riferimento (il tuo gold):** «Material too thick.» → azione «Thin the material.» (riparazione)

Ramo del gold: problema «Speed of application too slow.». Contesto del ramo: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6. The material should immediately fold back in as a finger is drawn through its surface.

**Il grafo afferma:** causa «Material too thick» → passi:

- «Thoroughly mix material until it immediately folds back when a finger is drawn through its surface» (riparazione); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «No material output from pump»; «Speed of application too slow»; «Pattern too coarse»

- Giudizio: `G`
- Nota: Per «Speed of application too slow» la soluzione è miscelare; «Thin the material» appartiene alla riga «No material output».

### A006 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

`p8.t1.r11`

> Speed of application too slow | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

`p8.t1.r2`

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

**Riferimento (il tuo gold):** problema «Speed of application too slow.» → «Not enough air pressure to pump.»

Contesto del ramo: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.

**Il grafo afferma:** problema «Speed of application too slow» → causa «Not enough air pressure to pump»

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A007 · Grizzly G0872 CNC laser cutter/engraver, pagina 50

**Il manuale dice:**

`p50.b1`

> Exhaust Fan

`p50.b4`

> To inspect and clean exhaust system:

`p50.b5`

> (step 1) 1. DISCONNECT LASER MACHINE AND EXHAUST FAN SYSTEM FROM POWER!

`p50.b6`

> (step 2) 2. Inspect ducting for evidence of leaks. Patch or replace ducts as required.

**Riferimento (il tuo gold):** problema «Exhaust ducting has leaks.» (codice -) → causa non indicata nel manuale

Contesto del ramo: patch or replace as required

**Il grafo afferma:** problema «Exhaust system maintenance concerns» → causa «Leaking exhaust ducting» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `G`
- Nota: Il manuale chiede di cercare eventuali perdite e ripararle se presenti; il gold le tratta come già accertate.

### A008 · Grizzly G0872 CNC laser cutter/engraver, pagina 52

**Il manuale dice:**

`p52.t1.r3`

> Machine laser has poor cutting or engraving results. | 1. Laser speed, path, or other CNC error exists. 2. Incorrect laser speed or laser power setting. 3. Focus is not set to correct height. 4. Laser is skewed or off-center. 5. Laser path is obstructed by smoke or material. 6. Laser unable to cut or scan workpiece. 7. Laser kerf too wide, and material is poorly cut. 8. Laser head has vibration or lash (workpiece path shows distortion/overlap). 9. Workpiece buckling or moving. 10. Laser output creating sawtooth pattern on cuts or engravings. 11. Laser tube at fault. 12. Transformer, power supply, or controller at fault. | 1. Review RDCam path settings and verify that software is free of errors. 2. Review RDCam power settings and verify that speed/power is set as desired (Page 28). Adjust laser speed/power at machine (Page 35). 3. Inspect/adjust focal length (Page 36). Inspect/adjust table parallelism (Page 52). 4. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Clean laser optics (Page 45). 5. Verify air supply hose is unobstructed and connected to air nozzle. Inspect/replace air pump (Page 22). Verify exhaust ducting is unobstructed and functional (Page 22). 6. Workpiece material beyond machine capability. 7. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Inspect/adjust focal length (Page 36). Inspect/ adjust table parallelism (Page 52). 8. Adjust/replace belts (Page 51). Inspect/adjust linkage, tracks, and guides for loose fasteners or binding. Reset origin (Page 34). 9. Use honeycomb table for thin workpiece support. Use clamps to secure large or irregular workpieces. 10. Increase laser power (Page 35). Workpiece may contain impurities that ignite, ejecting particles of molten material. 11. Replace laser tube (Page 52). Replace laser tube power supply. 12. Inspect/replace transformer, power supply, or controller, as required.

**Riferimento (il tuo gold):** problema «Machine laser has poor cutting or engraving results.» (codice -) → «Laser path is obstructed by smoke or material.»

Contesto del ramo: see Page 22

**Il grafo afferma:** problema «Machine has poor cutting or engraving results» → causa «Laser kerf too wide and material poorly cut»

Condizioni: nessuna

- Giudizio: `S`
- Nota: Il riferimento è la causa 5 (percorso ostruito), mentre il grafo collega la causa 7 (kerf troppo largo).

### A009 · LG LMH2235ST over-the-range microwave oven, pagina 2

**Il manuale dice:**

`p2.b10`

> microwave generation and transmission systems shall be repaired, replaced, or adjusted by procedures described in this manual before the oven is released to the owner.

`p2.b15`

> • Routine service safety procedures should be exercised at all times.

`p2.b16`

> • Untrained personnel should not attempt service without a thorough review of the test procedures and safety information contained in this manual.

`p2.b4`

> a. Do not operate or allow the oven to be operated with the door open.

`p2.b9`

> d. Any defective or misadjusted components in the interlock, monitor, door seal, and [p2.b10] microwave generation and transmission systems shall be repaired, replaced, or adjusted by procedures described in this manual before the oven is released to the owner.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «If personnel are untrained, review the test procedures and safety information before service.» (controllo)

Ramo del gold: problema «Safety checks before activating the magnetron or another microwave source.». Contesto del ramo: prima di attivare il magnetron o altra sorgente a microonde; personale non addestrato non deve intervenire senza prima aver studiato procedure e informazioni di sicurezza

**Il grafo afferma:** causa «Defective or misadjusted components in the microwave generation and transmission systems» → passi:

- «Repair, replace, or adjust defective or misadjusted microwave generation and transmission system components by procedures described in the manual.» (riparazione); condizioni: [prerequisite] Complete repairs before releasing the oven to the owner.

Problemi collegati a questa causa nel grafo: nessuno

- Giudizio: `S`
- Nota: Il gold chiede la revisione delle procedure per il personale non addestrato; il grafo assegna una riparazione diversa.

### A010 · Grizzly G0872 CNC laser cutter/engraver, pagina 51

**Il manuale dice:**

`p51.b2`

> Review the troubleshooting procedures in this section if a problem develops with your machine. If you need replacement parts or additional help with a procedure, call our Technical Support. Note: Please gather the serial number and manufacture date of your machine before calling.

`p51.t1.r2`

> Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | 1. Emergency stop button depressed/at fault. 2. Incorrect power supply voltage or circuit size. 3. Power supply circuit breaker tripped or fuse blown. 4. Air pump, water chiller, or exhaust fan have a short. 5. Wiring broken, disconnected, or corroded. 6. Machine chassis ground at fault. 7. Laser tube at fault. 8. Power supply or controller at fault. 9. Computer board at fault. | 1. Rotate emergency stop button head to reset. Replace if at fault. 2. Ensure correct power supply voltage and circuit size. 3. Ensure circuit is sized correctly and free of shorts. Reset circuit breaker or replace fuse. 4. Inspect/replace if at fault. 5. Fix broken wires or disconnected/corroded connections. 6. Machine must be connected to a dedicated ground rod at/or near machine (Page 15). 7. Inspect for evidence of arcing at laser tube connections. Verify wire insulation is preventing arcing and discharge to machine frame. 8. Inspect/replace if at fault (Page 63). 9. Inspect/replace if at fault (Page 63).

**Riferimento (il tuo gold):** «Air pump, water chiller, or exhaust fan have a short.» → azione «Inspect the air pump, water chiller, or exhaust fan.» (controllo)

Ramo del gold: problema «Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems.» (codice -). Contesto del ramo: replace if at fault

**Il grafo afferma:** causa «Power supply circuit breaker tripped or fuse blown» → passi:

- «Ensure circuit is correctly sized and free of shorts» (controllo); condizioni: nessuna
- «Reset circuit breaker» (riparazione); condizioni: nessuna
- «Replace blown fuse» (riparazione); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Machine does not start or breaker trips immediately»

- Giudizio: `S`
- Nota: Il grafo collega i rimedi per fusibile/interruttore (causa 3), non l’ispezione di pompa, chiller o ventola (causa 4).

### A011 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

`p8.b3`

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

`p8.t1.r14`

> Speed of application too slow | Hose plugged or too small. | Relieve Pressure, page 6. Clean hose, or try a 1-1/4 in. hose.

**Riferimento (il tuo gold):** «Hose plugged or too small.» → azione «Relieve pressure using the procedure on page 6.» (controllo)

Ramo del gold: problema «Speed of application too slow.». Contesto del ramo: Before any troubleshooting procedure, follow the Pressure Relief procedure on page 6.

**Il grafo afferma:** causa «Hose plugged or too small» → passi:

- «Clean hose or try a 1-1/4 in. hose» (riparazione); condizioni: [prerequisite] Relieve pressure before cleaning the hose.

Problemi collegati a questa causa nel grafo: «Speed of application too slow»

- Giudizio: `U`
- Nota: 

### A012 · Grizzly G0872 CNC laser cutter/engraver, pagina 39, 40

**Il manuale dice:**

`p39.b19`

> (step 2) 2. Highlight "TrackFrame" in job setup screen (see Figure 61).

`p40.b1`

> (step 3) 3. Review .RD file using RDCam, and position workpiece so queued image fits within work­ ing envelope.

`p40.b12`

> If "XSlop Over," "YSlop Over," or "Frame slop" errors are displayed on screen, the machine has determined that the currently queued image is outside the work­ ing envelope, based on current origin (see Figures 63–64).

`p40.b2`

> (step 4) 4. Move laser head assembly to location of ori­ gin defined in RDCam, in reference to work­ ing envelope.

`p40.b3`

> For example, if operator set origin to center of image in RDCam software, position laser head assembly over center of table.

`p40.b4`

> (step 5) 5. Press Origin button. Machine will beep to indicate origin has been set.

**Riferimento (il tuo gold):** «the currently queued image is outside the working envelope, based on current origin» → azione «Highlight "TrackFrame" in the job setup screen.» (controllo)

Ramo del gold: problema «"XSlop Over," "YSlop Over," or "Frame slop" error displayed during TrackFrame.» (codice XSlop Over; YSlop Over; Frame slop). Contesto del ramo: if one of the listed errors is displayed, repeat Steps 1–6; based on current origin

**Il grafo afferma:** causa «Queued image outside the working envelope based on current origin» → passi:

- «Repeat TrackFrame steps 1–6» (riparazione); condizioni: [if] If an XSlop Over, YSlop Over, or Frame slop error is displayed

Problemi collegati a questa causa nel grafo: «X-axis travel exceeds working envelope»; «Y-axis travel exceeds working envelope»; «Frame slop»

- Giudizio: `U`
- Nota: 

### A013 · LG LMH2235ST over-the-range microwave oven, pagina 20, 27

**Il manuale dice:**

`p20.b10`

> 0.2 ~ 0.5 Ohm

`p27.b14`

> (2) Close the door tightly and check gaps A and B to [p27.b15] be sure they are no more than 1/64” (0.5 mm). See Figure 23-b for close-up view of gaps A and B (door latches). If all gaps are less than 1/64” (0.5 mm), adjustment of the latch board may not be necessary. Go to Steps 5 and 6 to check the sequence of the switches.

`p27.b15`

> be sure they are no more than 1/64” (0.5 mm). See Figure 23-b for close-up view of gaps A and B (door latches). If all gaps are less than 1/64” (0.5 mm), adjustment of the latch board may not be necessary. Go to Steps 5 and 6 to check the sequence of the switches.

`p27.b17`

> The correct sequence of the Primary Interlock Switch, Secondary Interlock Switch and the Interlock Monitor Switch is very important. If any gap is larger than 1/64” (0.5 mm), you will need to adjust the latch board. Go to step 3 and follow all steps in order.

`p27.b19`

> (3) Loosen the two screws holding the plastic latch [p27.b20] board as shown.

`p27.b21`

> (4) With the oven door closed tightly, move the latch [p27.b22] board upward toward the top of the oven and/or away from the door latch until the gaps are less than 1/64 ” (0.5 mm). Hold the latch board tightly in this position until you check the sequence of the switches in steps 5 and 6.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Close the door tightly and check gaps A and B.» (controllo)

Ramo del gold: problema «Door latch gaps exceed 1/64 in. (0.5 mm) or interlock switches do not operate in the required sequence.». Contesto del ramo: se ciascun gap A/B supera 1/64 in. (0,5 mm), regolare; se entrambi sono inferiori, la regolazione può non essere necessaria e si passa ai controlli di sequenza

**Il grafo afferma:** causa «Latch board out of adjustment» *(non scritta nel manuale)* → passi:

- «Adjust the latch board until gaps are less than 1/64 in. (0.5 mm)» (riparazione); condizioni: [if] If any gap is larger than 1/64 inch (0.5 mm).; [warning] Hold the latch board tightly in position until checking the switch sequence in steps 5 and 6.
- «Check door latch gaps A and B» (controllo); condizioni: [if] If the gaps are less than 1/64 inch (0.5 mm), latch-board adjustment may not be necessary; proceed to check the switch sequence.
- «Check the switch operating sequence while opening the door» (controllo); condizioni: [expected] On slowly opening the door, the switches operate in this order: Primary Interlock Switch, Secondary Interlock Switch, Interlock Monitor Switch.
- «Check the switch operating sequence while closing the door» (controllo); condizioni: [expected] On slowly closing the door, the switches operate in this order: Interlock Monitor Switch, Primary Interlock Switch, Secondary Interlock Switch.
- «Tighten the latch board screws after achieving the proper switch sequence» (riparazione); condizioni: [if] When the proper switch sequence has been achieved in steps 5 and 6.

Problemi collegati a questa causa nel grafo: «Keys do not operate»; «Product does not operate after power on»; «Door latch and switch closing does not meet specified gaps or sequence»

- Giudizio: `U`
- Nota: 

### A014 · LG LMH2235ST over-the-range microwave oven, pagina 31

**Il manuale dice:**

`p31.t1.r2`

> CAPACITOR | 1. Remove wire leads. 2. Measure resistance. (ohm meter scale: Rx1000) • Terminal to terminal • Terminal to case | Normal: Momentarily Infinite and then soon reach 10 mega. ohms Normal: Infinite.

**Riferimento (il tuo gold):** problema «Capacitor component test.» → causa non indicata nel manuale

Contesto del ramo: normale terminale-terminale: inizialmente infinito, poi raggiunge presto 10 MΩ; terminale-case: infinito

**Il grafo afferma:** problema «Suspected capacitor fault» → causa «Capacitor resistance outside normal range» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: La tabella dà i valori normali del test; non riporta una misura fuori intervallo né un guasto del condensatore.

### A015 · LG LMH2235ST over-the-range microwave oven, pagina 18, 19, 21

**Il manuale dice:**

`p18.b1`

> No Heat / No Cook

`p19.b1`

> After power on, does the product operate?

`p21.b11`

> 10 Is the connector connected to the high voltage diode assembly disconnected or disassembled?

`p21.b12`

> Reconnect or repair the connector.

`p21.b13`

> Yes

**Riferimento (il tuo gold):** problema «No heat / no cook; high-voltage diode connector disconnected or disassembled.» → «The connector to the high-voltage diode assembly is disconnected or disassembled.»

Contesto del ramo: se il connettore è scollegato o disassemblato

**Il grafo afferma:** problema «No heat / no cook» → causa «High voltage diode connector disconnected or disassembled» *(non scritta nel manuale)*

Condizioni: [if] The high voltage diode connector is disconnected or disassembled.

- Giudizio: `U`
- Nota: 

### A016 · Grizzly G0872 CNC laser cutter/engraver, pagina 27

**Il manuale dice:**

`p27.b5`

> (step 9) 9. With limit switch lever held in place, press arrow nav buttons on control panel to test movement of laser head assembly. The laser head assembly should not move.

`p27.b8`

> — If the laser head assembly does move, [p27.b9] disconnect machine from power. The limit switch safety feature is NOT working prop­ erly and must be replaced before operat­ ing the machine.

`p27.b9`

> disconnect machine from power. The limit switch safety feature is NOT working prop­ erly and must be replaced before operat­ ing the machine.

**Riferimento (il tuo gold):** problema «Laser head assembly moves while the limit switch lever is held in place.» (codice -) → «The limit switch safety feature is NOT working properly.»

Contesto del ramo: if the laser head assembly moves; before operating the machine

**Il grafo afferma:** problema «Laser head assembly moves while the X-axis limit switch lever is held» → causa «X-axis limit switch safety feature not working properly» *(non scritta nel manuale)*

Condizioni: [if] The laser head assembly moves while the limit switch lever is held.

- Giudizio: `U`
- Nota: 

### A017 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

`p232.t1.r4`

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Reset the fault.» (riparazione)

Ramo del gold: problema «There is an active fault in the drive.». Contesto del ramo: Red control panel LED lit and steady.

**Il grafo afferma:** causa «Active fault in another drive on the panel bus» → passi:

- «Switch to the drive with the active fault and check and reset it» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Control-panel LED lit steadily red»

- Giudizio: `S`
- Nota: Il riferimento riguarda un guasto nel drive corrente; il grafo usa il guasto di un altro drive sul bus.

### A018 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

`p232.t1.r4`

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Riferimento (il tuo gold):** problema «There is an active fault in another drive on the panel bus.» → causa non indicata nel manuale

Contesto del ramo: Red control panel LED lit and steady.

**Il grafo afferma:** problema «Control panel LED is steadily red» → causa «Active fault in another drive on the panel bus»

Condizioni: nessuna

- Giudizio: `G`
- Nota: La tabella collega LED rosso e assenza di alimentazione al guasto dell’altro drive; il gold trasforma quel guasto nel problema.

### A019 · LG LMH2235ST over-the-range microwave oven, pagina 18, 21

**Il manuale dice:**

`p18.b1`

> No Heat / No Cook

`p21.b20`

> 12 Is the connector connected to the magnetron assembly disconnected or disassembled?

`p21.b21`

> Yes

`p21.b22`

> Reconnect or repair the connector.

`p21.b5`

> 9 Is the resistance of the high voltage capacitor out of range? (refer to section 10)

**Riferimento (il tuo gold):** problema «No heat / no cook; high-voltage capacitor resistance is out of range.» → causa non indicata nel manuale

Contesto del ramo: sostituire se la resistenza è fuori intervallo; vedere section 10

**Il grafo afferma:** problema «No heat or no cook» → causa «Disconnected magnetron connector» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: Il gold riguarda la resistenza del condensatore HV; il grafo collega il connettore del magnetron.

### A020 · LG LMH2235ST over-the-range microwave oven, pagina 2

**Il manuale dice:**

`p2.b1`

> CAUTION WARNING TO SERVICE TECHNICIANS

`p2.b11`

> e. A microwave leakage check to verify compliance with the federal performance [p2.b12] standard should be performed on each oven prior to release to the owner.

`p2.b12`

> standard should be performed on each oven prior to release to the owner.

`p2.b2`

> PRECAUTIONS TO BE OBSERVED BEFORE AND DURING SERVICING TO AVOID POSSIBLE EXPOSURE

`p2.b3`

> TO EXCESSIVE MICROWAVE ENERGY

`p2.b5`

> b. Make the following safety checks on all ovens to be serviced before activating the [p2.b6] magnetron or other microwave source, and make repairs as necessary; (1) Interlock operation, (2) proper door closing, (3) seal and sealing surfaces (arcing, wear, and other damage), (4) damage to or loosening of hinges and latches, (5) evidence of dropping or abuse.

**Riferimento (il tuo gold):** problema «Safety checks before activating the magnetron or another microwave source.» → causa non indicata nel manuale

Contesto del ramo: prima di attivare il magnetron o altra sorgente a microonde; personale non addestrato non deve intervenire senza prima aver studiato procedure e informazioni di sicurezza

**Il grafo afferma:** problema «Potential exposure to excessive microwave energy» → causa «Unspecified cause of potential excessive microwave energy exposure» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `G`
- Nota: Il manuale indica l’esposizione come rischio da evitare con i controlli pre-attivazione; il gold tratta quei controlli come problema.

### A021 · Lincoln Electric POWER MIG 215 MP welder, pagina 27, 28

**Il manuale dice:**

`p27.b15`

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

`p27.b4`

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

`p27.b5`

> Capacitor Discharge Procedure:

`p27.b6`

> Do not operate with panels removed. Before servicing or installing kits, disconnect machine from power and wait a minimum of two minutes prior to removing sheet metal.

`p28.t1.r3`

> Major physical or electrical damage is evident. | “Do not Plug in machine or turn it on.” Contact your local Authorized Field Service Facility. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

`p28.t1.r9`

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed. | 1. Check gas supply, flow regulator and gas hoses. 2. Check gun connection to machine for obstruction or leaky machine. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «If all recommended possible areas of misadjustment have been checked and the problem persists, contact your local Lincoln Authorized Field Service Facility.» (assistenza)

Ramo del gold: problema «No wire feed, weld output or gas flow when gun trigger is pulled. Fan does NOT operate.». Contesto del ramo: Se tutti i controlli raccomandati per il sintomo sono stati eseguiti e il problema persiste.

**Il grafo afferma:** causa «Major physical or electrical damage» → passi:

- «Contact an authorized field service facility» (assistenza); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Major physical or electrical damage is evident»

- Giudizio: `S`
- Nota: L’assistenza è condizionata dal sintomo no wire feed/no output/no gas e ventola ferma; il grafo la lega a danni evidenti.

### A022 · Grizzly G0872 CNC laser cutter/engraver, pagina 51, 52

**Il manuale dice:**

`p51.t1.r2`

> Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | 1. Emergency stop button depressed/at fault. 2. Incorrect power supply voltage or circuit size. 3. Power supply circuit breaker tripped or fuse blown. 4. Air pump, water chiller, or exhaust fan have a short. 5. Wiring broken, disconnected, or corroded. 6. Machine chassis ground at fault. 7. Laser tube at fault. 8. Power supply or controller at fault. 9. Computer board at fault. | 1. Rotate emergency stop button head to reset. Replace if at fault. 2. Ensure correct power supply voltage and circuit size. 3. Ensure circuit is sized correctly and free of shorts. Reset circuit breaker or replace fuse. 4. Inspect/replace if at fault. 5. Fix broken wires or disconnected/corroded connections. 6. Machine must be connected to a dedicated ground rod at/or near machine (Page 15). 7. Inspect for evidence of arcing at laser tube connections. Verify wire insulation is preventing arcing and discharge to machine frame. 8. Inspect/replace if at fault (Page 63). 9. Inspect/replace if at fault (Page 63).

`p52.t1.r3`

> Machine laser has poor cutting or engraving results. | 1. Laser speed, path, or other CNC error exists. 2. Incorrect laser speed or laser power setting. 3. Focus is not set to correct height. 4. Laser is skewed or off-center. 5. Laser path is obstructed by smoke or material. 6. Laser unable to cut or scan workpiece. 7. Laser kerf too wide, and material is poorly cut. 8. Laser head has vibration or lash (workpiece path shows distortion/overlap). 9. Workpiece buckling or moving. 10. Laser output creating sawtooth pattern on cuts or engravings. 11. Laser tube at fault. 12. Transformer, power supply, or controller at fault. | 1. Review RDCam path settings and verify that software is free of errors. 2. Review RDCam power settings and verify that speed/power is set as desired (Page 28). Adjust laser speed/power at machine (Page 35). 3. Inspect/adjust focal length (Page 36). Inspect/adjust table parallelism (Page 52). 4. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Clean laser optics (Page 45). 5. Verify air supply hose is unobstructed and connected to air nozzle. Inspect/replace air pump (Page 22). Verify exhaust ducting is unobstructed and functional (Page 22). 6. Workpiece material beyond machine capability. 7. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Inspect/adjust focal length (Page 36). Inspect/ adjust table parallelism (Page 52). 8. Adjust/replace belts (Page 51). Inspect/adjust linkage, tracks, and guides for loose fasteners or binding. Reset origin (Page 34). 9. Use honeycomb table for thin workpiece support. Use clamps to secure large or irregular workpieces. 10. Increase laser power (Page 35). Workpiece may contain impurities that ignite, ejecting particles of molten material. 11. Replace laser tube (Page 52). Replace laser tube power supply. 12. Inspect/replace transformer, power supply, or controller, as required.

`p52.t1.r4`

> Laser tube inoperative or laser powers down while machine is operating. | 1. Water chiller system not cooling laser tube; thermal kill switch activates or alarm sounds. 2. Air pump, water pump, or exhaust fan have a short. 3. One or more laser tube power supply components have failed. 4. Laser tube electrical connections at fault. 5. Electrical system at fault. 6. Laser tube at fault. | 1. Inspect/replace water chiller system (Page 21). Reduce ambient temperature of machine operating environment. Add ice to reservoir, as required. Add additional water chilling equipment, as required. 2. Inspect/replace if at fault. 3. Replace laser tube power supply and machine electrical components, as required (Page 63). 4. Verify laser tube electrical connections are correct and secure. 5. Test/replace electrical system components, as required (Page 63). 6. Replace laser tube (Page 52).

**Riferimento (il tuo gold):** «Laser path is obstructed by smoke or material.» → azione «Replace the air pump.» (riparazione)

Ramo del gold: problema «Machine laser has poor cutting or engraving results.» (codice -). Contesto del ramo: see Page 22

**Il grafo afferma:** causa «Laser tube faulty» → passi:

- «Replace laser tube» (riparazione); condizioni: nessuna
- «Replace laser tube power supply» (riparazione); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Machine does not start, or breaker immediately trips after startup»; «Machine laser has poor cutting or engraving results»; «Laser tube inoperative or powers down during operation»

- Giudizio: `S`
- Nota: Il gold riguarda un percorso ostruito e il controllo della pompa aria; il grafo collega il guasto del tubo laser.

### A023 · Haas vertical mill (2023 operator's manual), pagina 141

**Il manuale dice:**

`p141.t1.r6`

> Light Curtain Breach | This icon appears when the machine is idle and the light curtain is triggered. It also appears when a program is running and the light curtain is running. This icon disappears when the obstacle is removed from the light curtain line of sight.

**Riferimento (il tuo gold):** problema «The light curtain is triggered.» → causa non indicata nel manuale

Contesto del ramo: The icon appears when the machine is idle or a program is running and the light curtain is triggered.

**Il grafo afferma:** problema «Light curtain is triggered while the machine is idle or a program is running» → causa «Obstacle in the light curtain line of sight»

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A024 · LG LMH2235ST over-the-range microwave oven, pagina 15, 17

**Il manuale dice:**

`p15.b1`

> Does the display operate?

`p15.b12`

> Yes Check PCB Go to No. 6 of this flow chart.

`p15.b25`

> Replace the PCB.

`p15.b3`

> 1 When you push any Key, is there any beeping sound?

`p17.b12`

> No Replace the PCB (EBR75341201)

`p17.b22`

> Replace the PCB.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Press any key and check whether there is a beep.» (controllo)

Ramo del gold: problema «No display or dead; display does not operate.». Contesto del ramo: display non funzionante; se il test di continuità emette un beep, andare al punto 6 del diagramma

**Il grafo afferma:** causa «PCB faulty» *(non scritta nel manuale)* → passi:

- «Replace the PCB (EBR75341201)» (riparazione); condizioni: [if] Voltage across both ends of D35 is not over 8 V during EZ-ON operation.

Problemi collegati a questa causa nel grafo: «No display or dead»; «Keypad failure»; «Turntable motor does not work»

- Giudizio: `S`
- Nota: La sostituzione PCB mostrata è condizionata al test D35 del ramo No Heat, non al test del beep del display.

### A025 · LG LMH2235ST over-the-range microwave oven, pagina 18, 20, 21

**Il manuale dice:**

`p18.b1`

> No Heat / No Cook

`p20.b2`

> 5 Is there any beeping sound in the continuity test between the ends of the latch board? (Door should be closed)

`p21.b20`

> 12 Is the connector connected to the magnetron assembly disconnected or disassembled?

**Riferimento (il tuo gold):** problema «No heat / no cook; latch-board continuity test fails.» → causa non indicata nel manuale

Contesto del ramo: porta chiusa; regolare se non c'è beep; vedere sections 9-1, 9-2

**Il grafo afferma:** problema «No heat / no cook» → causa «Magnetron connector disconnected or disassembled» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: Il gold riguarda il test di continuità della latch board; il grafo indica il connettore del magnetron.

### A026 · Lincoln Electric POWER MIG 215 MP welder, pagina 27, 28, 29

**Il manuale dice:**

`p27.b15`

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

`p27.b4`

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

`p27.b5`

> Capacitor Discharge Procedure:

`p27.b6`

> Do not operate with panels removed. Before servicing or installing kits, disconnect machine from power and wait a minimum of two minutes prior to removing sheet metal.

`p28.t1.r9`

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed. | 1. Check gas supply, flow regulator and gas hoses. 2. Check gun connection to machine for obstruction or leaky machine. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

`p29.t1.r3`

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Contact your local Lincoln Authorized Field Service Facility.» (assistenza)

Ramo del gold: problema «Arc is unstable - Poor starting.». Contesto del ramo: Se il gun tip è usurato, danneggiato o della misura non corretta; se il problema persiste dopo i controlli, contattare il servizio autorizzato.

**Il grafo afferma:** causa «Incorrect liner size» *(non scritta nel manuale)* → passi:

- «Check for the proper size liner» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Arc is unstable and starting is poor»

- Giudizio: `S`
- Nota: Il riferimento chiede assistenza se i controlli falliscono; il grafo offre il controllo del liner e perde la condizione.

### A027 · Grizzly G0872 CNC laser cutter/engraver, pagina 40

**Il manuale dice:**

`p40.b1`

> (step 3) 3. Review .RD file using RDCam, and position workpiece so queued image fits within work­ ing envelope.

`p40.b12`

> If "XSlop Over," "YSlop Over," or "Frame slop" errors are displayed on screen, the machine has determined that the currently queued image is outside the work­ ing envelope, based on current origin (see Figures 63–64).

`p40.b2`

> (step 4) 4. Move laser head assembly to location of ori­ gin defined in RDCam, in reference to work­ ing envelope.

`p40.b3`

> For example, if operator set origin to center of image in RDCam software, position laser head assembly over center of table.

`p40.b4`

> (step 5) 5. Press Origin button. Machine will beep to indicate origin has been set.

`p40.b5`

> (step 6) 6. Press Enter and observe perimeter of tool­ paths being traced by laser head movement. Verify display shows "Tracking Frame" during operation (see Figure 62).

**Riferimento (il tuo gold):** «the currently queued image is outside the working envelope, based on current origin» → azione «Verify the display shows "Tracking Frame" during operation.» (controllo)

Ramo del gold: problema «"XSlop Over," "YSlop Over," or "Frame slop" error displayed during TrackFrame.» (codice XSlop Over; YSlop Over; Frame slop). Contesto del ramo: if one of the listed errors is displayed, repeat Steps 1–6; based on current origin

**Il grafo afferma:** causa «Queued image outside the working envelope based on the current origin» → passi:

- «Review the RD file and position the workpiece so the queued image fits within the working envelope» (riparazione); condizioni: nessuna
- «Move the laser head assembly to the origin defined in RDCam» (riparazione); condizioni: nessuna
- «Press Origin to set the origin» (riparazione); condizioni: nessuna
- «Press Enter and observe the traced toolpath perimeter» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «TrackFrame slop error»; «X-axis travel exceeds working envelope»; «Y-axis travel exceeds working envelope»

- Giudizio: `S`
- Nota: Il grafo osserva il tracciato ma omette la verifica che il display mostri «Tracking Frame».

### A028 · Grizzly G0872 CNC laser cutter/engraver, pagina 51, 52

**Il manuale dice:**

`p51.t1.r2`

> Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | 1. Emergency stop button depressed/at fault. 2. Incorrect power supply voltage or circuit size. 3. Power supply circuit breaker tripped or fuse blown. 4. Air pump, water chiller, or exhaust fan have a short. 5. Wiring broken, disconnected, or corroded. 6. Machine chassis ground at fault. 7. Laser tube at fault. 8. Power supply or controller at fault. 9. Computer board at fault. | 1. Rotate emergency stop button head to reset. Replace if at fault. 2. Ensure correct power supply voltage and circuit size. 3. Ensure circuit is sized correctly and free of shorts. Reset circuit breaker or replace fuse. 4. Inspect/replace if at fault. 5. Fix broken wires or disconnected/corroded connections. 6. Machine must be connected to a dedicated ground rod at/or near machine (Page 15). 7. Inspect for evidence of arcing at laser tube connections. Verify wire insulation is preventing arcing and discharge to machine frame. 8. Inspect/replace if at fault (Page 63). 9. Inspect/replace if at fault (Page 63).

`p52.t1.r3`

> Machine laser has poor cutting or engraving results. | 1. Laser speed, path, or other CNC error exists. 2. Incorrect laser speed or laser power setting. 3. Focus is not set to correct height. 4. Laser is skewed or off-center. 5. Laser path is obstructed by smoke or material. 6. Laser unable to cut or scan workpiece. 7. Laser kerf too wide, and material is poorly cut. 8. Laser head has vibration or lash (workpiece path shows distortion/overlap). 9. Workpiece buckling or moving. 10. Laser output creating sawtooth pattern on cuts or engravings. 11. Laser tube at fault. 12. Transformer, power supply, or controller at fault. | 1. Review RDCam path settings and verify that software is free of errors. 2. Review RDCam power settings and verify that speed/power is set as desired (Page 28). Adjust laser speed/power at machine (Page 35). 3. Inspect/adjust focal length (Page 36). Inspect/adjust table parallelism (Page 52). 4. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Clean laser optics (Page 45). 5. Verify air supply hose is unobstructed and connected to air nozzle. Inspect/replace air pump (Page 22). Verify exhaust ducting is unobstructed and functional (Page 22). 6. Workpiece material beyond machine capability. 7. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Inspect/adjust focal length (Page 36). Inspect/ adjust table parallelism (Page 52). 8. Adjust/replace belts (Page 51). Inspect/adjust linkage, tracks, and guides for loose fasteners or binding. Reset origin (Page 34). 9. Use honeycomb table for thin workpiece support. Use clamps to secure large or irregular workpieces. 10. Increase laser power (Page 35). Workpiece may contain impurities that ignite, ejecting particles of molten material. 11. Replace laser tube (Page 52). Replace laser tube power supply. 12. Inspect/replace transformer, power supply, or controller, as required.

`p52.t1.r4`

> Laser tube inoperative or laser powers down while machine is operating. | 1. Water chiller system not cooling laser tube; thermal kill switch activates or alarm sounds. 2. Air pump, water pump, or exhaust fan have a short. 3. One or more laser tube power supply components have failed. 4. Laser tube electrical connections at fault. 5. Electrical system at fault. 6. Laser tube at fault. | 1. Inspect/replace water chiller system (Page 21). Reduce ambient temperature of machine operating environment. Add ice to reservoir, as required. Add additional water chilling equipment, as required. 2. Inspect/replace if at fault. 3. Replace laser tube power supply and machine electrical components, as required (Page 63). 4. Verify laser tube electrical connections are correct and secure. 5. Test/replace electrical system components, as required (Page 63). 6. Replace laser tube (Page 52).

**Riferimento (il tuo gold):** «Laser kerf too wide, and material is poorly cut.» → azione «Inspect the focal length.» (controllo)

Ramo del gold: problema «Machine laser has poor cutting or engraving results.» (codice -). Contesto del ramo: see Pages 61, 57, 36 and 52

**Il grafo afferma:** causa «Laser tube faulty» → passi:

- «Inspect laser tube connections for arcing and verify wire insulation prevents arcing to machine frame» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Machine does not start, or breaker immediately trips after startup»; «Machine laser has poor cutting or engraving results»; «Laser tube inoperative or powers down during operation»

- Giudizio: `S`
- Nota: Il riferimento chiede di ispezionare la focale per kerf troppo largo; il grafo dà rimedi per il guasto del tubo laser.

### A029 · ABB ACS580-01 variable speed drive, pagina 232

**Il manuale dice:**

`p232.t1.r4`

> Panel has no power | Red | Check the display to see where the fault is. • Active fault in the drive. Reset the fault. • Active fault in another drive in the panel bus. Switch to the drive in question and check and reset the fault. | Red | Active fault in the drive. To reset the fault, cycle the drive power.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Reset the fault.» (riparazione)

Ramo del gold: problema «There is an active fault in another drive on the panel bus.». Contesto del ramo: Red control panel LED lit and steady.

**Il grafo afferma:** causa «Active fault in another drive on the panel bus» → passi:

- «Switch to the drive with the active fault and check and reset it» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Control-panel LED lit steadily red»

- Giudizio: `U`
- Nota: 

### A030 · LG LMH2235ST over-the-range microwave oven, pagina 30

**Il manuale dice:**

`p30.t1.r1`

> COMPONENTS | TEST | RESULTS

`p30.t1.r3`

> MAGNETRON | Antenna Gasket Chassis Filament 1. Remove wire leads. Install the magnetron seal in the correct position. Check that the seal is in good condition. 2. Measure resistance. (ohm meter scale: Rx1) • Filament terminal 3. Measure resistance. (ohm meter scale: Rx1000) • Filament to chassis | Normal: Less than 1 ohm Normal: Infinite

**Riferimento (il tuo gold):** problema «Magnetron component test.» → causa non indicata nel manuale

Contesto del ramo: normale: filament terminal <1 Ω; filament-to-chassis resistance infinite

**Il grafo afferma:** problema «Suspected magnetron fault» → causa «Magnetron filament resistance outside normal range» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: La tabella specifica resistenze normali del magnetron; non attesta un valore anomalo.

### A031 · Grizzly G0872 CNC laser cutter/engraver, pagina 40

**Il manuale dice:**

`p40.b12`

> If "XSlop Over," "YSlop Over," or "Frame slop" errors are displayed on screen, the machine has determined that the currently queued image is outside the work­ ing envelope, based on current origin (see Figures 63–64).

`p40.b8`

> — If "XSlop Over," "YSlop Over," or "Frame [p40.b9] slop" errors are displayed on screen, repeat Steps 1–6.

`p40.b9`

> slop" errors are displayed on screen, repeat Steps 1–6.

**Riferimento (il tuo gold):** problema «"XSlop Over," "YSlop Over," or "Frame slop" error displayed during TrackFrame.» (codice XSlop Over; YSlop Over; Frame slop) → «the currently queued image is outside the working envelope, based on current origin»

Contesto del ramo: if one of the listed errors is displayed, repeat Steps 1–6; based on current origin

**Il grafo afferma:** problema «TrackFrame slop error» → causa «Queued image outside the working envelope based on the current origin»

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A032 · Haas vertical mill (2023 operator's manual), pagina 144

**Il manuale dice:**

`p144.t1.r6`

> Transformer Overheat (Warning) | This icon appears when the transformer is detected to be overheated for more than 1 second.

**Riferimento (il tuo gold):** problema «The transformer is overheated for more than one second (Transformer Overheat warning).» → «The transformer is detected to be overheated for more than 1 second.»

Contesto del ramo: nessuna

**Il grafo afferma:** problema «Transformer overheat warning icon» → causa «Transformer remains overheated for more than 1 second»

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A033 · LG LMH2235ST over-the-range microwave oven, pagina 30

**Il manuale dice:**

`p30.b1`

> (step 10) 10. COMPONENT TESTING INFORMATION

`p30.t1.r2`

> TRANSFORMER | FILAMENT SECONDARY WINDING WINDING PRIMARY WINDING 1. Remove wire leads. 2. Measure resistance. (ohm meter scale: Rx1) • Primary winding • Secondary winding • Filament winding 3. Measure resistance. (ohm meter scale: Rx1000) • Primary winding to ground • Filament winding to ground | Approx. 0.3 to 0.5 ohms Approx. 65 to 120 ohms 0 ohm Normal: Infinite Normal: Infinite

**Riferimento (il tuo gold):** problema «Transformer component test.» → causa non indicata nel manuale

Contesto del ramo: valori indicati: primario circa 0,3–0,5 Ω; secondario circa 65–120 Ω; filamento 0 Ω; primario e filamento verso terra: infinito

**Il grafo afferma:** problema «Suspected transformer fault» → causa «High-voltage transformer winding is grounded» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: La tabella riporta valori normali del trasformatore; non afferma che un avvolgimento sia a massa.

### A034 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

`p29.t1.r4`

> Error Code 003,010,013 Is displayed on screen | 1. Communication error between display P.C. board and power control board. | 1. Cycle power to machine 2. Contact your local Lincoln Authorized Field Service Facility.

**Riferimento (il tuo gold):** problema «Error code is displayed on screen.» (codice 003, 010, 013) → «Communication error between display P.C. board and power control board.»

Contesto del ramo: nessuna

**Il grafo afferma:** problema «Error code is displayed on screen» → causa «Unspecified cause of communication error between display and power control boards» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `U`
- Nota: 

### A035 · LG LMH2235ST over-the-range microwave oven, pagina 18, 19

**Il manuale dice:**

`p18.b1`

> No Heat / No Cook

`p19.b1`

> After power on, does the product operate?

`p19.b2`

> No

**Riferimento (il tuo gold):** problema «No heat / no cook; product does not operate after power on.» → causa non indicata nel manuale

Contesto del ramo: se dopo i tre cicli il prodotto opera, seguire l'alternate explanation indicata nel diagramma

**Il grafo afferma:** problema «Product does not operate after power on» → causa «D35 voltage below 8 V» *(non scritta nel manuale)*

Condizioni: [if] D35 voltage is not over 8 V during EZ-ON operation.

- Giudizio: `U`
- Nota: 

### A036 · LG LMH2235ST over-the-range microwave oven, pagina 12

**Il manuale dice:**

`p12.b10`

> (2) After power is applied:

`p12.b11`

> (a) Make sure the interlock switch mechanism [p12.b12] is operating properly by opening and closing the door.

`p12.b12`

> is operating properly by opening and closing the door.

`p12.b13`

> (b) Check microwave energy leakage must be [p12.b14] below the limit of 5 mW/cm2 . (All service adjustments should be made for minimum microwave energy leakage readings).

`p12.b14`

> below the limit of 5 mW/cm2 . (All service adjustments should be made for minimum microwave energy leakage readings).

`p12.b15`

> (3) Do not operate the unit until it is completely [p12.b16] repaired. If any of the following conditions exist, the unit must not be operated. (a) The door does not close firmly. (b) The hinge is broken. (c) The door seal is damaged. (d) The door is bent or warped, or there is any [p12.b17] other visible damage on the unit that may cause microwave energy leakage. NOTE: Always keep the seal clean. (e) Make sure that there are no defective parts [p12.b18] in the interlock mechanism. (f) Make sure that there are no detective parts [p12.b19] in the microwave generating and transmission assembly (especially waveguide).

**Riferimento (il tuo gold):** «Possible exposure to microwave energy leakage.» → azione «Check microwave energy leakage.» (controllo)

Ramo del gold: problema «Pre-service microwave-leakage precautions.». Contesto del ramo: before power is applied and after power is applied; leakage below 5 mW/cm²

**Il grafo afferma:** causa «Unit does not stop when the door is opened or time is up» *(non scritta nel manuale)* → passi:

- «Check that the unit stops when the door is opened or time is up» (controllo); condizioni: nessuna

Problemi collegati a questa causa nel grafo: nessuno

- Giudizio: `S`
- Nota: Il riferimento misura la perdita di microonde (<5 mW/cm²); il grafo verifica solo l’arresto dell’unità.

### A037 · LG LMH2235ST over-the-range microwave oven, pagina 18, 19, 21

**Il manuale dice:**

`p18.b1`

> No Heat / No Cook

`p19.b10`

> 3 While the product is operating under EZ-ON start, is the voltage of both ends of the D35 over 8 V?

`p21.b20`

> 12 Is the connector connected to the magnetron assembly disconnected or disassembled?

**Riferimento (il tuo gold):** problema «No heat / no cook; D35 voltage is over 8 V during EZ-ON operation.» → causa non indicata nel manuale

Contesto del ramo: sostituire se la tensione su entrambi i capi di D35 supera 8 V

**Il grafo afferma:** problema «No heat / no cook» → causa «Magnetron connector disconnected or disassembled» *(non scritta nel manuale)*

Condizioni: nessuna

- Giudizio: `S`
- Nota: Il gold è nel ramo D35 >8 V; il grafo collega un controllo successivo sul magnetron e non conserva la condizione D35.

### A038 · LG LMH2235ST over-the-range microwave oven, pagina 27, 28

**Il manuale dice:**

`p27.b11`

> The outer cover of the microwave oven is removed.

`p27.b6`

> The Interlock Monitor and Primary Interlock Switch act as the final safety switch protecting the user from microwave energy. The terminals between COM and NC of the Interlock Monitor must close when the door is opened. After adjusting the Interlock Monitor Switch, make sure that it is correctly connected. Mounting of the primary/monitor/secondary switches to the latch board.

`p28.b13`

> (7) When you achieve the proper sequence of [p28.b14] switches in Steps 5 and 6, tighten the latch board screws at that point.

`p28.b14`

> switches in Steps 5 and 6, tighten the latch board screws at that point.

`p28.b3`

> (5) Open the oven door slowly. Watch the door latch [p28.b4] and the Secondary Switch. Release the rod and lever on the switches to make sure they are zero to the body of the switches in the following sequence:

`p28.b4`

> and the Secondary Switch. Release the rod and lever on the switches to make sure they are zero to the body of the switches in the following sequence:

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Check that the monitor-switch COM and NC terminals close when the door is opened.» (controllo)

Ramo del gold: problema «Door latch gaps exceed 1/64 in. (0.5 mm) or interlock switches do not operate in the required sequence.». Contesto del ramo: se ciascun gap A/B supera 1/64 in. (0,5 mm), regolare; se entrambi sono inferiori, la regolazione può non essere necessaria e si passa ai controlli di sequenza

**Il grafo afferma:** causa «Interlock switches operate in the wrong sequence» *(non scritta nel manuale)* → passi:

- «Check the switch opening sequence» (controllo); condizioni: [expected] On opening: Primary, Secondary, then Interlock Monitor switch.
- «Check the switch closing sequence» (controllo); condizioni: [expected] On closing: Interlock Monitor, Primary, then Secondary switch.
- «Tighten the latch board screws after obtaining the proper switch sequence» (riparazione); condizioni: [if] The proper switch sequence is achieved.

Problemi collegati a questa causa nel grafo: «Door latch and interlock switch closing out of adjustment»

- Giudizio: `S`
- Nota: Il riferimento verifica COM-NC dell’interlock monitor; il grafo controlla la sequenza degli switch.

### A039 · Grizzly G0872 CNC laser cutter/engraver, pagina 51, 52

**Il manuale dice:**

`p51.t1.r2`

> Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | 1. Emergency stop button depressed/at fault. 2. Incorrect power supply voltage or circuit size. 3. Power supply circuit breaker tripped or fuse blown. 4. Air pump, water chiller, or exhaust fan have a short. 5. Wiring broken, disconnected, or corroded. 6. Machine chassis ground at fault. 7. Laser tube at fault. 8. Power supply or controller at fault. 9. Computer board at fault. | 1. Rotate emergency stop button head to reset. Replace if at fault. 2. Ensure correct power supply voltage and circuit size. 3. Ensure circuit is sized correctly and free of shorts. Reset circuit breaker or replace fuse. 4. Inspect/replace if at fault. 5. Fix broken wires or disconnected/corroded connections. 6. Machine must be connected to a dedicated ground rod at/or near machine (Page 15). 7. Inspect for evidence of arcing at laser tube connections. Verify wire insulation is preventing arcing and discharge to machine frame. 8. Inspect/replace if at fault (Page 63). 9. Inspect/replace if at fault (Page 63).

`p52.t1.r3`

> Machine laser has poor cutting or engraving results. | 1. Laser speed, path, or other CNC error exists. 2. Incorrect laser speed or laser power setting. 3. Focus is not set to correct height. 4. Laser is skewed or off-center. 5. Laser path is obstructed by smoke or material. 6. Laser unable to cut or scan workpiece. 7. Laser kerf too wide, and material is poorly cut. 8. Laser head has vibration or lash (workpiece path shows distortion/overlap). 9. Workpiece buckling or moving. 10. Laser output creating sawtooth pattern on cuts or engravings. 11. Laser tube at fault. 12. Transformer, power supply, or controller at fault. | 1. Review RDCam path settings and verify that software is free of errors. 2. Review RDCam power settings and verify that speed/power is set as desired (Page 28). Adjust laser speed/power at machine (Page 35). 3. Inspect/adjust focal length (Page 36). Inspect/adjust table parallelism (Page 52). 4. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Clean laser optics (Page 45). 5. Verify air supply hose is unobstructed and connected to air nozzle. Inspect/replace air pump (Page 22). Verify exhaust ducting is unobstructed and functional (Page 22). 6. Workpiece material beyond machine capability. 7. Verify mirrors are secure, and reflective side is facing outward (Page 61). Align laser beam (Page 57). Inspect/adjust focal length (Page 36). Inspect/ adjust table parallelism (Page 52). 8. Adjust/replace belts (Page 51). Inspect/adjust linkage, tracks, and guides for loose fasteners or binding. Reset origin (Page 34). 9. Use honeycomb table for thin workpiece support. Use clamps to secure large or irregular workpieces. 10. Increase laser power (Page 35). Workpiece may contain impurities that ignite, ejecting particles of molten material. 11. Replace laser tube (Page 52). Replace laser tube power supply. 12. Inspect/replace transformer, power supply, or controller, as required.

`p52.t1.r4`

> Laser tube inoperative or laser powers down while machine is operating. | 1. Water chiller system not cooling laser tube; thermal kill switch activates or alarm sounds. 2. Air pump, water pump, or exhaust fan have a short. 3. One or more laser tube power supply components have failed. 4. Laser tube electrical connections at fault. 5. Electrical system at fault. 6. Laser tube at fault. | 1. Inspect/replace water chiller system (Page 21). Reduce ambient temperature of machine operating environment. Add ice to reservoir, as required. Add additional water chilling equipment, as required. 2. Inspect/replace if at fault. 3. Replace laser tube power supply and machine electrical components, as required (Page 63). 4. Verify laser tube electrical connections are correct and secure. 5. Test/replace electrical system components, as required (Page 63). 6. Replace laser tube (Page 52).

**Riferimento (il tuo gold):** «Laser head has vibration or lash (workpiece path shows distortion/overlap).» → azione «Replace the belts.» (riparazione)

Ramo del gold: problema «Machine laser has poor cutting or engraving results.» (codice -). Contesto del ramo: see Pages 51 and 34; inspect/adjust linkage, tracks and guides for loose fasteners or binding

**Il grafo afferma:** causa «Laser tube fault» → passi:

- «Replace laser tube» (riparazione); condizioni: nessuna

Problemi collegati a questa causa nel grafo: «Machine does not start or breaker trips immediately»; «Machine has poor cutting or engraving results»; «Laser tube is inoperative or powers down during operation»

- Giudizio: `S`
- Nota: Il riferimento riguarda le cinghie per vibrazione/slop; il grafo collega la sostituzione del tubo laser.

### A040 · Lincoln Electric POWER MIG 215 MP welder, pagina 27, 28

**Il manuale dice:**

`p27.b15`

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

`p27.b4`

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

`p27.b5`

> Capacitor Discharge Procedure:

`p27.b6`

> Do not operate with panels removed. Before servicing or installing kits, disconnect machine from power and wait a minimum of two minutes prior to removing sheet metal.

`p28.t1.r3`

> Major physical or electrical damage is evident. | “Do not Plug in machine or turn it on.” Contact your local Authorized Field Service Facility. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

`p28.t1.r7`

> Low or no gas flow when gun trigger is pulled. Wire feed, weld output and fan operate normally. | 1. Check gas supply, flow regulator and gas hoses. 2. Check gun connection to machine for obstruction or leaky machine. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Riferimento (il tuo gold):** causa non indicata nel manuale → azione «Do not plug in machine or turn it on.» (controllo)

Ramo del gold: problema «Major physical or electrical damage is evident.». Contesto del ramo: Se tutti i controlli raccomandati per il sintomo sono stati eseguiti e il problema persiste.

**Il grafo afferma:** causa «Obstruction or leak at the gun-to-machine connection» *(non scritta nel manuale)* → passi:

- «Check the gun connection to the machine for obstruction or leakage» (controllo); condizioni: nessuna
- «Contact an authorized field service facility» (assistenza); condizioni: [if] If all recommended possible areas of misadjustment have been checked and the problem persists.

Problemi collegati a questa causa nel grafo: «Low or no gas flow when the gun trigger is pulled; wire feed, weld output, and fan operate normally»

- Giudizio: `S`
- Nota: Il problema gold è un danno fisico/elettrico con divieto di accensione; il grafo usa la riga sul flusso del gas.

