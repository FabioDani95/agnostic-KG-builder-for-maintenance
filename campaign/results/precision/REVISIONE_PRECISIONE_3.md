# Revisione della precisione del grafo

72 affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi
cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi
al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `chiave_non_aprire_3.json`:
contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.

Revisore: 
Data: 
Tempo totale impiegato (minuti): 

### R001 · Lincoln Electric POWER MIG 215 MP welder, pagina 21

**Il manuale dice:**

> The duty cycle is the “on” time (based on a 10 minute interval) the user can weld with the machine at a specific output without causing a thermal trip.

> If the duty cycle of the machine is exceeded, then the machine will thermally trip and the image shown will be displayed on the user interface. The machine must cool down before welding can be performed.

> 3 constant minutes and needing 7 minutes of “off” time before welding again.

**Il grafo afferma:** «Thermal trip after exceeding the duty cycle» **può indicare la causa** «Duty cycle exceeded»

- Giudizio: `?`
- Nota: 

### R002 · Grizzly G0872 CNC laser cutter/engraver, pagina 15

**Il manuale dice:**

> TOXIC FUMES. Cutting or engraving metals and plastics give off highly toxic fumes, vapors, and air particulates containing zinc, lead, beryllium, cadmium, mercury, fluorine, hexavalent chromi- um, chlorine gas, and many others. These fumes and air contaminants can damage the machine and harm your health. If the air filtration system or exhaust system is malfunctioning, immediately stop operations and correct the issue.

> ADEQUATE VENTILATION. Only use CNC lasers in spaces with adequate ventilation. Some materials can produce vapors and fumes that may irritate the nose, throat, and respiratory tract, or cause suffocation. Only operate CNC lasers with a fully-functioning exhaust and air filtration system. Utilize additional personnel to monitor operator from outside the operating area in the event of equipment failure.

**Il grafo afferma:** «Air filtration system malfunction» **si affronta con** «Correct the air filtration system malfunction» (riparazione)

Contesto: [warning] If the air filtration system or exhaust system is malfunctioning, immediately stop operations and correct the issue.; [warning] Only operate CNC lasers with a fully functioning exhaust and air filtration system.

- Giudizio: `?`
- Nota: 

### R003 · ABB ACS580-01 variable speed drive, pagina 345

**Il manuale dice:**

> Protecting the system in brake circuit fault situations

> Protecting the system in cable and brake resistor short-circuit situations

> The drive input fuses will also protect the resistor cable when it is identical with the input power cable.

**Il grafo afferma:** «Brake circuit short-circuit situation» **può indicare la causa** «Brake resistor cable short circuit»

- Giudizio: `?`
- Nota: 

### R004 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 28

**Il manuale dice:**

> WARNING Do not operate the pump without having connected the flanges to a vacuum system The screws of the flanges on the suction and the pressure side must not be loosened in the presence of a vacuum even if the pump is not running.

> WARNING

> Hot surfaces, risk of suffering burns. Notice safety information 0.3.

**Il grafo afferma:** «Oil level requires correction» **si affronta con** «Correct the oil level as required» (riparazione)

Contesto: [warning] Do not operate the pump without connecting the flanges to a vacuum system. Do not loosen suction- or pressure-side flange screws in the presence of a vacuum, even when the pump is stopped.; [warning] Hot surfaces present a burn risk; observe safety information 0.3.; [warning] Never open the oil-fill or oil-drain screw under vacuum or while the pump is running because oil may squirt out.

- Giudizio: `?`
- Nota: 

### R005 · LG LMH2235ST over-the-range microwave oven, pagina 20

**Il manuale dice:**

> 0.2 ~ 0.5 Ohm

**Il grafo afferma:** «High-voltage transformer faulty» **si affronta con** «Measure the high-voltage transformer primary winding resistance» (controllo o test)

Contesto: [expected] Primary winding resistance: 0.2–0.5 ohm

- Giudizio: `?`
- Nota: 

### R006 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 9

**Il manuale dice:**

> 7.1 Priming

> The PACO in-line centrifugal pumps are not self priming, and must be completely primed (filled with liquid) before starting. If the pump will operate with a positive suction head, prime by opening the suction valve and allowing liquid to enter pump casing. Open all air vents a the high points of pump and piping to ensure air is forced from pump by liquid. Disconnect the recirculation line at the seal housing and bleed completely of all air. Re-connect the line prior to start-up. Rotate the shaft by hand to free entrapped air from impeller passageways. If pump has a suction lift, priming must be accomplished by other methods.

**Il grafo afferma:** «Pump does not prime before startup» **può indicare la causa** «Air trapped in pump or piping»

- Giudizio: `?`
- Nota: 

### R007 · ABB ACS580-01 variable speed drive, pagina 233

**Il manuale dice:**

> The mission time of functional safety components is 20 years which equals the time during which failure rates of electronic components remain constant. This applies to the components of the standard Safe torque off circuit as well as any modules, relays and, typically, any other components that are part of functional safety circuits.

> The expiry of mission time terminates the certification and SIL/PL classification of the safety function. The following options exist:

**Il grafo afferma:** «Safety function certification and SIL/PL classification terminated» **può indicare la causa** «Functional safety certification and SIL/PL classification expire»

- Giudizio: `?`
- Nota: 

### R008 · Grizzly G0872 CNC laser cutter/engraver, pagina 51, 52

**Il manuale dice:**

> Laser tube inoperative or laser powers down while machine is operating. | 1. Water chiller system not cooling laser tube; thermal kill switch activates or alarm sounds. 2. Air pump, water pump, or exhaust fan have a short. 3. One or more laser tube power supply components have failed. 4. Laser tube electrical connections at fault. 5. Electrical system at fault. 6. Laser tube at fault. | 1. Inspect/replace water chiller system (Page 21). Reduce ambient temperature of machine operating environment. Add ice to reservoir, as required. Add additional water chilling equipment, as required. 2. Inspect/replace if at fault. 3. Replace laser tube power supply and machine electrical components, as required (Page 63). 4. Verify laser tube electrical connections are correct and secure. 5. Test/replace electrical system components, as required (Page 63). 6. Replace laser tube (Page 52).

> Review the troubleshooting procedures in this section if a problem develops with your machine. If you need replacement parts or additional help with a procedure, call our Technical Support. Note: Please gather the serial number and manufacture date of your machine before calling.

