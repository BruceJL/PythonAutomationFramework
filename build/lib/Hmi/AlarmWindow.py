"""
Created on Apr 16, 2016

@author: Bruce
"""

from DataObjects.Alarm import Alarm
import logging
import curses
import Hmi.Common
from .AbstractWindow import AbstractWindow

logger = logging.getLogger('hmi')


class AlarmWindow(AbstractWindow):

    def __init__(self, alarm: Alarm) -> None:
        self.p = alarm
        [height, self.description_width, self.data_width] = self.hmi_window_size()
        width = self.description_width + self.data_width
        self.screen = Hmi.Common.get_modal_window([height, width], self)
        self._highlighted_item = 0

    def hmi_window_size(self) -> [int, int, int]:
        description_width = len("Acknowledged")
        description_width += 3
        data_width = len("False")
        data_width += 3

        logger.debug("Description_width: " + str(description_width) + " data_width: " + str(data_width))

        i = len(self.p.description)
        i += 6
        if (description_width + data_width) < i:
            i = int(round(i - description_width - data_width)/2)
            description_width += i
            data_width += i

        if len(self.p.description)+6 > description_width + data_width:
            raise Exception(
              "The description/data width math didn't work out. Got description: " + str(description_width)
              + " and data_width: " + str(data_width) + " Need to add up to at least: "
              + str(len(self.p.description)))

        y = 13
        return y, description_width, data_width

    # Get the user input
    def hmi_get_user_input(self) -> None:
        prompt = True
        self.screen.keypad(True)

        while prompt:
            # get user input
            x = self.screen.getch()

            # Enter (10 or 13) pressed
            if x == curses.KEY_ENTER or x == curses.KEY_SELECT or x == 10 or x == 13:
                pass

            # Escape (27) pressed
            elif x == 27:
                # try:
                prompt = False
                self.screen.refresh()
                # except:
                #    pass

            elif x == curses.KEY_DOWN:
                self._highlighted_item += 1

                if self._highlighted_item > 6:
                    self._highlighted_item -= 1

                self.hmi_draw_window()

            elif x == curses.KEY_UP:
                # logger.debug("KEY_UP pressed")
                self._highlighted_item -= 1

                if self._highlighted_item < 0:
                    self._highlighted_item = 0

                self.hmi_draw_window()

        self.screen.keypad(False)
        Hmi.Common.del_modal_window(self)

    # Draw the window
    def hmi_draw_window(self) -> None:
        (y, x) = self.screen.getmaxyx()
        # Grab the screen lock
        Hmi.Common.gui_loop_condition.acquire()
        self.screen.border(0)

        # Draw the point description
        i = round(x / 2 - len(self.p.description) / 2)
        j = 2
        self.screen.addstr(j, i, self.p.description, curses.A_BOLD)

        j += 2
        k = 0
        Hmi.Common.draw_property(
            self.screen, 
            j, 
            self.description_width,
            self.data_width, "STATE",
            k == self._highlighted_item,
            self.p.state,
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width, "Timer",
            k == self._highlighted_item,
            str(self.p.wake_time),
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width, "Blocked",
            k == self._highlighted_item,
            str(self.p.blocked),
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width,
            "Input",
            k == self._highlighted_item,
            str(self.p.input),
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width,
            "Output",
            k == self._highlighted_item,
            str(self.p.active),
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width,
            "Acknowledged",
            k == self._highlighted_item,
            str(self.p.acknowledged),
            curses.color_pair(0))
        j += 1
        k += 1
        Hmi.Common.draw_property(
            self.screen,
            j,
            self.description_width,
            self.data_width,
            "Reset",
            k == self._highlighted_item,
            str(not self.p.active),
            curses.color_pair(0))

        Hmi.Common.gui_loop_condition.release()

