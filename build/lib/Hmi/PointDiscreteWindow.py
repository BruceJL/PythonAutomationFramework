"""
Created on Apr 16, 2016

@author: Bruce
"""

import curses
from DataObjects.PointDiscrete import PointDiscrete
from .AbstractWindow import AbstractWindow
import Hmi.Common


class PointDiscreteWindow(AbstractWindow):
    def __init__(self, point_discrete: PointDiscrete) -> None:
        self.p = point_discrete
        [height, width] = self.hmi_window_size()
        self.screen = Hmi.Common.get_modal_window([height, width], self)
        self.selection = point_discrete.value

    def hmi_window_size(self) -> [int, int]:
        i = len(self.p.description)
        if len(self.p.off_state_description) > i:
            i = len(self.p.off_state_description)
        if len(self.p.on_state_description) > i:
            i = self.p.off_state_description

        y = 10
        x = i + 10
        return y, x

    # Get the user input
    def hmi_get_user_input(self) -> None:
        prompt = True
        self.screen.keypad(True)

        while prompt:
            x = self.screen.getch()

            if self.p.hmi_editable:
                if x == curses.KEY_LEFT or x == curses.KEY_RIGHT or x == curses.KEY_UP or x == curses.KEY_DOWN:
                    self.selection = not self.selection
                    Hmi.Common.trigger_gui_update()

                elif x == curses.KEY_ENTER or x == curses.KEY_SELECT or x == 10 or x == 13:
                    Hmi.Common.write_to_point(self.p.name, str(self.selection))
                    prompt = False

            elif x == curses.KEY_F11:
                Hmi.Common.toggle_point_force(self.p.name)
                Hmi.Common.trigger_gui_update()

            # escape key
            if x == 27:
                prompt = False

        self.screen.keypad(False)
        Hmi.Common.del_modal_window(self)
        Hmi.Common.trigger_gui_update()

    # Draw the window
    def hmi_draw_window(self) -> None:
        (y, x) = self.screen.getmaxyx()

        # Start drawin'
        self.screen.border(0)

        # Draw the point title
        if self.p.forced:
            # point is forced, color it the forced colour.
            color = curses.color_pair(6)
        else:
            color = curses.A_BOLD

        i = round(x / 2 - len(self.p.description) / 2)
        j = 2
        self.screen.addstr(j, i, self.p.description, color)

        if not self.p.hmi_editable:
            color = curses.color_pair(0)
        elif self.selection:
            color = curses.color_pair(1)
        else:
            color = curses.color_pair(2)

        i = round(x / 2 - len(self.p.off_state_description) / 2)
        j = 5
        self.screen.addstr(j, i, self.p.off_state_description, color)

        if not self.p.hmi_editable:
            color = curses.color_pair(0)
        elif not self.selection:
            color = curses.color_pair(1)
        else:
            color = curses.color_pair(2)

        i = round(x / 2 - len(self.p.on_state_description) / 2)
        j = 7
        self.screen.addstr(j, i, self.p.on_state_description, color)
