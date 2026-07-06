# Fryer VB Series FANUC 0i-MF CNC Maintenance Manual

Document type: maintenance manual
Language: English
Asset: Fryer VB Series Vertical Machining Center (FANUC 0i-MF control)

## Page 1 - Cover

VB SERIES FANUC 0i MF CONTROL MAINTENANCE MANUAL.
Fryer Machine Systems, Patterson, NY, USA.

## Page 2 - Manual Index

1.0 Safety information.
2.0 Basic installation.
3.0 General information. 3.1 Maintenance schedule chart. 3.31 FANUC machine
reference procedure after absolute encoder alarm. 3.32 Check axis backlash.
3.33 Adjusting backlash compensation.
4.0 FANUC control. 4.09 M-codes. 4.10 Alarms. 4.11 Fryer PLC alarms and
descriptions. 4.12 Clearing an alarm.
5.0 Automatic tool changer. ATC troubleshooting. ATC maintenance.
6.0 Drawings and parts lists.

## Page 4 - Safety Information

READ BEFORE INSTALLING OR OPERATING. This machine is automatically
controlled and may start at any time. Use appropriate eye and ear protection
while operating the machine. ANSI-approved impact safety glasses are
required. When restarting a machine after it has been shut down always
assume it has been altered. Recheck offsets and programs before running.
Always follow all Lock Out / Tag Out procedures before performing any
maintenance.

## Page 13 - Maintenance Schedule Chart

3.0 GENERAL INFORMATION. 3.1 Maintenance Schedule Chart.
CAUTION! Always follow all Lock Out / Tag Out procedures before performing
any maintenance.

Daily: check air pressure gage (90 - 125 PSI). At the end of the day remove
and dispose of chips; use of brush or vacuum is recommended. Check axis
lubrication pump oil level; use Mobil Vactra #2 (ISO 68) or equivalent.
Weekly: clean chips from interior of ATC. Check pneumatic (air) lubrication
oil. Check coolant level.
Every 6 months: check machine level. Check axis backlash (see procedure in
Section 3.32). Remove and clean underside of waycovers. Check ballscrew
endplay. Check axis motor belts. Grease ATC cam pockets.
As required: change coolant. Check and change electrical cabinet air
filters. Change ATC gearbox oil yearly.

## Page 20 - Reference Procedure After Absolute Encoder Alarm

3.31 FANUC Machine Reference Procedure after Absolute Encoder Alarm.
PROCEDURE TO BE PERFORMED BY QUALIFIED PERSONNEL ONLY.

This procedure must be followed after the encoder is disconnected or battery
for the absolute encoder goes dead or if parameters are reloaded. The
machine normally remembers the position of the table due to the absolute
encoder tracking. If this is lost the machine home position is also lost.
Each axis should be positioned at the home position and the alignment marks
lined up.

Referencing the axis: The X, Y and Z-axis have battery backed up encoders
(absolute encoders). The control will give advance notice of a weak battery
so it can be changed before position loss occurs. If the encoder is
disconnected an error will occur, you will have to reference the axis.
Follow this procedure:

1. Press offset setting - parameter - write enable (OFS/SET hard key twice),
set parameter write enable bit to 1.
2. Press system (hard key), type 1815, press no. search. Parameter 1815 is
the reference position parameter setting. Set APZ bits for the axis wishing
to reference to 0. If you already have an alarm about lost encoder position
the troubled axis will have a zero set in this bit.
3. Power down completely.
4. Power up, drives on, and jog the axis requiring referencing to align with
the scribe marks on the red painted washer. Be very careful you do not crash
the machine!
5. Change 1815 APZ bit to 1 for the axis wishing to reference. Change the
parameter write enable bit to 0.
6. Power down completely.
7. Power up, drives on. The axis display should read 0 and there should be
no alarms.

## Page 21 - Check Axis Backlash and Adjust Compensation

3.32 Check Axis Backlash. Tools required: 0.0001 inch resolution dial
indicator, remote handwheel (manual pulse generator). Set the indicator
along the axis which is being measured. Using the remote handwheel, move the
axis in one direction, then reverse. The difference shows the loss of motion
in the axis from the ballscrew and linear guide rails.

