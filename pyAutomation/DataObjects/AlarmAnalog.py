import logging
from typing import Dict, Any
from .Alarm import Alarm

logger = logging.getLogger('controller')


class AlarmAnalog(Alarm):
    """
    Represents an analog alarm object, it extends an alarm object but instead
    take an analog value and compares it to a theshold to drive the alarm state.
    """

    keywords = Alarm.keywords + [
        "alarm_value",
        "hysteresis",
        "high_low_limit"]

    def __init__(self, **kwargs) -> None:
        """
        The constructor for AlarmAnalog class.

        Parameters:
          alarm_value (float): EU value that alarm is activated at.
          hysteresis (float: EU amount that value must leave alarm_value to
            lower the alarm.
          high_low_limit (str LOW/HIGH): flag to determine if the alarm is a
            HIGH or LOW limit.
          description (str): A human readable string  detailing the alarm
            condition.
          on_delay (float): The time in seconds that the alarm input must
            be active, before it is considered to be a valid alarm.
          off_delay (float): The time in seconds that the alarm must be
            inactive, before it is considered to be a reset alarm.
          consequences (str): The consequences of not responding to this
            alarm in a timely manner.
          more_info (str): Additional information helpful in rectifing the
            alarm condition (e.g. links to: drawings, manuals, or procedures)
        """
        self.alarm_value = 0.0
        self.hysteresis = 0.0
        self.high_low_limit = "HIGH"

        super().__init__(**kwargs)

    def __getstate__(self) -> 'Dict[str, Any]':
        """
        Gets a dict representation of the alarm suitable for JSON
        transport to an HMI client. This function is specified by the
        jsonpickle library to pickle an object.

        Returns:
            dict: a dict of alarm properties.

        """

        d = super().__getstate__()
        d.update(dict(
          alarm_value=self.alarm_value,
          hysteresis=self.hysteresis,
          high_low_limit=self.high_low_limit,
        ))
        return d

    def __setstate__(self, d) -> 'None':
        """
        Creates an alarm object from a dict representation. This function
        is specified by the jsonpickle library to unpickle an object.

        Parameters:
            dict: JSON dict of alarm properties.

        """
        super().__setstate__(d)
        self.alarm_value    = d['alarm_value']
        self.hysteresis     = d['hysteresis']
        self.high_low_limit = d['high_low_limit']

    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        """
        Gets a representation of this alarm suitable for storage in a yaml file.
        YAML files are used for storing the alarm when stopping and starting
        the process supervisor.
        """
        d = super().yaml_dict
        d.update(dict(
          alarm_value=self.alarm_value,
          hysteresis=self.hysteresis,
          high_low_limit=self.high_low_limit,
        ))
        return d

    @property
    def human_readable_value(self) -> str:
        return str(self.alarm_value)

    def evaluate_analog(self, value: 'float') -> None:
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

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!AlarmAnalog',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)

        return AlarmAnalog(**value)