**Il grafo afferma:** «Water chiller not cooling laser tube» **si affronta con** «Add additional water chilling equipment as required» (riparazione)

Contesto: [if] As required

- Giudizio: `?`
- Nota: 

### R009 · LG LMH2235ST over-the-range microwave oven, pagina 30

**Il manuale dice:**

> MAGNETRON | Antenna Gasket Chassis Filament 1. Remove wire leads. Install the magnetron seal in the correct position. Check that the seal is in good condition. 2. Measure resistance. (ohm meter scale: Rx1) • Filament terminal 3. Measure resistance. (ohm meter scale: Rx1000) • Filament to chassis | Normal: Less than 1 ohm Normal: Infinite

**Il grafo afferma:** «Magnetron seal damaged or incorrectly positioned» **riguarda il componente** «Magnetron»

- Giudizio: `?`
- Nota: 

### R010 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

> To insure water and material are completely drained out of unit:

> 1. Remove material line from sprayer.

**Il grafo afferma:** «Water or material remaining in the unit can damage the pump or delay startup» **si affronta con** «Remove the material line from the sprayer» (riparazione)

Contesto: [warning] Water or material remaining in the unit below freezing can damage the pump and/or delay startup.; [warning] Wear appropriate protective equipment when operating, servicing, or in the operating area, including protective eyewear, clothing and respirator as recommended by the fluid and solvent manufacturer, gloves, and hearing protection.

- Giudizio: `?`
- Nota: 

### R011 · Lincoln Electric POWER MIG 215 MP welder, pagina 12

**Il manuale dice:**

> 12 DESIGN CASE BACK CASE REAR COMPONENTS DESCRIPTION INTERNAL CONTROLS INTERNAL CONTROLS DESCRIPTION 1. Spool Gun Switch – Permits toggling between standard push gun welding with the Magnum® Pro 175L or aluminum welding with the Magnum® Pro 100SG Spool Gun. 2. Wire Drive Tension Pressure Adjustment – Permits increasing or decreasing the pressure applied to the top drive roll. 3. Wire Drive Spindle – Supports a 4-inch or 8-inch spool of wire. The center wing-nut can be adjusted to increase tension on the wire. 4. Replaceable Wire Guide – Select the correct inner wire guide for the desired wire diameter. The outer wire guide provided can be used for any wire diameter. 5. Replaceable drive roll – Select the correct drive roll for the wire diameter and composition being fed. 6. Gun Connector Block – Permits securing a welding gun to the wire drive by ensuring the gun connector is fully seated, then tightening the large knob FIGURE A.2 FIGURE A.3 1 2 6 4 5 3  MIG Gas Solenoid Connector - Connection for the gas hose of the MIG shielding gas.  TIG Gas Solenoid Connector - Connection for the gas hose of the TIG shielding gas.  Thermal Breaker - The Power MIG® 215 MPJ5. features a resettable 25 amp thermal breaker. If the current conducted through the breaker exceeds 25 amps for an extended period of time, the breaker will open and require manual reset.  7*OQVU$PSE – )BSEXJSFE7JOQVUDPSE7UP7 JOQVUBEBQUFSJODMVEFEGPSFBTZ7DPNQBUJCJMJUZ POWER MIG 215 MP ® J5. 1 2 3 4 [STRUCTURED TABLES DETECTED ON THIS PAGE] | 6 1 2 3 INTER 1. Sp wel Ma 2. Wir 4 decr | --- | --- | --- | 4

**Il grafo afferma:** «Current through the breaker exceeds 25 amps for an extended period» **si affronta con** «Manually reset the thermal breaker» (riparazione)

- Giudizio: `?`
- Nota: 

### R012 · Haas vertical mill (2023 operator's manual), pagina 142

**Il manuale dice:**

> Low Lube | The spindle lubrication oil system detected a low oil condition, or the axis ball screw lubrication system detected a low grease or low pressure condition.

**Il grafo afferma:** «Low grease or low pressure condition in the axis ball screw lubrication system» **riguarda il componente** «Axis ball screw lubrication system»

- Giudizio: `?`
- Nota: 

### R013 · ABB ACS580-01 variable speed drive, pagina 121

**Il manuale dice:**

> 2. These screws have been disconnected. Otherwise EMC filter and ground-to-phase varistor capacitor leakage current will cause the residual current device to trip.

**Il grafo afferma:** «Residual current device trips» **può indicare la causa** «EMC filter and ground-to-phase varistor capacitor leakage current»

- Giudizio: `?`
- Nota: 

### R014 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 35

**Il manuale dice:**

> A intake screen is located in the intake port to collect foreign objects. It should be kept clean in order to avoid a reduction of the pumping speed. To do so, take off the intake line. Remove the dirt trap from the intake flange and rinse it using a suitable solvent. Then thoroughly dry it with compressed air. If the dirt trap is damaged, replace it.

> 6.5 Cleaning the Fan Cowl and the Cooling Fins

**Il grafo afferma:** «Intake dirt trap is damaged» **riguarda il componente** «Intake dirt trap»

- Giudizio: `?`
- Nota: 

### R015 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 8

**Il manuale dice:**

> PACO Type VL and VLS pumps are equipped with mechanical shaft seals.

> PACO mechanical seals are matched to conditions for which the pump was sold. Unlike Packing, mechanical seals require no field adjustments. Observe the following precautions to avoid seal damage and obtain maximum seal life: Do not exceed temperature or pressure limitations for the mechanical seal used.

> Do not run the pump dry or against a closed valve. Dry operation will cause seal failure within minutes.

**Il grafo afferma:** «Mechanical seal operated beyond its temperature or pressure limitations» **riguarda il componente** «Mechanical shaft seal»

- Giudizio: `?`
- Nota: 

### R016 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> Speed of application too slow | Pump in need of repair | See texture pump instruction manual 308479.

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

**Il grafo afferma:** «Stalled pump» **riguarda il componente** «Pump»

- Giudizio: `?`
- Nota: 

### R017 · Grizzly G0872 CNC laser cutter/engraver, pagina 26

**Il manuale dice:**

> information (see Figure 27), and after one audible beep, laser head assembly will home to upper right corner of table before moving to origin (or position of last cut).

> The Test Run consists of verifying the following: 1) Auxiliary systems power up and run properly, 2) stepper motors run correctly and machine prop­ erly homes, 3) limit switches function correctly, 4) top loading door interlock switch operates properly, and 5) Emergency Stop button functions properly.

