#!/usr/bin/python3

import curses
import logging
import threading

from pyAutomation.Hmi.AlarmWindow import AlarmWindow
from pyAutomation.Hmi.AlarmAnalogWindow import AlarmAnalogWindow
from pyAutomation.Hmi.ProcessValueWindow import ProcessValueWindow
from pyAutomation.Hmi.PointEnumerationWindow import PointEnumerationWindow
from pyAutomation.Hmi.PointAnalogWindow import PointAnalogWindow
from pyAutomation.Hmi.PointDiscreteWindow import PointDiscreteWindow

# setup the logger
logger = logging.getLogger('hmi')
logger.propagate = False
logger.setLevel(logging.DEBUG)
logger.handlers = []

fh = logging.FileHandler('./logs/hmi.log')

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

gui_loop_condition = threading.Condition()
screen = None
modal_windows = []
logic_server_conn = None


def hmi_interact(o) -> None:
    if o.hmi_object_name == "AlarmWindow":
        win = AlarmWindow(o)
        win.hmi_get_user_input()
    elif o.hmi_object_name == "AlarmAnalogWindow":
        win = AlarmAnalogWindow(o)
        win.hmi_get_user_input()
    elif o.hmi_object_name == "ProcessValueWindow":
        win = ProcessValueWindow(o)
        win.hmi_get_user_input()
    elif o.hmi_object_name == "PointAnalogWindow":
        win = PointAnalogWindow(o)
        win.hmi_get_user_input()
    elif o.hmi_object_name == "PointDiscreteWindow":
        win = PointDiscreteWindow(o)
        win.hmi_get_user_input()
    elif o.hmi_object_name == "PointEnumerationWindow":
        win = PointEnumerationWindow(o)
        win.hmi_get_user_input()
        logger.debug("Leaving function")


# Update a dict with new properties
def update_dict(local: dict, remote: dict, path: str) -> None:
    for key, value in remote.items():
        if isinstance(value, dict) and isinstance(local[key], dict):
            path = path + " > dict-" + local['name']
            update_dict(local[key], value, path)
        elif hasattr(value, '__dict__') and hasattr(local[key], '__dict__'):
            path = path + ">" + value.name
            update_object(local[key], value, path)
        elif not local[key] == value:
            path = path + ">" + local['name']
            # logger.debug(path  + " Updated " + "[" + key + "] from "
            #     + str(local[key]) + " to " + str(value))
            local[key] = value


# Updates an object with new properties from the point database
def update_object(local, remote, path: str) -> None:
    for key, value in remote.__dict__.items():
        # logger.debug("Working on " + str(key) + "-" + str(value))
        local_item = getattr(local, key)
        if isinstance(value, dict) and isinstance(local_item, dict):
            path = path + " > dict-" + str(key)
            update_dict(local_item, value, path)
        elif hasattr(value, '__dict__') and hasattr(local_item, '__dict__'):
            path = path + ">" + value.name
            update_object(local_item, value, path)
        elif not local_item == value:
            path = path + ">" + local.name
            # logger.debug(path  + " Updated " + "[" + key + "] from "
            #    + str(local_item) + " to " + str(value))
            setattr(local, key, value)


# Draws a representation of a point on the screen with all the appropriate
# coloring.
def draw_property(
  s,
  y: int,
  description_width: int,
  data_width: int,
  description: str,
  highlighted: bool,
  value: str,
  value_color) -> None:
    if highlighted:
        color = curses.color_pair(3)
    else:
        color = curses.color_pair(1)

    # -1 to make room for the colon
    k = description_width - len(description) - 1
    # Draw the description after the border and a whitespace
    s.addstr(y, 1, " " * (description_width + data_width - 2))
    s.addstr(y, k, description + ":", color)

    k = description_width
    k += data_width - len(str(value)) - 2
    s.addstr(y, k, str(value), value_color)


# Get the highlighting color for a point
def get_point_curses_color(point) -> object:
    if not point.quality and not point.forced:
        return curses.color_pair(4)
    elif not point.quality and point.forced:
        return curses.color_pair(7)
    elif point.quality and point.forced:
        return curses.color_pair(6)
    else:
        return curses.color_pair(1)


# Get the highlighting color for an alarm
def get_alarm_curses_color(alarm) -> object:
    i = alarm.alarm_state

    if i == "NORMAL":
        # "ALARM NORMAL"
        return curses.color_pair(1)
    elif i == "ACTIVE":
        # "ALARM ACTIVE"
        return curses.color_pair(2)
    elif i == "ACKNOWLEDGED":
        # "ALARM ACKNOWLEDGED"
        return curses.color_pair(8)
    elif i == "RESET":
        # "ALARM RESET"
        return curses.color_pair(9)
    elif i == "BLOCKED":
        # "ALARM BLOCKED"
        return curses.color_pair(10)
    else:
        return curses.color_pair(1)


# wrapper to issue a point update on the control server.
def write_hmi_point(point, value) -> None:
    logic_server_conn.root.exposed_write_hmi_point(point, value)


# Rpyc calls here
def write_to_point(name: str, value: str) -> None:
    logger.info("writing %s to %s", value, name)
    try:
        logic_server_conn.root.exposed_set_hmi_value(name, value)
    except Exception as e:
        logger.error("write failed with exception:\n %s", e)

def acknowledge_alarm(name: str) -> None:
    logger.info("acknowledging: %s", name)
    logic_server_conn.root.exposed_acknowledge_alarm(name)


def toggle_point_quality(name: str) -> None:
    logger.info("toggling quality: %s", name)
    logic_server_conn.root.exposed_toggle_point_quality(name)


def toggle_point_force(name: str) -> None:
    logger.info("toggling force: %s", name)
    logic_server_conn.root.exposed_toggle_point_force(name)


def get_modal_window(size: [int, int], window_object):
    (height, width) = size
    (y, x) = screen.getmaxyx()
    begin_x = round(x / 2 - width / 2)
    begin_y = round(y / 2 - height / 2)

    win = curses.newwin(height, width, begin_y, begin_x)
    modal_windows.append(window_object)
    return win


def del_modal_window(win) -> None:
    with gui_loop_condition:
        modal_windows.remove(win)
        del win
        trigger_gui_update()


def trigger_gui_update() -> None:
    with gui_loop_condition:
        gui_loop_condition.notify()
