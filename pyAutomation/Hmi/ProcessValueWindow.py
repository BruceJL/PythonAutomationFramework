"""
Created on Apr 16, 2016

@author: Bruce
"""

from pyAutomation.DataObjects.ProcessValue import ProcessValue
from .AbstractWindow import AbstractWindow
import curses
import logging
import pyAutomation.Hmi.Common


class ProcessValueWindow(AbstractWindow):

    def __init__(self, process_value: ProcessValue) -> None:
        self.logger = logging.getLogger('hmi')
        self.p = process_value
        self.index = 0
        self._highlighted_item = 0
        [height, self.description_width, self.data_width] = \
            self.hmi_window_size()
        width = self.description_width + self.data_width
        self.logger.debug("creating %s by %s modal window.", height, width)

        self.screen = \
            pyAutomation.Hmi.Common.get_modal_window([height, width], self)

        self.item_count = \
            1 + len(self.p.control_points) \
            + len(self.p.related_points) + len(self.p.alarms)

    # Determine the size of the window.
    def hmi_window_size(self) -> ['int', 'int', 'int']:
        # determine length of window

        desc_width = len("Value")
        data_width = self.p.data_display_width

        for key in self.p.control_points:
            j = len(self.p.control_points[key].description)
            if j > desc_width:
                desc_width = j

            j = self.p.control_points[key].data_display_width
            if j > data_width:
                data_width = j

        for key in self.p.related_points:
            j = len(self.p.related_points[key].description)
            if j > desc_width:
                desc_width = j

            self.logger.debug("checking point: %s", key)
            j = self.p.related_points[key].data_display_width
            if j > data_width:
                data_width = j

        for key in self.p.alarms:
            j = len(self.p.alarms[key].description)
            if desc_width < j:
                desc_width = j
            if 8 > data_width:
                data_width = 8

        x = desc_width + data_width
        point_desc_width = len(self.p.description)
        self.logger.debug(
          "point description length %s", point_desc_width)

        if x < point_desc_width:
            i = int(round(point_desc_width - x)/2)
            desc_width += i
            data_width += i

        desc_width += 3  # 1 window border line, 1 whitespace and 1 colon

        data_width += 3  # 1 whitespace after colon,
                         # 1 after the value, and 1 for the border

        self.logger.debug(
          "Description_width: %s data width: %s", desc_width, data_width)

        # Determine height of window
        y = 6

        j = len(self.p.control_points)
        if j > 0:
            y += j + 1

        j = len(self.p.related_points)
        if j > 0:
            y += j + 1

        j = len(self.p.alarms)
        if j > 0:
            y += j + 1
        y += 1
        return y, desc_width, data_width

    # Get the user input
    def hmi_get_user_input(self):
        prompt = True
        self.screen.keypad(True)

        control_points_keys = list(self.p.control_points.keys())
        related_points_keys = list(self.p.related_points.keys())
        alarms_keys = list(self.p.alarms.keys())

        while prompt:
            x = self.screen.getch()
            # Enter (10 or 13) pressed
            if x == curses.KEY_ENTER or x == curses.KEY_SELECT or x == 10 or x == 13:
                self.screen.keypad(False)

                if self._highlighted_item == 0:
                    p = self.p
                    if p.hmi_writeable:
                        pyAutomation.Hmi.Common.hmi_interact(p)

                elif self._highlighted_item <= len(control_points_keys):
                    p = self.p.control_points[control_points_keys[self._highlighted_item - 1]]
                    if p.hmi_writeable:
                        pyAutomation.Hmi.Common.hmi_interact(p)

                elif self._highlighted_item <= \
                  len(control_points_keys) + len(related_points_keys):
                    p = self.p.related_points[
                        related_points_keys[self._highlighted_item - len(control_points_keys) - 1]]
                    if p.hmi_writeable:
                        pyAutomation.Hmi.Common.hmi_interact(p)

                elif self._highlighted_item <= len(control_points_keys) + len(related_points_keys) + len(alarms_keys):
                    p = self.p.alarms[alarms_keys[self._highlighted_item - len(control_points_keys) - len(
                        related_points_keys) - 1]]
                    pyAutomation.Hmi.Common.hmi_interact(p)
                self.screen.keypad(True)

            # Escape (27) pressed
            elif x == 27:
                # try:
                prompt = False
                # except:
                #    pass

            elif x == curses.KEY_DOWN:
                self._highlighted_item += 1

                if self._highlighted_item > self.item_count - 1:
                    self._highlighted_item -= 1

                pyAutomation.Hmi.Common.trigger_gui_update()

            elif x == curses.KEY_UP:
                # logger.debug("KEY_UP pressed")
                self._highlighted_item -= 1

                if self._highlighted_item < 0:
                    self._highlighted_item = 0

                pyAutomation.Hmi.Common.trigger_gui_update()

        self.screen.keypad(False)
        pyAutomation.Hmi.Common.del_modal_window(self)
        pyAutomation.Hmi.Common.trigger_gui_update()

    # Draw the window
    def hmi_draw_window(self):
        (y, x) = self.screen.getmaxyx()
        index = 0

        # Grab the screen lock
        self.screen.border(0)

        # Draw the point description
        i = round(x / 2 - len(self.p.description) / 2)
        j = 2

        assert i > 0 and j > 0, \
            "curses x print coordinates are negative"

        self.screen.addstr(j, i, self.p.description, curses.A_BOLD)

        j += 2
        pyAutomation.Hmi.Common.draw_property(
          self.screen,
          j,
          self.description_width,
          self.data_width,
          "Value",
          index == self._highlighted_item,
          str(self.p.human_readable_value),
          pyAutomation.Hmi.Common.get_point_curses_color(self.p))

        j += 1
        index += 1
        if 0 < len(self.p.control_points):
            j += 1
            for key in self.p.control_points:
                cp = self.p.control_points[key]
                pyAutomation.Hmi.Common.draw_property(
                  self.screen,
                  j,
                  self.description_width,
                  self.data_width, cp.description,
                  index == self._highlighted_item,
                  cp.human_readable_value,
                  pyAutomation.Hmi.Common.get_point_curses_color(cp)
                )

                j += 1
                index += 1

        if 0 < len(self.p.related_points):
            j += 1
            for key in self.p.related_points:
                rp = self.p.related_points[key]
                pyAutomation.Hmi.Common.draw_property(
                  self.screen,
                  j,
                  self.description_width,
                  self.data_width,
                  rp.description,
                  index == self._highlighted_item,
                  rp.human_readable_value,
                  pyAutomation.Hmi.Common.get_point_curses_color(rp))
                j += 1
                index += 1

        if 0 < len(self.p.alarms):
            j += 1
            for key in self.p.alarms:
                a = self.p.alarms[key]
                pyAutomation.Hmi.Common.draw_property(
                  self.screen,
                  j,
                  self.description_width,
                  self.data_width,
                  a.description,
                  index == self._highlighted_item,
                  a.human_readable_value,
                  pyAutomation.Hmi.Common.get_alarm_curses_color(a))
                j += 1
                index += 1