**Il grafo afferma:** «Laser head assembly does not home correctly» **riguarda il componente** «Laser head assembly»

- Giudizio: `?`
- Nota: 

### R018 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • Of the Automatic Tool Changer/tool and spindle - Press [RECOVER] and follow the on-screen instructions.

**Il grafo afferma:** «Automatic Tool Changer, tool, or spindle jam» **può indicare la causa** «Automatic Tool Changer, tool, or spindle blockage»

- Giudizio: `?`
- Nota: 

### R019 · LG LMH2235ST over-the-range microwave oven, pagina 30

**Il manuale dice:**

> COMPONENTS | TEST | RESULTS

> MAGNETRON | Antenna Gasket Chassis Filament 1. Remove wire leads. Install the magnetron seal in the correct position. Check that the seal is in good condition. 2. Measure resistance. (ohm meter scale: Rx1) • Filament terminal 3. Measure resistance. (ohm meter scale: Rx1000) • Filament to chassis | Normal: Less than 1 ohm Normal: Infinite

**Il grafo afferma:** «Suspected magnetron fault» **può indicare la causa** «Magnetron filament resistance outside normal range»

- Giudizio: `?`
- Nota: 

### R020 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

> To insure water and material are completely drained out of unit:

> 1. Remove material line from sprayer.

**Il grafo afferma:** «Water or material remaining in the unit below freezing» **si affronta con** «Remove the material line from the sprayer» (riparazione)

Contesto: [order] Step 1; [warning] Water or material remaining in the unit when temperatures are below freezing can damage the pump or delay startup.

- Giudizio: `?`
- Nota: 

### R021 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 44

**Il manuale dice:**

> he oil level in the ler drops. | Visible oil leak: Outer shaft sealing ring is defective. No visible oil leak: Inner shaft sealing ring is defective. | Replace the shaft sealing rings. In case the oil loss is only slight, the pump may continue to operate providing it is ensured that a sufficient quantity of oil is topped up at the oiler. Replace the shaft sealing rings. Switch the pump off; the draining out oil enters into the bearing chambers, causing there an unacceptably high oil a level. | 6.9

**Il grafo afferma:** «Outer shaft sealing ring is defective» **si affronta con** «Replace the shaft sealing rings» (riparazione)

- Giudizio: `?`
- Nota: 

### R022 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 43

**Il manuale dice:**

> Pump gets too hot. | Ambient temperature is too high or cooling air flow is obstructed. Pump is operating in the wrong pressure range. Pressure differences too high. Gas temperature is too high. Clearance between housing and rotors are too small due to - contamination - distortion of the pump Friction resistance is too high due to contaminated bearings and/or contaminated oil. Oil level is too high. Oil level is too low. Wrong oil filled in. Bearing is defective. Valve of the pressure balance line does not open. | Install the pump at a suitable place or ensure a 4 sufficient flow of cooling air. Check the pressure levels within the system. - Check the pressure levels within the system. - Check system. - Clean pumping chamber. 6 Affix and connect the pump free of tension. 4 Change oil. 6 Drain oil down to the correct level. 6 Top up oil to the correct level. 6 Drain oil, fill in correct oil. 6 Atlas Copco Service. - Clean the valve or have it repaired. 6 | .1 .5 .1/4.5 .3 .3 .3 .3 .7

**Il grafo afferma:** «Pump gets too hot» **può indicare la causa** «Pump operates in the wrong pressure range»

- Giudizio: `?`
- Nota: 

### R023 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> Pump stops delivering liquid after start-up 2*3*4*5*6*7*8*9*10*11*12*13*22*23*24*34

> 23. The impeller may be clogged with debris.

**Il grafo afferma:** «Pump stops delivering liquid after start-up» **può indicare la causa** «Impeller clogged with debris»

- Giudizio: `?`
- Nota: 

### R024 · LG LMH2235ST over-the-range microwave oven, pagina 21

**Il manuale dice:**

> 9 Is the resistance of the high voltage capacitor out of range? (refer to section 10)

> Replace the high voltage capacitor.

> Yes

**Il grafo afferma:** «High-voltage capacitor resistance out of range» **si affronta con** «Replace the high-voltage capacitor» (riparazione)

- Giudizio: `?`
- Nota: 

### R025 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 35, 36

**Il manuale dice:**

> 6.5 Cleaning the Fan Cowl and the Cooling Fins

> Under dirty operating conditions, contaminants may be deposited in the pumping chamber or on the rotors. After removing the two connecting lines, the contaminants can be blown out with dry compressed air or flushed out with a suitable solvent. Contaminants that cannot be blown or flushed out, can be removed completely from the pumping chamber with a wire brush, metallic sponge or scraper. Then change the oil.

> WARNING During cleaning, the rotors must be turned only by hand. Please make sure that the rotors are turned in a way that fingers or hands can not be trapped between the rotors or between rotors and housing. Due to the high mass and inertia of the rotors serious injuries can occur even if the rotors are turned by hand only. The loosened deposits must not remain in the pump. After cleaning, check the pump by slowly turning the rotors by hand. They should move freely and without any resistance. Generally, the DRB pump does not need to be disassembled. If necessary, this should only be done by our after-sales service.

**Il grafo afferma:** «Unspecified cause of contaminants deposited in the pumping chamber or on the rotors» **si affronta con** «Check that the rotors turn slowly by hand and move freely without resistance» (controllo o test)

Contesto: [order] After cleaning the pump; [warning] During pumping-chamber cleaning, turn the rotors only by hand; keep fingers and hands clear of the rotors and housing because serious injury can occur. Do not leave loosened deposits in the pump.; [warning] Observe all safety information provided in Sections 0.1 to 0.3 and 6.1.

- Giudizio: `?`
- Nota: 

### R026 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 35

**Il manuale dice:**

> The slits in the fan cowl as well as the fins on the motor and on the pump may be contaminated depending on humidity conditions and the degree of contamination in the ambient air. In order to ensure a sufficient air flow for the motor and the pump’s casing, the grid of the fan cowl must be cleaned with a clean brush when contaminated. Any coarse dirt must be removed from the fins on the motor and the pump.

> column 1: | WARNING Observe all safety information provided in Sections 0.3 to 0.5 and 6.1.

> 6.5 Cleaning the Fan Cowl and the Cooling Fins

**Il grafo afferma:** «Contaminated fan cowl grille and cooling fins» **si affronta con** «Clean the contaminated fan cowl grid with a clean brush» (riparazione)

