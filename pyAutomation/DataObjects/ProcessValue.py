import logging
from typing import TYPE_CHECKING

from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract

if TYPE_CHECKING:
    from .PointAbstract import PointAbstract
    from .AlarmAnalog import AlarmAnalog
    from .PointAnalog import PointAnalog
    from typing import Dict, Any
    from datetime import datetime

logger = logging.getLogger('controller')


class ProcessValue(PointAnalogReadOnlyAbstract):
    yaml_tag = u'!ProcessValue'
    _name = None  # type: str

    # this is the callback passed to the pointAnalog that this ProcessValue
    # wraps
    def point_updated(self, name: 'str'):
        # logger.debug("called for " + self.name + " from: " + name)
        for key in self.alarms:
            self.alarms[key].evaluate_analog(self._point.value)

    _point = None  # type: PointAnalogReadOnlyAbstract

    def __init__(self, point_analog: 'PointAnalogReadOnlyAbstract') -> 'None':

        self.control_points = {}  # type: 'Dict[str, PointAbstract]'
        self.alarms = {}  # type: 'Dict[str, AlarmAnalog]'
        self.related_points = {}  # type: 'Dict[str, PointAbstract]'

        self.high_display_limit = 0.0
        self.low_display_limit = 0.0

        super().__init__()

        assert point_analog is not None,\
            "ProcessValue instanciated with null point."

        self._point = point_analog

    def config(self) -> 'None':
        self._point.name = f"{self._name}.point"
        self._point.config()

        # now that the point has been named and configured, switch over to a
        # read-only copy of the object.

        self._point = self._point.readonly_object

        self._point.add_observer("ProcessValue", self.point_updated)

        for key, value in self.control_points.items():
            value.config()

        for key, value in self.related_points.items():
            value.config()

        for key, value in self.alarms.items():
            value.config()

    # methods to add alarms and points.
    def add_alarm(self, name, alarm_analog):
        self.alarms[name] = alarm_analog
        alarm_analog.name = f"{self.name}.alarms.{name}"

    def add_control_point(self, name, point):
        self.control_points[name] = point
        point.name = f"{self.name}.control.{name}"

    def add_related_point(self, name, point):
        self.related_points[name] = point
        point.name = f"{self.name}.related.{name}"

    # #########################################################
    # Below are properties proxied from the wrapped PointAnalog.

    # point name
    @property
    def name(self) -> 'str':
        return self._name

    @name.setter
    def name(self, name) -> 'None':
        self._name = name

    # Point EU value
    @property
    def value(self) -> 'float':
        return self._point.value

    # point HMI value
    @property
    def hmi_value(self) -> 'str':
        return self._point.hmi_value

    @hmi_value.setter
    def hmi_value(self, value) -> 'None':
        self._point.hmi_value = value

    # Point quaity
    @property
    def quality(self) -> 'bool':
        return self._point.quality

    # Point forced
    @property
    def forced(self) -> 'bool':
        return self._point.forced

    # Description
    @property
    def description(self) -> 'str':
        return self._point.description

    # human readable value
    @property
    def human_readable_value(self) -> 'str':
        return self._point.human_readable_value

    # last update property
    @property
    def last_update(self) -> 'datetime':
        return self._point.last_update

    @property
    def next_update(self) -> 'datetime':
        return self._point.next_update

    @property
    def readonly(self) -> 'bool':
        return True

    @property
    def request_value(self) -> 'str':
        return self._point.request_value

    @request_value.setter
    def request_value(self, value: 'str') -> 'None':
        self._point.request_value = value

    # HMI writable
    @property
    def hmi_writeable(self) -> 'bool':
        return self._point.hmi_writeable

    # data display width
    @property
    def data_display_width(self) -> 'int':
        return self._point.data_display_width

    @property
    def hmi_object_name(self) -> 'str':
        return "ProcessValueWindow"

    # writer
    @property
    def writer(self) -> 'object':
        return self._point.writer

    # unit of measure
    @property
    def u_of_m(self) -> 'str':
        return self._point.u_of_m

    @property
    def readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return self

    @property
    def readwrite_object(self) -> 'PointAnalog':
        return self._point.readwrite_object

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = {
          'point': self._point.readwrite_object,
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
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
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
          'point': self._point.readwrite_object,
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
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        # reference https://bitbucket.org/ruamel/yaml/issues/189/
        # construct_mapping-of-inline-mapping-fails
        # https://stackoverflow.com/questions/43812020/
        # what-does-deep-true-do-in-pyyaml-loader-construct-mapping
        # /43812995#43812995

        # If you dump a data structure that has the same
        # object/mapping/sequence attached at multiple positions you'll get
        # anchors and aliases in your YAML and then you need deep=True to be
        # able to load those. If you dump data that at some point has an
        # object that "underneath" itself has a self reference, you will get
        # anchors and aliases as well, but you'll need deep=True and the
        # two-step process provided by yield to be able to load that YAML.
        # So I always make constructors for non-scalars (the potential
        # (self)-recursive ones) with yield and deep=True although not needed
        #  by some YAML docs. – Anthon May 5 '17 at 20:20

        value = constructor.construct_mapping(node, deep=True)
        assert value['point'] is not None, \
            "ProcessValue created from yaml without associated point object " \
            + "for " + str(value)

        p = ProcessValue(value['point'])
        p.high_display_limit = value['high_display_limit']
        p.low_display_limit = value['low_display_limit']

        for k, v in value['control_points'].items():
            p.add_control_point(k, v)
            logger.info("    control point %s added", k)

        for k, v in value['alarms'].items():
            p.add_alarm(k, v)
            logger.info("    alarm %s added", k)

        for k, v in value['related_points'].items():
            p.add_related_point(k, v)
            logger.info("    related point %s added", k)

        return p
