# ABB IRC5 Robot Controller Trouble Shooting Manual

Document type: operating manual, trouble shooting
Language: English
Asset: ABB IRC5 Robot Controller

## Page 1 - Cover

ABB Robotics. Operating manual. Trouble shooting, IRC5.
Document ID: 3HAC020738-001. Revision: K.

## Page 5 - Index

1 Safety (page 15). 1.5.3 WARNING - The unit is sensitive to ESD (page 19).
2 Trouble shooting, general (page 23).
3 Troubleshooting by fault symptoms (page 31).
3.1 Start-up failures (page 31). 3.2 Controller not responding (page 33).
3.3 Low Controller performance (page 34). 3.4 All LEDs are OFF at Controller
(page 36). 3.5 No voltage in service outlet (page 38). 3.6 Problem starting
the FlexPendant (page 40). 3.7 Problem connecting FlexPendant to the
controller (page 41). 3.8 Erratic event messages on FlexPendant (page 42).
3.9 Problem jogging the robot (page 43). 3.10 Reflashing firmware failure
(page 44). 3.11 Inconsistent path accuracy (page 45). 3.12 Oil and grease
stains on motors and gearboxes (page 46). 3.13 Mechanical noise (page 47).
3.14 Manipulator crashes on power down (page 49). 3.15 Problem releasing
Robot brakes (page 50). 3.16 Intermittent errors (page 52).
4 Trouble shooting by Unit (page 53).
5 Descriptions and background information.
6 Trouble shooting by Event log (page 83).

## Page 7 - Overview of this manual

About this manual: this manual contains information, procedures and
descriptions, for trouble shooting IRC5 based robot systems.
Usage: this manual should be used whenever robot operation is interrupted by
malfunction, regardless of whether an error event log message is created or
not.
Who should read this manual: machine and robot operators qualified to perform
very basic trouble shooting and reporting to service personnel; programmers
qualified to write and change RAPID programs; specialized trouble shooting
personnel, usually very experienced service personnel, qualified for
methodically isolating, analyzing and correcting malfunctions within the
robot system.
References: Product manual - IRC5 (3HAC021313-001). Operating manual - IRC5
with FlexPendant (3HAC16590-1). Operating manual - RobotStudio (3HAC032104-001).

## Page 21 - WARNING - The unit is sensitive to ESD

1 Safety. 1.5.3 WARNING - The unit is sensitive to ESD.
Description: ESD (electrostatic discharge) is the transfer of electrical
static charge between two bodies at different potentials, either through
direct contact or through an induced electrical field. When handling parts or
their containers, personnel not grounded may potentially transfer high static
charges. This discharge may destroy sensitive electronics.
Elimination: use a wrist strap (wrist straps must be tested frequently to
ensure that they are not damaged and are operating correctly). Use an ESD
protective floor mat (the mat must be grounded through a current-limiting
resistor). Use a dissipative table mat.
The wrist strap button is located in the top right corner of the IRC5.

## Page 33 - Start-up failures

3 Troubleshooting by fault symptoms. 3.1 Start-up failures.
Introduction: this section describes possible faults during start-up and the
recommended action for each failure.
Consequences: problem starting the system.
Symptoms and causes. The following are the possible symptoms of a start-up
failure: LEDs not lit on any unit. Earth fault protection trips. Unable to
load the system software. FlexPendant not responding. FlexPendant starts, but
does not respond to any input. Disk containing the system software does not
start correctly.
Recommended actions. NOTE: this may be due to a loss of power supply in many
stages.
Action 1: make sure the main power supply to the system is present and is
within the specified limits. Your plant or cell documentation can provide
this information.
Action 2: make sure that the main transformer in the Drive module is
correctly connected to the mains voltage levels at hand. How to strap the
mains transformer is detailed in the product manual for the controller.
Action 3: make sure that the main switches are switched on.
Action 4: make sure that the power supply to the Control module and Drive
module are within the specified limits.

## Page 34 - Start-up failures (continued)

Action 5: if no LEDs lit, proceed to section All LEDs are OFF at Controller.
Action 6: if the system is not responding, proceed to section Controller not
responding.
Action 7: if the FlexPendant is not responding, proceed to section Problem
starting the FlexPendant.
Action 8: if the FlexPendant starts, but does not communicate with the
controller, proceed to section Problem connecting FlexPendant to the
controller.

## Page 35 - Controller not responding