- Giudizio: `?`
- Nota: 

### R027 · ABB ACS580-01 variable speed drive, pagina 312

**Il manuale dice:**

> WARNING! The opening of the branch-circuit protective device may be an indication that a fault current has been interrupted. To reduce the risk of fire or electric shock, current-carrying parts and other components of the device should be examined and replaced if damaged.

**Il grafo afferma:** «Damaged current-carrying parts or other device components» **si affronta con** «Replace damaged current-carrying parts and other device components» (riparazione)

- Giudizio: `?`
- Nota: 

### R028 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

**Il grafo afferma:** «Water or material remaining in the unit can damage the pump or delay startup» **riguarda il componente** «Pump»

- Giudizio: `?`
- Nota: 

### R029 · Haas vertical mill (2023 operator's manual), pagina 96

**Il manuale dice:**

> The control can generate an error report that saves the state of the machine that is used for analysis. This is useful when helping the HFO troubleshoot an intermittent problem.

> The control saves the error report to your USB device or control memory. The error report is a zip file that includes a screen capture, the active program, and other information used for diagnostics. Generate this error report when an error or an alarm occurs. E-mail the error report to your local Haas Factory Outlet.

**Il grafo afferma:** «Intermittent machine problem» **può indicare la causa** «Unspecified cause of intermittent machine problem»

- Giudizio: `?`
- Nota: 

### R030 · Lincoln Electric POWER MIG 215 MP welder, pagina 21

**Il manuale dice:**

> The Power MIG® 215 MPJ5. features overload protection of the wire drive motor. If the motor becomes overloaded, the protection circuitry turns off the wire feed unit. Check for the proper size tip, liner, and drive rolls, for any obstructions or bends in the gun cable, and any other factors that would impede the wire feeding. To resume welding, simply pull the trigger. There is no circuit breaker to reset.

**Il grafo afferma:** «Wire drive motor overloaded» **si affronta con** «Check for the proper size tip» (controllo o test)

- Giudizio: `?`
- Nota: 

### R031 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 9

**Il manuale dice:**

> Make the following inspections before starting your PACO in-line centrifugal pump: Make sure all wiring connections to the motor (and starting device) match the wiring diagram and produce clockwise rotation as viewed from the end of the motor. If the motor has been in storage for an extended length of time, either before or after installation, refer to motor instructions before starting. Check voltage, phase, and line circuit frequency with the motor data plate. Turn rotating element by hand to make sure it rotates freely. Tighten plugs in gauge and drain taps. If pump is fitted with pressure gauges, keep gauge cocks closed when not in use.

**Il grafo afferma:** «Gauge or drain tap plugs are loose» **si affronta con** «Tighten plugs in gauge and drain taps» (riparazione)

- Giudizio: `?`
- Nota: 

### R032 · LG LMH2235ST over-the-range microwave oven, pagina 18, 19

**Il manuale dice:**

> No Heat / No Cook

> After power on, does the product operate?

> 3 While the product is operating under EZ-ON start, is the voltage of both ends of the D35 over 8 V?

**Il grafo afferma:** «No heat / no cook» **può indicare la causa** «Relay 2 fault»

Contesto: [if] During EZ-ON operation, voltage across D35 is over 8 V.

- Giudizio: `?`
- Nota: 

### R033 · ABB ACS580-01 variable speed drive, pagina 231

**Il manuale dice:**

> The DC link of the drive contains several electrolytic capacitors. Operating time, load, and surrounding air temperature have an effect on the life of the capacitors. Capacitor life can be extended by decreasing the surrounding air temperature.

> Capacitor failure is usually followed by damage to the unit and an input cable fuse failure, or a fault trip. If you think that any capacitors in the drive have failed, contact ABB.

**Il grafo afferma:** «Failed DC-link capacitors» **si affronta con** «Contact ABB about suspected failed capacitors» (contattare l'assistenza)

Contesto: [if] If you think that any capacitors in the drive have failed; [if] If you think that any capacitors in the drive have failed.

- Giudizio: `?`
- Nota: 

### R034 · Grizzly G0872 CNC laser cutter/engraver, pagina 26

**Il manuale dice:**

> Once assembly is complete, test run the machine to ensure it is properly connected to power and safety components are functioning correctly.

> If you find an unusual problem during the test run, immediately stop the machine, disconnect it from power, and fix the problem BEFORE operating the machine again. The Troubleshooting table in the SERVICE section of this manual can help.

> The Test Run consists of verifying the following: 1) Auxiliary systems power up and run properly, 2) stepper motors run correctly and machine prop­ erly homes, 3) limit switches function correctly, 4) top loading door interlock switch operates properly, and 5) Emergency Stop button functions properly.

**Il grafo afferma:** «Unusual problem during test run» **può indicare la causa** «Auxiliary systems not operating correctly»

- Giudizio: `?`
- Nota: 

### R035 · Lincoln Electric POWER MIG 215 MP welder, pagina 29

**Il manuale dice:**

> Arc is unstable - Poor starting. | 1. Check for correct input voltage to machine. 2. Check for proper electrode polarity for process. 3. Check gun tip for wear or damage and proper size - Replace. 4. Check for proper gas and flow rate for process. (For MIG only.) 5. Check work cable for loose or faulty connections. 6. Check gun for damage or breaks. 7. Check for proper drive roll ori- entation and alignment. 8. Check liner for proper size. | If all recommended possible areas of misadjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «Arc is unstable and starting is poor» **può indicare la causa** «Incorrect liner size»

- Giudizio: `?`
- Nota: 

### R036 · LG LMH2235ST over-the-range microwave oven, pagina 2

**Il manuale dice:**

> • Proper operation of the microwave oven requires that the magnetron be assembled to the wave guide and cavity. Never operate the magnetron unless it is properly installed.

> c. Before turning on microwave power for any service test or inspection within the

> microwave generating compartments, check the magnetron, wave guide or transmission line, and cavity for proper alignment, integrity, and connections.

**Il grafo afferma:** «Unspecified cause of potential excessive microwave energy exposure» **riguarda il componente** «Wave guide or transmission line»

- Giudizio: `?`
- Nota: 

### R037 · ABB ACS580-01 variable speed drive, pagina 385

**Il manuale dice:**

> 2. If no warning is shown,

> • make sure that the value of both parameters 15.01 Extension module type and 15.02 Detected extension module is CHDI-01.

