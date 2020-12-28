from .PointAnalogReadOnly import PointAnalogReadOnly
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from pyAutomation.DataObjects.Point import Point
from typing import Dict, List, Any


class PointAnalog(Point, PointAnalogReadOnlyAbstract):
    """ Concrete implementation of an Analog point. Stores values as floats.
    PointAnalogs can be quantized or continous. """
    yaml_tag = u'!PointAnalog'

    _u_of_m = None  # type: 'str'
    _value = 0.0  # type: 'float'

    def _get_keywords(self) -> 'List[str]':
        return super()._get_keywords() + ['u_of_m']

    keywords = property(_get_keywords)

    def __init__(self, **kwargs: object) -> 'None':
        super().__init__(**kwargs)

    # human readable value
    @property
    def human_readable_value(self) -> 'str':
        if self._value is not None and self.u_of_m is not None:
            return str(round(self._value, 2)) + " " + self.u_of_m
        elif self._value is not None:
            return str(round(self._value, 2))
        else:
            return "***"

    @property
    def editable_value(self) -> 'str':
        return str(self._value)

    # data display width
    @property
    def data_display_width(self) -> 'int':
        return len(self.human_readable_value)

    def _set_hmi_value(self, v: 'str'):
        super()._set_hmi_value(float(v))

    def _get_hmi_value(self):
        return super()._get_hmi_value()

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # HMI window type
    def _get_hmi_object_name(self) -> 'str':
        return "PointAnalogWindow"

    def _get_u_of_m(self) -> 'str':
        return self._u_of_m

    def _set_u_of_m(self, s):
        self._u_of_m = s

    u_of_m = property(_get_u_of_m, _set_u_of_m)

    def get_readonly_object(self) -> 'PointAnalogReadOnly':
        return PointAnalogReadOnly(self)

    def get_readwrite_object(self) -> 'PointAnalog':
        return self

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = super().__getstate__()
        d.update({'u_of_m': self.u_of_m})
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        super().__setstate__(d)
        self._u_of_m = d['u_of_m']

    # YAML representation for configuration storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = super()._get_yaml_dict()
        d.update({'u_of_m': self.u_of_m})
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalog',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)
        return PointAnalog(**value)
