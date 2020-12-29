from .PointAnalogReadOnly import PointAnalogReadOnly
from .PointAnalogAbstract import PointAnalogAbstract
from typing import Dict, List, Any


class PointAnalog(PointAnalogAbstract):
    """ Concrete implementation of an Analog point. Stores values as floats.
    PointAnalogs can be quantized or continous.
    """

    yaml_tag = u'!PointAnalog'

    _value = 0.0  # type: 'float'

    def __init__(self, **kwargs: 'str') -> 'None':
        super().configure_parameters(**kwargs)

    @property
    def u_of_m(self) -> 'str':
        return self._u_of_m

    @u_of_m.setter
    def u_of_m(self, value) -> 'None':
        self._u_of_m = value

    @property
    def keywords(self) -> 'List[str]':
        return super().keywords + ['u_of_m']

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
        super()._set_hmi_value(v)

    def _get_hmi_value(self):
        return super()._get_hmi_value()

    # HMI window type
    @property
    def hmi_object_name(self) -> 'str':
        return "PointAnalogWindow"

    # Return readonly and read/write copies of this object.
    @property
    def readonly_object(self) -> 'PointAnalogReadOnly':
        return PointAnalogReadOnly(self)

    @property
    def readwrite_object(self) -> 'PointAnalog':
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
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = super().yaml_dict
        d.update({'u_of_m': self.u_of_m})
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalog',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)
        return PointAnalog(**value)
