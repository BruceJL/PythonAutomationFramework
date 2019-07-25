from .PointAnalogAbstract import PointAnalogAbstract
from .PointSaveable import PointSaveable
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointReadOnly import PointReadOnly
from .Point import Point
from typing import Dict, Any, List
from ruamel import yaml


class PointAnalog(Point, PointAnalogAbstract, PointSaveable):
    yaml_tag = u'!PointAnalog'

    def _get_keywords(self) -> 'List[str]':
        return super()._get_keywords() + ['u_of_m']

    keywords = property(_get_keywords)

    def __init__(self, **kwargs: object) -> None:
        self.u_of_m = None  # type: str
        self._value = 0.0  # type: float
        super().__init__(**kwargs)

    # YAML representation for configuration storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = super()._get_yaml_dict()
        d.update(dict(
          u_of_m=self.u_of_m,
        ))
        return d

    # dict object used to convert the object to JSON
    def _get__dict__(self) -> 'Dict[str, Any]':
        d = super().__dict__
        d.update(dict(u_of_m=self.u_of_m))
        return d

    __dict__ = property(_get__dict__)

    def _get_config_dict(self) -> 'Dict[str, Any]':
        d = super()._get_config_dict()
        d.update(dict(u_of_m=self._u_of_m))
        return d

    # human readable value
    @property
    def human_readable_value(self) -> 'str':
        if self._value is not None and self.u_of_m is not None:
            return str(round(self._value, 2)) + " " + self.u_of_m
        else:
            return "***"

    @property
    def editable_value(self) -> 'str':
        return str(self._value)

    # data display width
    @property
    def data_display_width(self) -> 'int':
        return len(self.human_readable_value)

    def _set_hmi_value(self, v: str):
        super()._set_hmi_value(float(v))

    def _get_hmi_value(self):
        return super()._get_hmi_value()

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # HMI window type
    @property
    def hmi_object_name(self) -> 'str':
        return "PointAnalogWindow"

    def _get_u_of_m(self) -> 'str':
        return self._u_of_m

    def _set_u_of_m(self, s):
        self._u_of_m = s

    u_of_m = property(_get_u_of_m, _set_u_of_m)

    def get_readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return PointReadOnly(self)

    def get_readwrite_object(self) -> 'PointAnalog':
        return self

    def get_yaml_object(self) -> 'PointAnalog':
        return self

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
