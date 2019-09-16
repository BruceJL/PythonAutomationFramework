"""
Created on Apr 16, 2016

@author: Bruce
"""
import logging
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from typing import Dict, TYPE_CHECKING, Any
from ruamel import yaml

if TYPE_CHECKING:
    from .PointAbstract import PointAbstract
    from .AlarmAnalog import AlarmAnalog

logger = logging.getLogger('controller')

yaml = yaml.YAML()


class ProcessValue(PointAnalogReadOnlyAbstract):
    yaml_tag = u'!ProcessValue'

    # this is the callback passed to the pointAnalog that this ProcessValue wraps
    def point_updated(self, name: 'str'):
        #logger.debug("called for " + self.name + " from: " + name)
        for key in self.alarms:
            self.alarms[key].evaluate_analog(self._point.value)

    def __init__(self, point_analog: 'PointAnalogReadOnlyAbstract') -> 'None':

        self.control_points = {}  # type: 'Dict[str, PointAbstract]'
        self.alarms         = {}  # type: 'Dict[str, AlarmAnalog]'
        self.related_points = {}  # type: 'Dict[str, PointAbstract]'
        self._point         = None
        self._point_rw      = None

        self.high_display_limit = 0.0
        self.low_display_limit  = 0.0

        super().__init__()

        assert point_analog is not None,\
          "ProcessValue instanciated with null point."

        self._point = point_analog.get_readonly_object()
        point_analog.add_observer("ProcessValue", self.point_updated)

        # In order to setup the name of the analog point, we need to
        # temporarly hold on to a reference of the r/w object.
        # and discard it after the name is set.
        self._point_rw = point_analog

    def config(self, n: 'str') -> 'None':
        self._name = n
        self._point_rw.config(n)

        for k, o in self.control_points.items():
            o.config(n + ".control_points." + k)

        for k, o in self.related_points.items():
            o.config(n + ".related_points." + k)

        for k, o in self.alarms.items():
            o.config(n + ".alarms." + k)

    # methods to add alarms and points.
    def add_alarm(self, name, alarm_analog):
        self.alarms[name] = alarm_analog
        # self.alarms_list.append(alarm_analog)

    def add_control_point(self, n, point):
        self.control_points[n] = point

        # self.control_points_list.append(point)

    def add_related_point(self, n, point):
        self.related_points[n] = point
        # self.related_points_list.append(point)

    # #########################################################3
    # Below are properties proxied from the wrapped PointAnalog.

    # point name
    def _get_name(self) -> str:
        return self._point.name

    # def _set_name(self, n) -> None:
    #     assert self._point is not None, \
    #         "ProcessValue contains no wrapped PointAnalog"
    #     assert self._point_rw is not None,\
    #         "ProcessValue has already setup the point"
    #     self._point_rw.name = n
    #     self._point_rw = None

    name = property(_get_name)

    # Point EU value
    def _get_value(self):
        return self._point.value

    # def _set_value(self, value):
    #    self._point.value = value

    value = property(_get_value)

    # point HMI value
    def _get_hmi_value(self):
        return self._point.hmi_value

    def _set_hmi_value(self, v):
        self._point.hmi_value = v

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # Point quaity
    def _get_quality(self) -> bool:
        return self._point.quality

    # def _set_quality(self, quality: bool):
    #    self._point.quality = quality

    quality = property(_get_quality)

    # Point forced
    def _get_forced(self) -> bool:
        return self._point.forced

    # def _set_forced(self, forced: bool):
    #     self._point.forced = forced

    forced = property(_get_forced)

    # Description
    def _get_description(self) -> str:
        return self._point.description

    description = property(_get_description)

    # human readable value
    @property
    def human_readable_value(self) -> str:
        return self._point.human_readable_value

    # last update property
    def _get_last_update(self):
        return self._point.last_update

    last_update = property(_get_last_update)

    # HMI writable
    @property
    def hmi_writeable(self):
        return self._point.hmi_writeable

    # data display width
    @property
    def data_display_width(self) -> int:
        return self._point.data_display_width

    # point observers
    def add_observer(self, name: 'str', observer: 'Callable[str, None]') -> 'None':
        self._point.add_observer(name, observer)

    def del_observer(self, name: 'str') -> 'None':
        self.point.del_observer(name)

    @property
    def hmi_object_name(self) -> str:
        return "ProcessValueWindow"

    # writer
    def _get_writer(self) -> object:
        return self._point.writer

    # def _set_writer(self, w: object):
    #     self._point.writer = w

    writer = property(_get_writer)

    # unit of measure
    def _get_u_of_m(self) -> str:
        return self._point.u_of_m

    # def _set_u_of_m(self, s: str):
    #     self._point.u_of_m = s

    u_of_m = property(_get_u_of_m)

    def get_readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return self

    def get_readwrite_object(self) -> 'PointAnalog':
        return self._point.get_readwrite_object()

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = {
          'point': self._point,
          'high_display_limit': self.high_display_limit,
          'low_display_limit': self.low_display_limit,
          'control_points': self.control_points,
          'alarms': self.alarms,
          'related_points': self.related_points,
        }
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        self._point = d['point']
        self.high_display_limit = d['high_display_limit']
        self.low_display_limit = d['low_display_limit']
        self.control_points = d['control_points']
        self.alarms = d['alarms']
        self.related_points = d['related_points']


    # yaml dumping function
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        cps = {}
        if self.control_points is not None:
            for k in self.control_points:
                cps[k] = self.control_points[k]

        alms = {}
        if self.alarms is not None:
            for k in self.alarms:
                alms[k] = self.alarms[k]

        rps = {}
        if self.related_points is not None:
            for k in self.related_points:
                rps[k] = self.related_points[k]

        d = {
           'point': self._point.yamlable_object,
           'high_display_limit': self.high_display_limit,
           'low_display_limit': self.low_display_limit,
           'control_points': cps,
           'alarms': alms,
           'related_points': rps,
        }
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!ProcessValue',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        # reference https://bitbucket.org/ruamel/yaml/issues/189/construct_mapping-of-inline-mapping-fails
        # https://stackoverflow.com/questions/43812020/what-does-deep-true-do-in-pyyaml-loader-construct-mapping/43812995#43812995

        # If you dump a data structure that has the same object/mapping/sequence
        # attached at multiple positions you'll get anchors and aliases in your
        # YAML and then you need deep=True to be able to load those. If you dump
        # data that at some point has an object that "underneath" itself has a
        # self reference, you will get anchors and aliases as well, but you'll
        # need deep=True and the two-step process provided by yield to be able
        # to load that YAML. So I always make constructors for non-scalars (the
        # potential (self)-recursive ones) with yield and deep=True although not
        # needed by some YAML docs. – Anthon May 5 '17 at 20:20

        value = constructor.construct_mapping(node, deep=True)
        assert value['point'] is not None, \
          "ProcessValue created from yaml without associated point object for " + str(value)

        p = ProcessValue(value['point'])
        p.high_display_limit = value['high_display_limit']
        p.low_display_limit = value['low_display_limit']

        for k,v in value['control_points'].items():
            p.add_control_point(k, v)
            print("    control point " + k + " added")

        for k,v in value['alarms'].items():
            p.add_alarm(k, v)
            print("    alarm " + k + " added")

        for k,v in value['related_points'].items():
            p.add_related_point(k, v)
            print("    related point " + k + " added")

        return p
