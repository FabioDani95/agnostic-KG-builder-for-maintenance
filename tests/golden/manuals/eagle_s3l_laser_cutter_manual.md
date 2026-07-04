# Eastman Eagle S3L Laser Cutting System Service Manual

Document type: service manual
Language: English
Asset: Eastman Eagle S3L Laser Cutting System

## Page 1 - Cover

THE EASTMAN

Eagle Automatic Laser Cutting System
Model: Eagle S3L
Form E-554

Service Manual

This machine is equipped with a class IV laser product. Avoid eye or skin exposure
to direct or scattered radiation at all times. Approved laser protective eyewear
required.

## Page 2 - Manual Index

Safety Information ....................................................... 3
General Safety Precautions ......................................... 3
Laser Safety Precautions ............................................ 4
Eagle S3L Familiarization ........................................... 7
INSTALLATION ............................................................ 8
SERVICE and MAINTENANCE ................................. 13
Aligning, Cleaning and Replacing Consumables ........ 13
Laser Mirror Replacement ......................................... 22
Laser Focus Lens Replacement ................................ 23
Laser Optics Cleaning ............................................... 24
Fume Extractor Filter Replacement ........................... 24
CALIBRATION & ADJUSTMENTS ............................. 25
SCHEDULES MAINTENANCE PROCEDURES......... 28
Yearly Maintenance Checklist ................................... 31
TROUBLE SHOOTING GUIDE .................................. 37
ELECTRICAL & PNEUMATIC DIAGRAMS ................ 39
Pneumatic Diagram Blue Print No. (31-9000-41) ....... 40

## Page 35 - Preventive Maintenance Checklists

Laser Bridge Assembly

Comments
Signoff

Inspect all covers for proper fit.
Check safety labels. Replace if damaged.
Inspect all safety limit switches for proper operation.
Remove fume extractor funnel. Clean and inspect for damage.
Check Coolant, Co2 and air Purge lines for leaks
Check laser enable light for proper operation.
Check all cables for any wear, cracks or loose connections.
Inspect and clean laser beam mirrors (3).
Inspect and clean laser beam focusing lens (3).
Check brass laser beam nozzle for damage.
Check laser beam for proper alignment and focus.
Check & secure all screws.

Diagnostic Cabinet

Comments
Signoff

Inspect all internal components for discoloration and ensure screw terminals
and wiring connectors are tight and secure
Clean inside using dry compressed air.
Clean and inspect fans for proper operation.

## Page 36 - Preventive Maintenance Checklists (continued)

Rack & Rail Assembly

Comments
Signoff

