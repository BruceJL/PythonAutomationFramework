#!/usr/bin/python3

import sys
import curses
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import traceback
import threading
import collections
import jsonpickle
import json
import rpyc
from ruamel import yaml
from typing import List, Dict

import pyAutomation.Hmi.Common
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

fh = RotatingFileHandler(
    './logs/hmi.log',
    maxBytes=2048000,
    backupCount=1)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


class CursesHmi(object):

    def load_page_points(self, i: int):
        self.points = {}
        logic_server_conn.root.clear_monitored_points()
        logic_server_conn.root.add_monitored_points(self.pages[i]['points'])

    def __init__(self, config):
        self.quit = False           # type: 'bool'
        self.mode = "POINTS"        # type: 'str'
        self.highlighted_point = 0  # type: 'int'
        self.current_page = -1      # type 'int'
        self.pages = []             # type: 'List[Dict]'
        self.failed = False         # type: 'bool'

        # open the supplied yaml file.
        with open(config, 'r') as ymlfile:
            cfg = yaml.safe_load(ymlfile)

        for page in cfg:
            points = cfg[page]['points']
            self.pages.append({
              'title': page,
              'points' : points,
            })

        assert len(self.pages) > 0, \
            "No page data found. No configuration file specified?"

        self.load_page_points(0)

        self.data_access_condition = threading.Condition()
        self.user_input_condition = threading.Condition()
        self.get_network_data_condition = threading.Condition()

        self.gui_loop_thread = threading.Thread(target=self.gui_loop)
        self.user_input_thread = threading.Thread(target=self.get_user_input)
        self.get_network_data_thread = \
            threading.Thread(target=self.get_network_data)
        self.points = collections.OrderedDict()
        self.alarms = collections.OrderedDict()
        self.threads = []
        self.last_read_time = datetime.datetime.now()
        self.alarms_need_refresh = False
        pyAutomation.Hmi.Common.gui_loop_condition = self.data_access_condition

        # setup ncurses
        os.environ.setdefault('ESCDELAY', '25')

    def hmi_interact(self, o) -> None:
        logger.debug("Entering Function for " + o.name)
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

    def get_point_name(self, p):
        logger.debug("looking for point " + str(p))
        for k, v in self.points.items():
            logger.debug(k + " (" + str(v) + ") isn't it.")
            if v == p:
                return k
        assert False, \
            "Point: " + p.description + " not found in local database."

    # Get the data from the point database server.
    def get_network_data(self):
        logger.info("Starting!")
        try:
            self.get_network_data_condition.acquire()
            while not self.quit:

                points_json_data = \
                    logic_server_conn.root.exposed_get_hmi_points_list()
                alarms_json_data = \
                    logic_server_conn.root.exposed_get_active_alarm_list()
                threads_json_data = \
                    logic_server_conn.root.exposed_get_thread_list()

                json_points = jsonpickle.decode(points_json_data)
                json_alarms = jsonpickle.decode(alarms_json_data)
                self.threads = jsonpickle.decode(threads_json_data)

                with self.data_access_condition:
                    if json_points is not None:
                        for k, point in json_points.items():
                            if k in self.points:
                                # point already exists, only update the
                                # received values.
                                pyAutomation.Hmi.Common.update_object(
                                  self.points[k], point, k)
                            else:
                                # point doesn't exist, make a new entry
                                self.points[k] = point
                                logger.info("Registering point: " + k)
                    else:
                        logger.info("Received empty points list from server")

                    # dump the alarm data
                    self.alarms.clear()
                    self.alarms_need_refresh = False
                    if json_alarms is not None:
                        for a in json_alarms:
                            self.alarms[a.name] = a

                    if self.mode == "ALARMS":
                        while self.highlighted_point > len(self.alarms) - 1:
                            self.highlighted_point -= 1

            # Something didn't work so output the last recieved network data
            if self.failed:
                j = json.loads(points_json_data)
                logger.info("point data: %s",
                            json.dumps(j, indent=4, sort_keys=True))
                j = json.loads(threads_json_data)
                logger.info("thread data: %s ",
                            json.dumps(j, indent=4, sort_keys=True))
                self.exit()

                self.get_network_data_condition.wait(0.5)
        except Exception:
            logger.error(traceback.format_exc())
            self.exit()
        finally:
            self.get_network_data_condition.release()
            logger.info("Stopping!")

    def exit(self) -> None:
        logger.debug("Entering function.")
        self.quit = True

        with self.data_access_condition:
            self.data_access_condition.notify()

        logger.debug("Leaving function.")

    def start_gui(self, screen) -> None:
        logger.info("*****************Starting Curses HMI******************.")
        pyAutomation.Hmi.Common.screen = screen
        self.get_network_data_thread.start()
        self.gui_loop_thread.start()
        self.get_user_input()

    def gui_loop(self) -> None:
        logger.info("Starting")

        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)     # normal color
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)       # Alarm Active color
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)      # highlighted point color
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_MAGENTA)   # bad quality color
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)     # User entry color.
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_YELLOW)    # Forced point color.
        curses.init_pair(7, curses.COLOR_MAGENTA, curses.COLOR_YELLOW)  # Forced bad quality point color.
        curses.init_pair(8, curses.COLOR_RED, curses.COLOR_BLACK)       # alarm acknowledged color.
        curses.init_pair(9, curses.COLOR_GREEN, curses.COLOR_BLACK)     # alarm reset color.
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW)   # alarm blocked color.

        try:
            pyAutomation.Hmi.Common.screen.clear()
            pyAutomation.Hmi.Common.screen.border(0)
            while not self.quit:

                try:
                    self.draw_gui()
                except Exception:
                    logger.error(traceback.format_exc())
                    pyAutomation.Hmi.Common.screen.clear()
                    self.failed = True

                finally:
                    with self.data_access_condition:
                        self.data_access_condition.wait(0.5)

        except Exception:
            logger.error(traceback.format_exc())
            self.exit()
        finally:
            logger.info("Stopping!")

    def draw_gui(self):
        with self.data_access_condition:
            # determine the longest description
            (y, x) = pyAutomation.Hmi.Common.screen.getmaxyx()

            pyAutomation.Hmi.Common.screen.addstr(
              1,
              2,
              str(datetime.datetime.now()))

            right_justify = 0
            for point in self.points.values():
                j = len(point.description)
                if j > right_justify:
                    right_justify = j
            right_justify += 2

            line = 3
            i = 0
            for point in self.points.values():
                # clear the line, write x-2 blank spaces to the line
                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  1,
                  " " * (x - 2),
                  curses.color_pair(1))

                if i == self.highlighted_point and self.mode == "POINTS":
                    color = curses.color_pair(3)
                else:
                    color = curses.color_pair(1)
                j = right_justify - len(point.description)

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  j,
                  point.description + ":",
                  color)

                j = right_justify + 2

                color = pyAutomation.Hmi.Common.get_point_curses_color(point)

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  j,
                  point.human_readable_value,
                  color)
                pyAutomation.Hmi.Common.screen.addstr(
                  " " * (10 - len(point.human_readable_value)))

                line += 1
                i += 1

            # Render the threads
            line += 3

            # calculate the column widths
            columns = [3, 0, 0, 0, 0, 0]
            for thread in self.threads:
                logger.debug("thread data: %s", str(thread))
                size = len(thread['name'])
                if size > columns[1]:
                    columns[1] = size

                size = len("{:.5f}".format(thread['sweep_time']))
                if size > columns[2]:
                    columns[2] = size

                if thread['sleep_time'] is not None:
                    size = len("{:.5f}".format(thread['sleep_time']))
                else:
                    size = 4
                if size > columns[3]:
                    columns[3] = size

                size = len(str(thread['last_run_time']))
                if size > columns[4]:
                    columns[4] = size

                size = len(str(thread['terminated']))
                if size > columns[5]:
                    columns[5] = size

            columns[1] += columns[0] + 3
            columns[2] += columns[1] + 3
            columns[3] += columns[2] + 3
            columns[4] += columns[3] + 3
            columns[5] += columns[4] + 3

            color = curses.color_pair(1)

            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[0],
              " " * (columns[5]),
              curses.color_pair(1))
            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[0],
              "Name",
              color)
            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[1],
              "Sweep",
              color)
            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[2],
              "Sleep",
              color)
            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[3],
              "last run time",
              color)
            pyAutomation.Hmi.Common.screen.addstr(
              line,
              columns[4],
              "Died",
              color)
            line += 1

            for thread in self.threads:
                # Clear the line
                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  columns[0],
                  " " * (columns[4]),
                  curses.color_pair(1))

                # Render the line
                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  columns[0],
                  thread['name'],
                  color)

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  columns[1],
                  "{:.5f}".format(thread['sweep_time']),
                  color)

                if thread['sleep_time'] is not None:
                    pyAutomation.Hmi.Common.screen.addstr(
                      line,
                      columns[2],
                      "{:.5f}".format(thread['sleep_time']),
                      color)
                else:
                    pyAutomation.Hmi.Common.screen.addstr(
                      line,
                      columns[2],
                      "None",
                      color)

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  columns[3],
                  str(thread['last_run_time']),
                  color)

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  columns[4],
                  str(thread['terminated']),
                  color)
                line += 1

            # Render the alarms.
            line += 1
            j = 6  # indent

            # Clear out the bottom of the screen.
            for k in range(line, y - 1):
                pyAutomation.Hmi.Common.screen.addstr(k, 2, " " * x)

            i = 0
            for alarm in self.alarms.values():
                if self.highlighted_point == i and self.mode == "ALARMS":
                    pyAutomation.Hmi.Common.screen.addstr(line, j - 2, ">")

                pyAutomation.Hmi.Common.screen.addstr(
                  line,
                  j,
                  alarm.status_string,
                  pyAutomation.Hmi.Common.get_alarm_curses_color(alarm))
                line += 1
                i += 1

            # cause the screen to re render
            pyAutomation.Hmi.Common.screen.touchwin()
            pyAutomation.Hmi.Common.screen.refresh()

            # Render any subwindows.
            for win in pyAutomation.Hmi.Common.modal_windows:
                win.hmi_draw_window()
                win.screen.touchwin()
                win.screen.refresh()

    def get_user_input(self):
        logger.info("Starting!")
        try:
            while not self.quit:
                c = pyAutomation.Hmi.Common.screen.getch()
                if c == ord('q'):
                    self.exit()
                    break

                elif c == ord('r'):
                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif c == curses.KEY_RESIZE:
                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif c == ord('\t'):
                    with self.data_access_condition:
                        if self.mode == "POINTS":
                            self.mode = "ALARMS"
                        elif self.mode == "ALARMS":
                            self.mode = "POINTS"
                        else:
                            pass
                        self.highlighted_point = 0
                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif c == curses.KEY_DOWN:
                    with self.data_access_condition:
                        self.highlighted_point += 1
                        last_item = None
                        with self.data_access_condition:
                            if self.mode == "ALARMS":
                                last_item = len(self.alarms)
                            elif self.mode == "POINTS":
                                last_item = len(self.points)

                        if self.highlighted_point > last_item - 1:
                            self.highlighted_point -= 1

                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif c == curses.KEY_UP:
                    with self.data_access_condition:
                        self.highlighted_point -= 1

                        if self.highlighted_point < 0:
                            self.highlighted_point = 0

                elif self.mode == "POINTS":
                    keys = list(self.points.keys())

                    if len(self.points) > 0:
                        if c == 10 or c == 13:
                            p = self.points[keys[self.highlighted_point]]
                            logger.debug("Enter pressed on: " + p.name)
                            pyAutomation.Hmi.Common.screen.keypad(False)
                            self.hmi_interact(p)
                            pyAutomation.Hmi.Common.screen.keypad(True)

                        elif c == curses.KEY_F11:  # Toggle force
                            pyAutomation.Hmi.Common.toggle_point_force(
                              keys[self.highlighted_point])

                        elif c == curses.KEY_F10:  # Toggle quality if forced
                            if self.points[keys[self.highlighted_point]].forced:
                                pyAutomation.Hmi.Common.toggle_point_quality(
                                  keys[self.highlighted_point])
                        else:
                            pass

                elif self.mode == "ALARMS":
                    if len(self.alarms.values()) > 0:
                        with self.data_access_condition:
                            alarms = list(self.alarms.values())

                        if c == ord('a') and not self.alarms_need_refresh:
                            pyAutomation.Hmi.Common.acknowledge_alarm(
                              alarms[self.highlighted_point].name)
                            with self.data_access_condition:
                                self.alarms_need_refresh = True
                            pyAutomation.Hmi.Common.trigger_gui_update()
                        elif c == ord('b'):
                            alarms[self.highlighted_point].blocked = \
                                not alarms[self.highlighted_point].blocked
                        elif c in (10, 13):
                            self.hmi_interact(alarms[self.highlighted_point])
                        else:
                            pass

        except Exception:
            logger.error(traceback.format_exc())
            self.failed = True
            self.exit()
        finally:
            logger.info("Stopping!")


if __name__ == "__main__":
    logic_server_conn = rpyc.connect("localhost", 18861, config={"allow_all_attrs": True})
    pyAutomation.Hmi.Common.logic_server_conn = logic_server_conn
    cursesHmi = CursesHmi(config=sys.argv[1])
    curses.wrapper(cursesHmi.start_gui)