3.33 Adjusting Backlash Compensation. PROCEDURE TO BE PERFORMED BY QUALIFIED
PERSONNEL ONLY. If the measured backlash is out of specification, backlash
compensation can be adjusted according to the procedure outlined in Section
3.33.

## Page 29 - M-Codes

4.09 M-Codes. An M code in CNC programming controls miscellaneous machine
functions, including starting and stopping specific actions or programs.

M00 program stop. M03 spindle clockwise. M05 spindle stop. M06 tool change
requested. M08 flood coolant. M19 spindle orient. M52 ATC carousel in (arm
ATC pot down). M53 ATC carousel out (arm ATC pot up). M58 ATC carousel CW 1
position. M59 ATC carousel CCW 1 position. M61 home ATC carousel to pocket
1, assumes tool 0 in spindle. M62 arm ATC grab tool. M63 arm ATC arm origin.

Note: M-codes may change depending on options the machine is equipped with.

## Page 30 - Alarms and Fryer PLC Alarm Descriptions

4.10 Alarms. An alarm will be displayed once a fault occurs.
! Warning: if you do not heed an alarm that is issued and do not resolve the
cause of the alarm, it can present a hazard to the machine, the work piece,
the saved settings, and in certain circumstances may cause injury.

4.11 Fryer PLC Alarms and Descriptions. These are Fryer machine specific
alarms that are for optional equipment installed on the machine. The alarms
are listed below (NO. / ADDRESS / MESSAGE):

Alarm 1001 (A001.0): LOW WAY LUBE.
Alarm 1002 (A001.1): LOW AIR PRESSURE.
Alarm 2001 (A001.2): ATC HOME REMOVE TOOL FROM SPINDLE.
Alarm 2002 (A001.3): TOOL NUMBER [I220, D110] IS IN SPINDLE.
Alarm 1003 (A001.4): ERROR TOOL CODE NOT ALLOWED.
Alarm 1005 (A001.5): SPINDLE CHILLER ALARM.
Alarm 1006 (A001.6): HIGH PRESS. COOLANT FAULT.
Alarm 1007 (A001.7): GEARSHIFT FAULT.
Alarm 1008 (A002.0): OUT OF GEAR FAULT.
Alarm 1009 (A002.1): ATC ARM OUT OF POS.
Alarm 1010 (A002.2): PROBE FAULT.
Alarm 1011 (A002.3): ATC CAR. MISCOUNT - DO M61 !!!!
Alarm 1012 (A002.4): ATC E-STOP ALARM - CHK TOOLS.
Alarm 1013 (A002.5): ATC ABORTED BY RESET - CHK TOOLS.
Alarm 1014 (A002.6): DOOR INTERLOCK OPEN.
Alarm 1015 (A002.7): PROBE BATTERY LOW.
Alarm 1016 (A003.0): DOOR CLOSE OBSTRUCTION - TIMED OUT.
Alarm 2001 (A003.1): WAY LUBE PRESSURE FAULT.

4.12 Clearing an Alarm. 1. Press RESET. 2. Certain alarms will require a
reboot of the control to clear.

## Page 46 - Electric Arm Type ATC Repair Procedures

ELECTRIC ARM TYPE ATC - REPAIR PROCEDURES.
1. To dismantle and reinstall the splined output shaft: turn to origin
position, remove the taper pin (246) and M8 bolt (227) on the case cap.
Remove the case cap (101B). Loosen hexagonal screw (225) and remove the
front fix cap (111). Remove the splined output shaft (106). Reassemble in
reverse order.
2. To change the bearings on bearing tube: turn to origin position, remove
the case cap. Rotate the bearings tube (108) to the standby position. Use
the special tool to remove the bearings (134) and reinstall the new
bearings. Reassemble in reverse order.

## Page 47 - ATC Troubleshooting

ATC TROUBLESHOOTING.
(The ATC troubleshooting chart in the source manual is provided as a
drawing without machine-readable text.)