3 Troubleshooting by fault symptoms. 3.2 Controller not responding.
Description: this section describes the possible faults and the recommended
actions for each failure: robot controller not responding; LED indicators not
lit.
Consequences: system cannot be operated using the FlexPendant.
Possible causes and recommended actions:
1. Cause: controller not connected to the mains power supply. Recommended
action: ensure that the mains power supply is working and the voltage level
matches that of the controller requirement.
2. Cause: main transformer is malfunctioning or not connected correctly.
Recommended action: ensure that the main transformer is connected correctly
to the mains voltage level.
3. Cause: main fuse (Q1) might have tripped. Recommended action: ensure that
the mains fuse (Q1) inside the Drive Module is not tripped.
4. Cause: connection missing between the Control and Drive modules.
Recommended action: if the Drive Module does not start although the Control
Module is working and the Drive Module main switch has been switched on,
ensure that all the connections between the Drive module and the Control
module are connected correctly.

## Page 38 - All LEDs are OFF at Controller

3 Troubleshooting by fault symptoms. 3.4 All LEDs are OFF at Controller.
Description: no LEDs at all are lit on the Control Module or the Drive Module
respectively.
Consequences: the system cannot be operated or started at all.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): the system is not supplied with power; the main transformer
is not connected for the correct mains voltage; circuit breaker F6 (if used)
is malfunctioning or open for any other reason; contactor K41 is
malfunctioning or open for any other reason.

## Page 39 - All LEDs are OFF at Controller (continued)

Recommended actions:
1. Make sure the main switch has been switched on.
2. Make sure the system is supplied with power. Use a voltmeter to measure
incoming mains voltage.
3. Check the main transformer connection. The voltages are marked on the
terminals. Make sure they match the shop supply voltage.
4. Make sure circuit breaker F6 (if used) is closed in position 3. The
circuit breaker F6 is shown in the circuit diagram in the product manual for
the controller.
5. Make sure contactor K41 opens and closes when ordered.
6. Disconnect connector X1 from the Drive Module power supply and measure the
incoming voltage. Measure between pins X1.1 and X1.5.
7. If the power supply incoming voltage is correct (230 VAC) but the LEDs
still do not work, replace the Drive Module power supply. Replace the power
supply as detailed in the product manual for the controller.

## Page 40 - No voltage in service outlet

3 Troubleshooting by fault symptoms. 3.5 No voltage in service outlet.
Description: some Control Modules are equipped with service voltage outlet
sockets, and this information applies to these modules only. No voltage is
available in the Control Module service outlet for powering external service
equipment.
Consequences: equipment connected to the Control Module service outlet does
not work.
Probable causes. The symptom can be caused by (the causes are listed in order
of probability): tripped circuit breaker (F5); tripped earth fault protection
(F4); mains power supply loss; transformers incorrectly connected.

## Page 41 - No voltage in service outlet (continued)

Recommended actions:
1. Make sure the circuit breaker in the Control Module has not been tripped.
Make sure any equipment connected to the service outlet does not consume too
much power, causing the circuit breaker to trip.
2. Make sure the earth fault protection has not been tripped. Make sure any
equipment connected to the service outlet does not conduct current to ground,
causing the earth fault protection to trip.
3. Make sure the power supply to the robot system is within specifications.
Refer to the plant documentation for voltage values.
4. Make sure the transformer supplying the outlet is correctly connected,
i.e. input and output voltages in accordance with specifications.

## Page 45 - Problem jogging the robot

3 Troubleshooting by fault symptoms. 3.9 Problem jogging the robot.
Description: the system can be started but the joystick on the FlexPendant
does not work.
Consequences: the robot can not be jogged manually.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): the joystick is malfunctioning; the joystick may be
deflected.
Recommended actions. The following actions are recommended (listed in order
of probability):
1. Make sure the controller is in manual mode. How to change operating mode
is described in Operating manual - IRC5 with FlexPendant.
2. Make sure the FlexPendant is connected correctly to the Control Module.
3. Reset the FlexPendant. Press the Reset button located on the back of the
FlexPendant. NOTE: the Reset button resets the FlexPendant, not the system on
the Controller.

## Page 48 - Oil and grease stains on motors and gearboxes

3 Troubleshooting by fault symptoms. 3.12 Oil and grease stains on motors and
gearboxes.
Description: the area surrounding the motor or gearbox shows signs of oil
leaks. This can be at the base, closest to the mating surface, or at the
furthest end of the motor at the resolver.
Consequences: besides the dirty appearance, in some cases there are no
serious consequences if the leaked amount of oil is very small. However, in
some cases the leaking oil lubricates the motor brake, causing the
manipulator to collapse at power down.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): leaking seal between gearbox and motor; gearbox overfilled
with oil; gearbox oil too hot.
Recommended actions. In order to remedy the symptom, the following actions
are recommended (the actions are listed in order of probability):
1. CAUTION: before approaching the potentially hot robot component, observe
the safety information in section CAUTION - Hot parts may cause burns.
2. Inspect all seals and gaskets between motor and gearbox. The different
manipulator models use different types of seals. Replace seals and gaskets as
specified in the product manual for the robot.
3. Check the gearbox oil level. Correct oil level is specified in the product
manual for the robot.
4. Too hot gearbox oil may be caused by: oil quality or level used is
incorrect; the robot work cycle runs a specific axis too hard (investigate
whether it is possible to program small "cooling periods" into the
application); overpressure created inside gearbox. Check the recommended oil
level and type as specified in the product manual for the robot.