> If warning the A7AB Extension I/O configuration failure is shown,

**Il grafo afferma:** «Incorrect extension module configuration» **si affronta con** «Check parameters 15.01 and 15.02 are set to CHDI-01» (controllo o test)

Contesto: [if] No warning is shown; [if] No warning is shown.

- Giudizio: `?`
- Nota: 

### R038 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 28

**Il manuale dice:**

> 5.1 Start-up

> Check the pump motor’s direction of rotation and the oil level in the oiler and the bearing chambers (see Section 4.2). The DRB can be started together with the backing pump at atmospheric pressure. It is protected against excessively high pressure differentials by a bypass line.

**Il grafo afferma:** «Unspecified cause of suspected pump motor fault» **si affronta con** «Check the pump motor direction of rotation» (controllo o test)

- Giudizio: `?`
- Nota: 

### R039 · Grizzly G0872 CNC laser cutter/engraver, pagina 26

**Il manuale dice:**

> 7. Open top loading door and locate x- and y-axis limit switches, and top loading door interlock switch (see Figure 28).

> If you find an unusual problem during the test run, immediately stop the machine, disconnect it from power, and fix the problem BEFORE operating the machine again. The Troubleshooting table in the SERVICE section of this manual can help.

> Serious injury or death can result from using this machine BEFORE understanding its controls and related safety information. DO NOT operate, or allow others to operate, machine until the information is understood.

**Il grafo afferma:** «Top loading door interlock switch safety feature not working properly» **si affronta con** «With the top loading door open, press the Pulse button to attempt a laser test fire» (controllo o test)

- Giudizio: `?`
- Nota: 

### R040 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Speed of application too slow | Hose plugged or too small. | Relieve Pressure, page 6. Clean hose, or try a 1-1/4 in. hose.

> No material output from pump | Not enough air pressure to pump | Shut off air at the gun, and increase air pressure to the pump to maximum. Turn regulator clockwise to increase.

> No material output from pump | Material too thick | Thin the material. Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «No material output from pump» **può indicare la causa** «Plugged hose or hose too small»

- Giudizio: `?`
- Nota: 

### R041 · Lincoln Electric POWER MIG 215 MP welder, pagina 28

**Il manuale dice:**

> No wire feed, weld output or gas flow when gun trigger is pulled. Fan does NOT operate. | 1. Make sure correct voltage is applied to the machine. 2. Make certain that power switch is in the ON position. 3. Make sure circuit breaker is reset. | If all recommended possible areas of mis- adjustment have been checked and the problem persists, Contact your local Lincoln Authorized Field Service Facility.

**Il grafo afferma:** «No wire feed, weld output, or gas flow when the gun trigger is pulled; fan does not operate» **può indicare la causa** «Unspecified cause of communication error between display and power control boards»

- Giudizio: `?`
- Nota: 

### R042 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 9

**Il manuale dice:**

> 7.7 Short duration shutdown

> For overnight or temporary shutdown periods under non-freezing conditions, the pump may remain filled with liquid. Make sure the pump is fully primed before restarting. For short or frequent shutdown periods under freezing conditions, keep fluid moving within pump casing and insulate or heat pump exterior to prevent freezing.

**Il grafo afferma:** «Short-duration or temporary pump shutdown» **può indicare la causa** «Pump liquid freezes during a short shutdown»

Contesto: [if] During short or frequent shutdown periods under freezing conditions

- Giudizio: `?`
- Nota: 

### R043 · Grizzly G0872 CNC laser cutter/engraver, pagina 51

**Il manuale dice:**

> Machine does not start, or breaker immediately trips after startup of machine or auxiliary systems. | 1. Emergency stop button depressed/at fault. 2. Incorrect power supply voltage or circuit size. 3. Power supply circuit breaker tripped or fuse blown. 4. Air pump, water chiller, or exhaust fan have a short. 5. Wiring broken, disconnected, or corroded. 6. Machine chassis ground at fault. 7. Laser tube at fault. 8. Power supply or controller at fault. 9. Computer board at fault. | 1. Rotate emergency stop button head to reset. Replace if at fault. 2. Ensure correct power supply voltage and circuit size. 3. Ensure circuit is sized correctly and free of shorts. Reset circuit breaker or replace fuse. 4. Inspect/replace if at fault. 5. Fix broken wires or disconnected/corroded connections. 6. Machine must be connected to a dedicated ground rod at/or near machine (Page 15). 7. Inspect for evidence of arcing at laser tube connections. Verify wire insulation is preventing arcing and discharge to machine frame. 8. Inspect/replace if at fault (Page 63). 9. Inspect/replace if at fault (Page 63).

> Review the troubleshooting procedures in this section if a problem develops with your machine. If you need replacement parts or additional help with a procedure, call our Technical Support. Note: Please gather the serial number and manufacture date of your machine before calling.

**Il grafo afferma:** «Emergency stop button depressed or faulty» **si affronta con** «Rotate emergency stop button head to reset» (riparazione)

- Giudizio: `?`
- Nota: 

### R044 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Gas supply, flow regulator, or gas hose fault» **si affronta con** «Check the gas supply, flow regulator, and gas hoses» (controllo o test)

- Giudizio: `?`
- Nota: 

### R045 · Graco GTX 2000EX texture sprayer, pagina 8

**Il manuale dice:**

> Before performing any Troubleshooting procedures, follow Pressure Relief procedure on page 6.

> Pulsing or surging material | Triggering too fast | Slowly squeeze trigger to fully open position while moving gun quickly in a circular motion.

> Speed of application too slow | Material too thick | Material must be mixed thoroughly to a consistency that immediately folds back in as you draw your finger through the surface of the material.

**Il grafo afferma:** «Material too thick» **si affronta con** «Thin and thoroughly mix the material until it immediately folds back after drawing a finger through its surface» (riparazione)

Contesto: [prerequisite] Before performing any troubleshooting procedures, follow the Pressure Relief procedure on page 6.

- Giudizio: `?`
- Nota: 

### R046 · LG LMH2235ST over-the-range microwave oven, pagina 30, 31, 33

**Il manuale dice:**

