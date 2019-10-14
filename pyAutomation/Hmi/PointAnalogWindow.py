"""
Created on Apr 16, 2016

@author: Bruce
"""

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from .AbstractWindow import AbstractWindow
import curses
import pyAutomation.Hmi.Common


class PointAnalogWindow(AbstractWindow):

    def __init__(self, point_analog: PointAnalog) -> None:
        self.p = point_analog
        [height, width] = self.hmi_window_size()
        self.screen = pyAutomation.Hmi.Common.get_modal_window(
          [height, width], self)
        self.selection = str(self.p.editable_value)

    def hmi_window_size(self) -> [int, int]:
        i = len(self.p.description)
        if 15 > i:
            i = 15
        y = 10
        x = i + 10
        return y, x

    # Get the user input
    def hmi_get_user_input(self) -> None:
        prompt = True
        self.screen.keypad(True)

        while prompt:
            x = self.screen.getch()
            if self.p.hmi_writeable:
                if ord('0') <= x <= ord('9') and len(self.selection) < 10:
                    self.selection += chr(x)
                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif ord(".") == x and len(self.selection) < 10:
                    if "." not in self.selection:
                        self.selection += "."
                    pyAutomation.Hmi.Common.trigger_gui_update()

                elif x == curses.KEY_BACKSPACE:
                    self.selection = self.selection[:-1]
                    pyAutomation.Hmi.Common.trigger_gui_update()

                # Enter key pressed
                elif x == curses.KEY_ENTER or x == 10 or x == 13:
                    pyAutomation.Hmi.Common.write_to_point(
                      self.p.name, str(self.selection))
                    prompt = False

            if x == curses.KEY_F11:
                pyAutomation.Hmi.Common.toggle_point_force(self.p.name)

            # escape key pressed
            if x == 27:
                prompt = False

        self.screen.keypad(False)
        pyAutomation.Hmi.Common.del_modal_window(self)

    # Draw the window
    def hmi_draw_window(self) -> None:
        (y, x) = self.screen.getmaxyx()
        self.screen.border(0)

        i = round(x / 2 - len(self.p.description) / 2)
        j = 2
        self.screen.addstr(j, i, self.p.description, curses.A_BOLD)

        if self.p.hmi_writeable:
            color = curses.color_pair(5)
        else:
            color = curses.color_pair(0)

        i = 4
        j = 5
        k = x - 8 - len(self.selection)

        self.screen.addstr(j, i, " " * k, color)
        i += k
        self.screen.addstr(j, i, self.selection, color)
