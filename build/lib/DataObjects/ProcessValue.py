"""
Created on Apr 16, 2016

@author: Bruce
"""
import logging
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from typing import Dict, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .PointAbstract import PointAbstract
    from .AlarmAnalog import AlarmAnalog

logger = logging.getLogger('controller')


class ProcessValue(PointAnalogReadOnlyAbstract):

    # this is the callback passed to the pointAnalog that this ProcessValue wraps
    def point_updated(self, name: str):
        logger.debug("called for " + self.point.description + " from " + name)
        for key in self.alarms:
            self.alarms[key].evaluate_analog(self.point.value)

    def __init__(self, point_analog: PointAnalogReadOnlyAbstract) -> None:
        super().__init__()
        self.point = point_analog

        point_analog.add_observer(self.name, self.point_updated)

        self.control_points = {}  # type: Dict[str, PointAbstract]

        self.alarms = {}  # type: Dict[str, AlarmAnalog]

        self.related_points = {}  # type: Dict[str, PointAbstract]

        self.high_display_limit = 0.0
        self.low_display_limit = 0.0

    # The dict property is what is used by jsonpickle to transpor the object over the network.
    def _get__dict__(self) -> 'Dict[str, Any]':
        d = dict(point=self.point,
                 high_display_limit=self.high_display_limit,
                 low_display_limit=self.low_display_limit,
                 control_points=self.control_points,
                 alarms=self.alarms,
                 related_points=self.related_points)

        return d

    __dict__ = property(_get__dict__)

    # methods to add alarms and points.
    def add_alarm(self, name, alarm_analog):
        self.alarms[name] = alarm_analog
        # self.alarms_list.append(alarm_analog)

    def add_control_point(self, name, point):
        self.control_points[name] = point
        # self.control_points_list.append(point)

    def add_related_point(self, name, point):
        self.related_points[name] = point
        # self.related_points_list.append(point)

    # #########################################################3
    # Below are properties proxied from the wrapped PointAnalog.

    # point name
    def _get_name(self) -> str:
        return self.point.name

    # def _set_name(self, value):
    #    # The point name is stored in the point, but we need a method here so this object can be reconstructed
    #    # from a JSONPICKLE remotely.
    #    pass

    name = property(_get_name)

    # Point EU value
    def _get_value(self):
        return self.point.value

    # def _set_value(self, value):
    #    self.point.value = value

    value = property(_get_value)

    # point HMI value
    def _get_hmi_value(self):
        return self.point.hmi_value

    def _set_hmi_value(self, v):
        self.point.hmi_value = v

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # Point quaity
    def _get_quality(self) -> bool:
        return self.point.quality

    # def _set_quality(self, quality: bool):
    #    self.point.quality = quality

    quality = property(_get_quality)

    # Point forced
    def _get_forced(self) -> bool:
        return self.point.forced

    # def _set_forced(self, forced: bool):
    #     self.point.forced = forced

    forced = property(_get_forced)

    # Description
    def _get_description(self) -> str:
        return self.point.description

    description = property(_get_description)

    # human readable value
    @property
    def human_readable_value(self) -> str:
        return self.point.human_readable_value

    # last update property
    def _get_last_update(self):
        return self.point.last_update

    last_update = property(_get_last_update)

    # HMI writable
    @property
    def hmi_writeable(self):
        return self.point.hmi_writeable

    # data display width
    @property
    def data_display_width(self) -> int:
        return self.point.data_display_width

    # point observers
    def _get_observers(self):
        return self.point.observers

    observers = property(_get_observers)

    @property
    def hmi_object_name(self) -> str:
        return "ProcessValueWindow"

    # writer
    def _get_writer(self) -> object:
        return self.point.writer

    # def _set_writer(self, w: object):
    #     self.point.writer = w

    writer = property(_get_writer)

    # unit of measure
    def _get_u_of_m(self) -> str:
        return self.point.u_of_m

    # def _set_u_of_m(self, s: str):
    #     self.point.u_of_m = s

    u_of_m = property(_get_u_of_m)