Clean and oil linear rails.
Check rack and rail gap(s).
Check rack and rail for wear.
Check shocks for proper operation.
Tighten all Linear rail screws (M3).
Tighten rack screws (#10-32 x 1/2).
Check & secure all screws.

Table Vacuum Assembly

Comments
Signoff

Inspect blower motors for excessive noise. Clean as required.
Inspect blower power cables for cracks or wear.
Check vacuum piping for leaks and loose hardware.

Variable Frequency Drives (VFD)

Comments
Signoff

Check cables for cracks and wear.
Inspect and clean VFD cooling fan and filter.

Computer Assembly

Comments
Signoff

Check all cable connections. Secure as required.
Inspect and clean computer fan and filter.

## Page 37 - Trouble Shooting Guide

TROUBLE SHOOTING GUIDE

Warning

Always disconnect power source (lockout/tagout) to machine before proceeding
with any maintenance, adjustments or repair. Failure to disconnect power may
cause serious personal injury and/or damage to machine.

Warning

This machine is equipped with a very sharp knife and powerful laser. Use caution
when working on this machine. Failure to keep hands, arms, and loose objects
away from knife area may cause serious personal injury.

Service and maintenance to this machine should be performed by qualified
personnel. If you do not have qualified personnel, contact your Eastman Sales
Representative or Eastman Factory direct.

Problem: UIT Does Not Power Up

Description of Problem:

The UIT does not power. Screen is blank and not lit up.

Troubleshooting:

1. Touch the screen to see if it turns on. If the machine sits idle for a long
period of time the touch screen goes into a sleep mode to protect the screen.
2. Make sure your cutting software is open on the cutting system computer.
4. Find the black ethernet power supply (PoE) located next to the computer.
Verify the green LED is illuminated.
5. If there is no green LED lit, check the AC outlets located on the back of the
diagnostic cabinet. If there is no AC power, check the AC power cord and fuses
F3 and F4 in the diagnostic cabinet.

Problem: Machine Stop during Cut Due to Unintentional pause

Description of Problem:

The machine stops in middle of cut and displays message "Machine Paused, Press
Zero, Next or Abort" on Touch Screen. When pressing NEXT on the keypad, the
machine will continue to cut where it left off. This is typically caused by an
intermittent pause circuit, usually in the stop discs.

Troubleshooting:

1. Check stop disc activation. The stop discs should not activate by a slight
touch or vibration. They should activate only when moved by minimum pressure.
Remove gantry side cover. Check the pause plunger. Tighten the plunger to increase activation pressure and loosen to decrease activation pressure.

Problem: The buttons on the Touch Screen are out of alignment

Description of Problem:

The touch screen buttons do not match where the screen needs to be touched to
activate the command. Operator needs to push above, below, right or left of the
button for the command to take effect.

Troubleshooting:

Touch screen calibration is required. Proceed as follows.
1. Power down the cutting system.
2. Place finger on the upper left corner of the touch screen as Shown. While
holding finger on the screen, turn ON the main power switch located on the back
of the diagnostic control cabinet.
3. Remove finger after the "Power On Setup" screen appears.
4. Using the left and right arrows to navigate, go to the Calibration Screen
(screen page 2). Press Touch screen to begin calibrating.

## Page 38 - Trouble Shooting Guide (continued)

5. Using a paper clip or fine tip object, press the center of the cross as
shown. The cross will reappear in the lower right corner. Press the center of
the cross.
6. Navigate to screen page 3. Select save and exit to complete calibration.
The touch screen will restart in normal mode. Check for proper screen operation
and begin your normal start-up procedure.

Problem: The Cutting Tool or Pen does not move down

Description of Problem:

The tool or Pen does not move down when cutting a file or they are delayed
coming down at the beginning of a cut. This can be caused by an electrical
short, tool mapping in software or a problem with the power supply.

Troubleshooting:

1. Make sure the gantry Tools ON switch is turned on. This can be verified by
making sure the laser pointer is on.
2. Verify the mapping of your tools and layers are mapped properly under each
tool.
a. Look at the tool bar at the bottom of the Cut window to quickly verify tool and layer mapping. If there is no Tool Bar as shown, then click on "View" then
click on "Layers" and "Tools" in the main E-Suite menu.
b. If the layer is not mapped to a tool or the tool is not on the tool holder
then just click and drag the tool to the spindle or the layer to the tool before
sending the file to the cutter.
3. With E-Suite closed, check tool holder to see if it moves freely and is not
damaged or bent.
4. Make sure you have pressure at the tools. Try pulling the tool holder down by
hand to see if it has pressure.
5. Check tool connections.
a. Hit the Cut Down button on the UIT to verify the corresponding green LED
light is on. Located on the slice output cards (non-operator gantry side plate).
b. Try firing the tool manually by pressing red button under solenoid block.
Each solenoid can be manually fired by pressing the individual button.
c. Check cable connection at air manifold for proper connection.
6. The Pen or Tool delays coming down and misses the beginning of marker or cut.
a. Check the 24 VDC power supply located in the diagnostic cabinet. Make sure
the green led is on.
b. Check the 24 VDC power supply fuse.
c. Check flow control valves on the pen air cylinder.

Problem: Laser Fume Extractor has reduced vacuum or no vacuum.

Description of Problem:

An odor is present when cutting with the laser tool or Laser cutting path is
wider than normal

Troubleshooting:

1. Check the laser fume extractor for power and is turned ON.
2. Increase vacuum pressure using the fume extractor control panel.
3. Replace vacuum filters.
4. Clean vacuum hose and funnel.

## Page 39 - Trouble Shooting Guide (continued)

Problem: Laser cutting path is too wide

Description of Problem:

The laser cutting path increases to an undesirable width.

Troubleshooting:

1. Check for damage to brass laser nozzle. Replace nozzle if any damage is present.
2. Check for brass laser nozzle alignment. If the tube or nozzle is bent, the
laser beam will reflect off the inside wall of the nozzle causing a wide path.
To verify, perform a test pulse on a piece of card board. If the dot has a ring
or partial ring around it, the nozzle is bent or the mirrors may need to be adjusted.
3. Check laser power and cutting speed. Settings may vary when changing
materials. Testing will yield best results.

RF/EMI Interference

Some factory environments may have equipment that generates Radio Frequency
(RF) or Electro-Magnetic Interference (EMI). These signals in close proximity to
the Eastman cutting system can generate electrical noise and cause problems for
the machine and computer (Eastman does offer a shielded mouse). It is
recommended that any RF Welders or other equipment generating RF or EMI noise be
a minimum of 75 feet (23 meter) from the Eastman cutting system.

Problem: Loss of laser cutting power

Description of Problem:

The laser cutting power decreases causing non-cut edges.

Troubleshooting:

1. Damaged or dirty lens. Check for damage or dirt on the focusing lens. Clean or replace lens as required.
2. Damaged or dirty Mirror. Check for damage, burn mark or dirt on the beam deflecting mirrors. Clean or replace mirrors as required.
3. Damage or debris in laser nozzle. Check for damage or debris in laser nozzle.
Clean or replace laser nozzle as required.
