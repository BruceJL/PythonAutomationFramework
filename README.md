# pyAutomation Framework
The pyAutomation framework provides a set of Python classes which allows you to quickly build an automation system similar to that offered by many PLC/PAC systems (e.g. Rockwell PACSystems, Siemens S7, Schneider Quantum, Emerson Rx3i, etc.) utilizing industry best practices for logic development and alarm management.

Additionally, using the pyAutomation system allows you many mature code management tools that are often cost adders, not offered, or ugly hacks on a number of the aforementioned platforms such as:
  - modern programming functionality (e.g. abstraction, polymorphism, etc.)
  - revision control (using Git, Mercurial, CVS, etc.)
  - Unit test functionality using the Python unittest module
  - The ability to test/execute logic on your development workstation without a dedicated control system.
  - Use of any commodity computing hardware at a platform.
  - Use the IDE of your choice.

Communications protocols currently supported are:
  - I2C (raspberry pi) with various devices:
    - Microchip MCP23017
    - TI ADS1015IDGSR
    - NXP MPL3115A2
    - AMS TMD3782 Color sensor.

Communications protocols planned are:
  - Modbus TCP client
  - Modbus TCP server
  - DNP3 TCP client
  - DNP3 TCP master
  - Emerson Rx3i EGD
  - OPC/UA client
  - IEC 61850 MMS
  - Profinet

## Getting Started.

### tldr; show me how to run the thing.
This framework comes with a sample project that consists of a simple system of 2 tanks, each with a lead and lag pump that drains the tanks. To start the framework, run the supervisor with the supplied logic.yaml and points.yaml files which will give the Supervisor the point database and logic to execute.
```sh
/pyAutomation/sample$ ../bin/Supervisor.py logic.yaml points.yaml
```
Now that the Supervisor is running, in another console, you can run the HMI to view the process values for the tanks.

```sh
/pyAutomation/sample$ ../bin/hmi.py hmi.yaml
```
While in the HMI console:
  - navigate using the up and down button,
  - enter to drill down on or edit an item
  - esc to navigate out of a menu item.
  - F11 to toggle forcing of a point.
  - F10 to toggle the quality of a point (only when forced.)
  - tab to switch between the point view and the active alarms view
  - 'a' to acknowledge a highlighted alarm (when on the alarm view).
  - 'q' to quit

In the sample project, you can edit the tank fill rate, and pump draw down rates without forcing the points, by doing this you can cause the lag pump to kick in (have the lead pump draw down rate less than the fill rate), and cause alarms to come in. The states of the pumps can be viewed and forced.

## Brass Tacks
The following sections outlines the functionality of the objects of the framework. They aim on taking care of the 80% of the standard logic and wrapping that up such that the size of any user defined logic routines are minimized.

### Alarms
Alarms are a integral component of any control system and defines conditions to which operator intervention is necessary to remedy an abnormal condition to prevent damage to the control system or product. Alarm objects have an integrated on delay, off delay and class information (used to drive notification type), as well as 'more info' and 'consequences' fields, which can be used to store alarm rationalization information.

#### Discrete Alarms
Discrete alarms are alarms driven from single conditions. They can be read by any logic routine and drive interrupts for those routines.

#### Analog Alarms
Analog alarms are alarms applied against Analog Points, they contain additional properties for hysteresis, the value the alarm is to activate at and a high/low flag.

### Points
Any project consists of a number of points which represent various inputs and outputs for the logic. The point object contains various information such as the time the point was last update, the quality of the point, the forced state of the point, update period, description, etc.

#### Discrete Points
Discrete points are two-state points. Typically used for contacts, level switches, floats, etc. They can be assigned custom on and off state descriptions to make HMI viewing easier.

#### Enumerated Points
Enumerated points are n-state points. Useful for representing state machines and other multi-input devices (e.g. Hand-Off-Auto switches).

#### Analog Points
Analog points are points that can represent a range of values.

#### Dual Analog Points
Dual Analogs Points are points composed of 2 other analog points. The average of the two points is used for the output. If the quality of any of the points drops out, the remaining point is used to populate the value. An alarm is created if the point values disagree beyond a threshold.

#### Process Values
Process values are points composed an Analog Point (or Dual Analog Point) and has a number of additional properties such as unit of measure, high and low display limits, associated control points, other related points and analog alarms. The analog alarms are updated any time the associated analog point for the process values is updated.

### Logic Routines
Logic routines are read the various input points and set output values to the points that they own. Ideally, the logic routines are small and numerous and limited to controlling a specific process such that a failing in one will be isolated from others. Logic routines can be instantiated multiple times with different points to re-use functionality.

### The Supervisor
The Supervisor first builds the point database form the points.yaml file, and then loads up the logic routines according to the logic.yaml file and associates points from the point database to required points for the logic routine. Each point can only be owned by a single logic routine instance (that logic routine instance becomes the 'producer' for that point). Any number of other logic routine instances may read the point or request different values for the point (which the owner instance is free to accept or ignore.)

The Supervisor then executes the logic routine instances based upon the following criteria:
   - The execution frequency defined in the routines 'period' property of the logic routine.
   - The 'update_period' of any points for which the routine is the owner of.
   - When an callback is received for the routine when another point or alarm the routine is interested in is updated.

### Loggers
Each process can have it output routed to a different log file. An unlimited number of loggers can be created.

### Alarm Notifiers
Alarm notifiers are used to route alarm events to various outputs such as databases, text logs, emails, etc. Currently only an E-mail handler is included.