## Page 49 - Mechanical noise

3 Troubleshooting by fault symptoms. 3.13 Mechanical noise.
Description: during operation, no mechanical noise should be emitted from
motors, gearboxes, bearings, or similar. A faulty bearing often emits
scraping, grinding, or clicking noises shortly before failing.
Consequences: failing bearings cause the path accuracy to become
inconsistent, and in severe cases, the joint can seize completely.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): worn bearings; contaminations have entered the bearing
races; loss of lubrication in bearings. If the noise is emitted from a
gearbox, the following can also apply: overheating.
Recommended actions. The following actions are recommended (listed in order
of probability):
1. CAUTION: before approaching the potentially hot robot component, observe
the safety information in section CAUTION - Hot parts may cause burns.
2. Determine which bearing is emitting the noise.
3. Make sure the bearing has sufficient lubrication. As specified in the
product manual for the robot.
4. If possible, disassemble the joint and measure the clearance. As specified
in the product manual for the robot.
5. Bearings inside motors are not to be replaced individually, but the
complete motor is replaced. Replace faulty motors as specified in the product
manual for the robot.
6. Make sure the bearings are fitted correctly.

## Page 50 - Mechanical noise (continued)

7. Too hot gearbox oil may be caused by: oil quality or level used is
incorrect; the robot work cycle runs a specific axis too hard (investigate
whether it is possible to program small "cooling periods" into the
application); overpressure created inside gearbox. Check the recommended oil
level and type as specified in the product manual for the robot.

## Page 51 - Manipulator crashes on power down

3 Troubleshooting by fault symptoms. 3.14 Manipulator crashes on power down.
Description: the manipulator is able to work correctly while Motors ON is
active, but when Motors OFF is active, it collapses under its own weight. The
holding brake, integral to each motor, is not able to hold the weight of the
manipulator arm.
Consequences: the fault can cause severe injuries or death to personnel
working in the area or severe damage to the manipulator and/or surrounding
equipment.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): faulty brake; faulty power supply to the brake.
Recommended actions:
1. Determine which motor(s) causes the robot to collapse.
2. Check the brake power supply to the collapsing motor during the Motors OFF
state. Also see the circuit diagrams in the product manuals for the robot and
the controller.
3. Remove the resolver of the motor to see if there are any signs of oil
leaks. If found faulty, the motor must be replaced as a complete unit as
detailed in the product manual for the robot.
4. Remove the motor from the gearbox to inspect it from the drive side. If
found faulty, the motor must be replaced as a complete unit as detailed in
the product manual for the robot.

## Page 52 - Problem releasing Robot brakes

3 Troubleshooting by fault symptoms. 3.15 Problem releasing Robot brakes.
Description: when starting robot operation or jogging the robot, the internal
robot brakes must release in order to allow movements.
Consequences: if the brakes do not release, no robot movement is possible,
and a number of error log messages can occur.
Possible causes. The symptom can be caused by (the causes are listed in order
of probability): brake contactor (K44) does not work correctly; the system
does not go to status Motors ON correctly; faulty brake on the robot axis;
supply voltage 24V BRAKE missing.

## Page 53 - Problem releasing Robot brakes (continued)

Recommended actions. This section details how to proceed when the robot
brakes do not release.
1. Make sure the brake contactor is activated. A 'tick' should be audible, or
you may measure the resistance across the auxiliary contacts on top of the
contactor.
2. Make sure the RUN contactors (K42 and K43) are activated. NOTE that both
contactors must be activated, not just one. A 'tick' should be audible, or
you may measure the resistance across the auxiliary contacts on top of the
contactor.
3. Use the push buttons on the robot to test the brakes. If just one of the
brakes malfunctions, the brake at hand is probably faulty and must be
replaced. If none of the brakes work, there is probably no 24V BRAKE power
available. The location of the push buttons differ, depending on robot model.
4. Check the Drive Module power supply to make sure 24V BRAKE voltage is OK.
5. A number of other faults within the system can cause the brakes to remain
activated. In such cases, event log messages will provide additional
information. The event log messages can also be accessed using RobotStudio.

## Page 57 - Trouble shooting fieldbuses and I/O units

4 Trouble shooting by Unit. 4.3 Trouble shooting fieldbuses and I/O units.
Where to find information: information about how to trouble shoot the
fieldbuses and I/O units can be found in the manual for the respective
fieldbus or I/O unit.
