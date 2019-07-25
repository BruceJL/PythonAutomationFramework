"""
Created on Apr 16, 2016

@author: Bruce
"""

from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from .AbstractWindow import AbstractWindow
import curses
import pyAutomation.Hmi.Common


class PointEnumerationWindow(AbstractWindow):

    def __init__(self, point_enumeration: PointEnumeration) -> None:
        self.p = point_enumeration
        [height, width] = self.hmi_window_size()
        self.screen = pyAutomation.Hmi.Common.get_modal_window([height, width], self)
        self.selection = self.p.states.index(self.p.hmi_value)

    def hmi_window_size(self) -> (int, int):
        x = len(self.p.description)
        for s in self.p.states:
            if len(s) > x:
                x = len(s)
        x += 6

        y = len(self.p.states) * 2 + 6

        return y, x

    # Get the user input
    def hmi_get_user_input(self) -> None:
        prompt = True
        self.screen.keypad(True)

        while prompt:
            # get user input
            x = self.screen.getch()
            if self.p.hmi_writeable:
                if x == curses.KEY_DOWN:
                    self.selection += 1
                    if len(self.p.states) == self.selection:
                        self.selection = 0
                        pyAutomation.Hmi.Common.trigger_gui_update()

                elif x == curses.KEY_UP:
                    self.selection -= 1
                    if self.selection == -1:
                        self.selection = len(self.p.states) - 1
                        pyAutomation.Hmi.Common.trigger_gui_update()

                elif x == curses.KEY_ENTER or x == curses.KEY_SELECT or x == 10 or x == 13:
                    pyAutomation.Hmi.Common.write_to_point(self.p.name, self.p.states[self.selection])
                    prompt = False

            # escape key
            if x == 27:
                prompt = False

        self.screen.keypad(False)
        pyAutomation.Hmi.Common.del_modal_window(self)
        pyAutomation.Hmi.Common.trigger_gui_update()

    # Draw the window
    def hmi_draw_window(self) -> None:
        (y, x) = self.screen.getmaxyx()
        self.screen.border(0)

        i = round(x / 2 - len(self.p.description) / 2)
        j = 2

        self.screen.addstr(j, i, self.p.description, curses.A_BOLD)
        j += 2
        for s in self.p.states:
            if self.p.states[self.selection] == s and self.p.hmi_writeable:
                color = curses.color_pair(2)
            else:
                color = curses.color_pair(1)

            i = round(x / 2 - len(s) / 2)
            self.screen.addstr(j, i, s, color)
            j += 2