> CAUTION 1. DISCONNECT THE POWER SUPPLY CORD FROM THE OUTLET WHENEVER REMOVING THE OUTER CASE FROM THE UNIT. PROCEED WITH THE TEST ONLY AFTER DISCHARGING THE HIGH VOLTAGE CAPACITOR AND REMOVING THE LEAD WIRES FROM THE PRIMARY WINDING OF THE HIGH VOLTAGE TRANSFORMER. 2. ALL OPERATIONAL CHECKS WITH MICROWAVE ENERGY MUST BE DONE WITH A LOAD (1 LITER OF WATER IN CONTAINER) IN THE OVEN.

> VENTILATION MOTOR | 1. Remove lead wires. 2. Measure resistance. (ohm meter scale: Rx1) Turbo speed : White and Brown High speed: White and Blue Low speed: White and Violet Slow speed: white and Yellow | Normal: Turbo speed: Approximately 20~25ohms High speed: Approximately 40~45ohms Low speed: Approximately 50~55ohms Slow speed: Approximately 60~65ohms

> • A MICROWAVE ENERGY TEST MUST ALWAYS BE PERFORMED WHEN THE UNIT IS SERVICED FOR ANY REASON. • MAKE SURE THE WIRE LEADS ARE IN THE CORRECT POSITION. • WHEN REMOVING THE WIRE LEADS FROM THE PARTS, BE SURE TO GRASP THE CONNECTOR, NOT THE WIRES.

**Il grafo afferma:** «Ventilation motor resistance outside normal values» **si affronta con** «Measure ventilation motor resistance at turbo, high, low, and slow speed wire pairs» (controllo o test)

Contesto: [expected] Turbo: approximately 20–25 ohms; high: approximately 40–45 ohms; low: approximately 50–55 ohms; slow: approximately 60–65 ohms; [warning] A microwave energy test must always be performed when the unit is serviced for any reason; make sure wire leads are in the correct position; when removing wire leads, grasp the connector, not the wires.; [warning] Disconnect the power supply cord before removing the outer case; test only after discharging the high voltage capacitor and removing the lead wires from the primary winding of the high voltage transformer.

- Giudizio: `?`
- Nota: 

### R047 · Lincoln Electric POWER MIG 215 MP welder, pagina 27

**Il manuale dice:**

> If for any reason you do not understand the test procedures or are unable to perform the tests/repairs safely, contact your Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before you proceed.

> Service and Repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs performed on this equipment may result in danger to the technician and machine operator and will invalidate your factory warranty. For your safety and to avoid Electrical Shock, please observe all safety notes and precautions detailed throughout this manual.

> Capacitor Discharge Procedure:

**Il grafo afferma:** «Unspecified cause of communication error between display and power control boards» **si affronta con** «Contact Lincoln Electric field service if the problem persists after checking misadjustment areas» (contattare l'assistenza)

Contesto: [warning] Do not operate with panels removed. Before servicing or installing kits, disconnect the machine from power and wait at least two minutes before removing sheet metal.; [warning] If test procedures are not understood or tests/repairs cannot be performed safely, contact the Local Lincoln Authorized Field Service Facility for technical troubleshooting assistance before proceeding.; [warning] Observe all safety guidelines detailed throughout the manual.; [warning] Service and repair should only be performed by Lincoln Electric Factory Trained Personnel. Unauthorized repairs may endanger the technician and machine operator and invalidate the factory warranty; observe the manual's safety notes and precautions to avoid electrical shock.

- Giudizio: `?`
- Nota: 

### R048 · Lincoln Electric POWER MIG 215 MP welder, pagina 14

**Il manuale dice:**

> 2. Remove the cylinder cap. Inspect the cylinder valves and regulator for damaged threads, dirt, dust, oil or grease. Remove dust and dirt with a clean cloth.

**Il grafo afferma:** «Damaged cylinder valve or regulator threads» **riguarda il componente** «Flow regulator»

- Giudizio: `?`
- Nota: 

### R049 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> Periodic inspection of machine safety features: • Inspect door interlock mechanism for proper fit and function.

> • Inspect the door interlock, verify the door interlock key is not bent, misaligned, and that all fasteners are installed.

> • Inspect the door interlock itself for any signs of obstruction or misalignment.

**Il grafo afferma:** «Door interlock inspection or verification issue» **può indicare la causa** «Door interlock key bent or misaligned»

- Giudizio: `?`
- Nota: 

### R050 · Lincoln Electric POWER MIG 215 MP welder, pagina 26

**Il manuale dice:**

> Have qualified personnel do all maintenance and troubleshooting work.

> After every coil of wire, inspect the wire drive mechanism. Clean it as necessary by blowing with low pressure compressed air. Do not use solvents for cleaning the idle roll because it may wash the lubricant out of the bearing. All drive rolls are stamped with the wire sizes they will feed. If a wire size other than that stamped on the roll is used, the drive roll must be changed.

> Before carrying out service, maintenance and/or repair jobs, fully disconnect power to the machine.

**Il grafo afferma:** «Wire drive mechanism needs cleaning» **si affronta con** «Inspect the wire drive mechanism after every coil of wire» (controllo o test)

Contesto: [if] After every coil of wire; [prerequisite] Before carrying out service, maintenance, and/or repair jobs, fully disconnect power to the machine.; [prerequisite] Have qualified personnel do all maintenance and troubleshooting work.; [prerequisite] Use personal protective equipment, including safety glasses, dust mask, and gloves; this also applies to persons who enter the work area.; [warning] Moving parts can injure. Do not operate with doors open or guards off; stop engine before servicing; keep away from moving parts.

- Giudizio: `?`
- Nota: 

### R051 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 8

**Il manuale dice:**

> Do not run the pump dry or against a closed valve. Dry operation will cause seal failure within minutes.

> Clean and purge suction piping in new installations before installing and operating pump. Pipe scale, welding slag and other abrasives can cause rapid seal failure.

**Il grafo afferma:** «Mechanical shaft seal failure» **può indicare la causa** «Dry pump operation»

Contesto: [if] If the pump is run dry.

- Giudizio: `?`
- Nota: 

### R052 · LG LMH2235ST over-the-range microwave oven, pagina 2

**Il manuale dice:**

> • Routine service safety procedures should be exercised at all times.

> • Untrained personnel should not attempt service without a thorough review of the test procedures and safety information contained in this manual.

> a. Do not operate or allow the oven to be operated with the door open.

**Il grafo afferma:** «Interlock operation fault» **si affronta con** «Check interlock operation» (controllo o test)

Contesto: [prerequisite] Before activating the magnetron or another microwave source, make the listed safety checks on all ovens to be serviced and make repairs as necessary.; [warning] Do not operate or allow the oven to be operated with the door open.; [warning] Routine service safety procedures should be exercised at all times.; [warning] Untrained personnel should not attempt service without thoroughly reviewing the manual's test procedures and safety information.

- Giudizio: `?`
- Nota: 

### R053 · Haas vertical mill (2023 operator's manual), pagina 26

**Il manuale dice:**

> This feature will display a warning message when the [FWD] or [REV] button is pressed and the previous commanded spindle speed is above the Spindle Maximum Manual Speed parameter. Press [ENTER] to go to the previous commanded spindle speed or press [CANCEL] to cancel the action.

> MACHINE / SPINDLE OPTION | SPINDLE MAXIMUM MANUAL SPEED

> Mills | 5000

**Il grafo afferma:** «Previous commanded spindle speed is above the Spindle Maximum Manual Speed parameter» **si affronta con** «Return to the previous commanded spindle speed» (riparazione)

- Giudizio: `?`
- Nota: 

### R054 · ABB ACS580-01 variable speed drive, pagina 374

**Il manuale dice:**

> • make sure that the value of both parameters 15.01 Extension module type and 15.02 Detected extension module is CAIO-01.

> If warning A7AB Extension I/O configuration failure is shown,

> • make sure that the value of 15.02 is CAIO-01.

**Il grafo afferma:** «Extension I/O configuration failure» **(codice) indica la causa** «Extension module type parameter is not set to CAIO-01»

- Giudizio: `?`
- Nota: 

### R055 · ABB ACS580-01 variable speed drive, pagina 220

**Il manuale dice:**

> The drive module heatsink fins pick up dust from the cooling air. The drive runs into overtemperature warnings and faults if the heatsink is not clean. When necessary, clean the heatsink as follows.

**Il grafo afferma:** «Heatsink overtemperature warnings and faults» **può indicare la causa** «Dirty heatsink fins»

- Giudizio: `?`
- Nota: 

### R056 · Haas vertical mill (2023 operator's manual), pagina 86

**Il manuale dice:**

> Umbrella Tool Changer Recovery

> If the tool changer jams, the control will automatically come to an alarm state. To correct this:

> 1. Remove the cause of the jam.

**Il grafo afferma:** «Unspecified cause of umbrella tool changer jam» **riguarda il componente** «Umbrella tool changer»

- Giudizio: `?`
- Nota: 

### R057 · Haas vertical mill (2023 operator's manual), pagina 112

**Il manuale dice:**

> When your program calls an M98 subprogram, the control looks for the subprogram in the main program’s directory. If the control cannot find the subprogram in the main program’s directory, it then looks in the location specified in Setting 251. An alarm occurs if the control cannot find the subprogram.

**Il grafo afferma:** «Alarm when the external subprogram cannot be found» **può indicare la causa** «External subprogram not found in the searched locations»

- Giudizio: `?`
- Nota: 

### R058 · Grizzly G0872 CNC laser cutter/engraver, pagina 15

**Il manuale dice:**

> TOXIC FUMES. Cutting or engraving metals and plastics give off highly toxic fumes, vapors, and air particulates containing zinc, lead, beryllium, cadmium, mercury, fluorine, hexavalent chromi- um, chlorine gas, and many others. These fumes and air contaminants can damage the machine and harm your health. If the air filtration system or exhaust system is malfunctioning, immediately stop operations and correct the issue.

**Il grafo afferma:** «Exhaust system malfunction» **si affronta con** «Correct the exhaust or air filtration system issue» (riparazione)

Contesto: [warning] If the exhaust system or air filtration system is malfunctioning, stop operations immediately.

- Giudizio: `?`
- Nota: 

### R059 · ABB ACS580-01 variable speed drive, pagina 119

**Il manuale dice:**

> 2. Make sure that the resistor cable is connected to the resistor and disconnected from the drive output terminals.

> 3. At the drive end, connect the R+ and R- conductors of the resistor cable together. Measure the insulation resistance between the conductors and the PE conductor with a measuring voltage of 1000 V DC. The insulation resistance must be more than 1 Mohm.

**Il grafo afferma:** «Low insulation resistance between resistor cable conductors and PE» **riguarda il componente** «Brake resistor cable»

- Giudizio: `?`
- Nota: 

### R060 · Grizzly G0872 CNC laser cutter/engraver, pagina 50

**Il manuale dice:**

> Storing Machine

> For long-term machine storage, or when not in operation during winter months, it is MANDATORY that ALL water is drained from the laser tube. Freezing temperatures can be encountered even in heated buildings or storage facilities from power outages. Water left in the laser tube may freeze and break the internal glass cooling coils. Damage to the laser tube after shipping is NOT covered under warranty.

> Perform ALL maintenance procedures for clean­ ing and lubrication as outlined in SECTION 6: MAINTENANCE on Page 40 before placing machine into storage.

**Il grafo afferma:** «Machine is being stored long-term or during winter months» **può indicare la causa** «Water left in the laser tube freezes and breaks internal glass cooling coils»

- Giudizio: `?`
- Nota: 

### R061 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 6

**Il manuale dice:**

> Check pumping unit for shortage and damage immediately upon arrival. Pump accessories when required are packaged in a separate container and shipped with the unit. If equipment is damaged in transit, promptly report this to the carrier's agent. Make complete notations on the freight bill to speed satisfactory adjustment by the carrier. Unload and handle the unit with a sling.

> WARNING Crushing of feet Death or serious personal injury ‐ Do not lift pump assembly by motor eye bolts alone. Motor eye bolts are not designed to support weight of entire pump assembly.

**Il grafo afferma:** «Unspecified cause of equipment damage in transit» **si affronta con** «Check the pumping unit for damage immediately upon arrival» (controllo o test)

Contesto: [if] Immediately upon arrival; [warning] Do not lift the pump assembly by motor eye bolts alone; the motor eye bolts are not designed to support the entire pump assembly's weight.

- Giudizio: `?`
- Nota: 

### R062 · Haas vertical mill (2023 operator's manual), pagina 20

**Il manuale dice:**

> • If the alarms do not reset or you are unable to clear a blockage, contact your Haas Factory Outlet (HFO) for assistance. Follow these guidelines when you work with the machine: • Normal operation - Keep the door closed and guards in place (for non-enclosed machines) while the machine operates.

**Il grafo afferma:** «Unresolved alarm or blockage» **si affronta con** «Contact the Haas Factory Outlet for assistance» (contattare l'assistenza)

- Giudizio: `?`
- Nota: 

### R063 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

> 2. Tip sprayer to allow material (water) to flow out of pump inlet.

> Before adding material or starting unit in cold weather, run warm water through pump.

**Il grafo afferma:** «Water or material remaining in the unit below freezing» **riguarda il componente** «Pump»

Contesto: [if] Water or material remains in the unit when temperatures are below freezing

- Giudizio: `?`
- Nota: 

### R064 · Haas vertical mill (2023 operator's manual), pagina 160

**Il manuale dice:**

> G04 P1.0 ;

> M59 P3 ;

> This turns on tool probe

**Il grafo afferma:** «Tool probe does not operate correctly» **si affronta con** «Run the tool probe MDI commands» (controllo o test)

Contesto: [expected] The tool probe LED flashes green.

- Giudizio: `?`
- Nota: 

### R065 · LG LMH2235ST over-the-range microwave oven, pagina 2

**Il manuale dice:**

> b. Make the following safety checks on all ovens to be serviced before activating the

> magnetron or other microwave source, and make repairs as necessary; (1) Interlock operation, (2) proper door closing, (3) seal and sealing surfaces (arcing, wear, and other damage), (4) damage to or loosening of hinges and latches, (5) evidence of dropping or abuse.

**Il grafo afferma:** «Unspecified cause of potential excessive microwave energy exposure» **riguarda il componente** «Door»

- Giudizio: `?`
- Nota: 

### R066 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 34. The operating conditions of the installation do not agree with the data specified when the pump was purchased.

> Pump stops delivering liquid after start-up 2*3*4*5*6*7*8*9*10*11*12*13*22*23*24*34

**Il grafo afferma:** «Pump stops delivering liquid after start-up» **può indicare la causa** «Installation operating conditions differ from purchase data»

- Giudizio: `?`
- Nota: 

### R067 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 34, 35

**Il manuale dice:**

> Please consult us if you intend to run the pump with other oils or special lubricants. The oil filling levels stated in Figure 4 - which apply to the shutdown (standing still) pump - must be observed. The filling level visible in the oil-sight glass depends on the size of the pump and the type of oil used. If the oil level is too low, the bearings and gearwheels are not lubricated adequately; if it is too high, oil may enter the pumping chamber or the pump may overheat. Clean the oil-fill port and reinstall the plug using a gasket which is in perfect condition. Wipe off any oil residues from the casing. The oil-fill port must be sealed air-tight.

> Under dirty operating conditions, contaminants may be deposited in the pumping chamber or on the rotors. After removing the two connecting lines, the contaminants can be blown out with dry compressed air or flushed out with a suitable solvent. Contaminants that cannot be blown or flushed out, can be removed completely from the pumping chamber with a wire brush, metallic sponge or scraper. Then change the oil.

**Il grafo afferma:** «Insufficient lubrication from low oil level» **riguarda il componente** «Pumping chamber»

- Giudizio: `?`
- Nota: 

### R068 · Atlas Copco DRB 250-2000 vacuum booster pump, pagina 20

**Il manuale dice:**

> If the oil level is too low, the bearings and gearwheels are not lubricated adequately; if it is too high oil may enter the pumping chamber or the pump may overheat. Clean the oil-fill port and screw the plug back in using a gasket which is in perfect condition. The oil-fill port must be sealed air-tight. Entry of air from the outside may cause oil-containing gas to enter the pumping chamber via the rotors seals.

**Il grafo afferma:** «Air enters through the oil-fill port» **si affronta con** «Clean the oil-fill port» (riparazione)

- Giudizio: `?`
- Nota: 

### R069 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

> To insure water and material are completely drained out of unit:

> 2. Tip sprayer to allow material (water) to flow out of pump inlet.

**Il grafo afferma:** «Water or material remaining in the unit can damage the pump or delay startup» **si affronta con** «Tip the sprayer to drain material or water from the pump inlet» (riparazione)

Contesto: [warning] Water or material remaining in the unit below freezing can damage the pump and/or delay startup.; [warning] Wear appropriate protective equipment when operating, servicing, or in the operating area, including protective eyewear, clothing and respirator as recommended by the fluid and solvent manufacturer, gloves, and hearing protection.

- Giudizio: `?`
- Nota: 

### R070 · Grundfos Paco VL/VLS in-line centrifugal pump, pagina 15

**Il manuale dice:**

> 9. The suction valve is closed or only partially open.

> Pump stops delivering liquid after start-up 2*3*4*5*6*7*8*9*10*11*12*13*22*23*24*34

**Il grafo afferma:** «Pump stops delivering liquid after start-up» **può indicare la causa** «Suction valve closed or partially open»

- Giudizio: `?`
- Nota: 

### R071 · Graco GTX 2000EX texture sprayer, pagina 3

**Il manuale dice:**

> NOTICE Water or material remaining in unit when temperatures are below freezing can damage pump and/or delay startup.

> To insure water and material are completely drained out of unit:

> 2. Tip sprayer to allow material (water) to flow out of pump inlet.

**Il grafo afferma:** «Water or material remaining in the unit below freezing» **si affronta con** «Tip the sprayer to drain material or water from the pump inlet» (riparazione)

Contesto: [order] Step 2; [warning] Water or material remaining in the unit when temperatures are below freezing can damage the pump or delay startup.

- Giudizio: `?`
- Nota: 

### R072 · Grizzly G0872 CNC laser cutter/engraver, pagina 49, 50

**Il manuale dice:**

> Water quality and effective cooling directly con­ tribute to the operational life of the laser tube. The cooling system requires distilled water to prevent scaling and contaminant build-up. Due to oxygenation and warm temperatures inherent in the system, water needs to be checked regu­ larly for evidence of algae or unpleasant odors. Mildew growth can reduce cooling efficiency and decrease tube life.

> 5. Reconnect water chiller system to power and turn ON. Allow water to cycle for 5 minutes and verify air bubbles have released from laser tube.

> For long-term machine storage, or when not in operation during winter months, it is MANDATORY that ALL water is drained from the laser tube. Freezing temperatures can be encountered even in heated buildings or storage facilities from power outages. Water left in the laser tube may freeze and break the internal glass cooling coils. Damage to the laser tube after shipping is NOT covered under warranty.

**Il grafo afferma:** «Water left in the laser tube freezes and breaks internal glass cooling coils» **riguarda il componente** «Laser tube»

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
