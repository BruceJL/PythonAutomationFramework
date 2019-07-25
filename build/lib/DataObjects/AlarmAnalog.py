import logging
from .Alarm import Alarm
from typing import Dict, Any

logger = logging.getLogger('controller')


class AlarmAnalog(Alarm):
    keywords = Alarm.keywords + [
        "alarm_value",
        "hysteresis",
        "high_low_limit"]

    def __init__(self, **kwargs) -> None:
        """
        @keyword description: alarm description
        @keyword on_delay: delay before alarm is raised
        @keyword off_delay: delay before alarm is lowered
        @keyword alarm_value: EU value that alarm is activated at
        @keyword hysteresis: EU amount that value must leave alarm_value to lower alarm
        @keyword high_low_limit: flag to determine if the alarm is a HIGH or LOW limit
        """

        self.alarm_value = 0.0
        self.hysteresis = 0.0
        self.high_low_limit = "HIGH"
        super().__init__(**kwargs)

    def _get__dict__(self) -> 'Dict[str, Any]':
        d = super().__dict__
        d.update(dict(
            alarm_value=self.alarm_value,
            hysteresis=self.hysteresis,
            high_low_limit=self.high_low_limit))
        return d

    __dict__ = property(_get__dict__)

    @property
    def human_readable_value(self) -> str:
        return str(self.alarm_value)

    def evaluate_analog(self, value):
        if self.high_low_limit == "HIGH":
            if not self.input:
                if value > self.alarm_value:
                    self.input = True
            else:
                if value < self.alarm_value - self.hysteresis:
                    self.input = False

        elif self.high_low_limit == "LOW":
            if not self.input:
                if value < self.alarm_value:
                    self.input = True
            else:
                if value > self.alarm_value + self.hysteresis:
                    self.input = False

    @property
    def data_display_width(self):
        return 8

    @property
    def hmi_object_name(self) -> str:
        return "AlarmAnalogWindow"
