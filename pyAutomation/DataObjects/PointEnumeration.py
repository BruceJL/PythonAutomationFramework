""""
Created on Apr 16, 2016

@author: Bruce
"""

from .Point import Point
from typing import Dict, Any
from .PointReadOnlyAbstract import PointReadOnlyAbstract
from .PointReadOnly import PointReadOnly


class PointEnumeration(Point):

    def __init__(self, **kwargs) -> None:
        self.states = []

        tmp_value = None
        if 'value' in kwargs:
            tmp_value = kwargs['value']
            kwargs.pop('value', None)

        super().__init__(**kwargs)

        if tmp_value is not None:
            super()._set_value(tmp_value)

    def _get_keywords(self):
        return super().keywords + ['states']

    keywords = property(_get_keywords)

    # human readable value
    @property
    def human_readable_value(self):
        return self.states[self._value]

    # hmi_value
    def _get_hmi_value(self):
        return self.value

    def _set_hmi_value(self, v: str):
        assert v in self.states, \
          "Tried to set " + self.description + " to a state of " + v + \
          " which is not a valid state."
        super()._set_hmi_value(v)

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # value
    def _get_value(self) -> object:
        return self.states[super()._get_value()]

    def _set_value(self, v: "str") -> 'None':
        assert v in self.states, "Tried to set " + self.description + \
          " to a state of " + str(v) + " which is not a valid state."

        super()._set_value(self.states.index(v))

    value = property(_get_value, _set_value)

    # forced value
    @property
    def forced_value(self):
        return self.states[super().value]

    @forced_value.setter
    def forced_value(self, v):
        super().forced_value(self.states.index(v))

    # data display width
    @property
    def data_display_width(self) -> int:
        x = 0
        for s in self.states:
            if len(s) > x:
                x = len(s)
        return x

    @property
    def hmi_object_name(self)-> str:
        return "PointEnumerationWindow"

    def get_readonly_object(self) -> 'PointReadOnlyAbstract':
        return PointReadOnly(self)

    def get_readwrite_object(self) -> 'PointEnumeration':
        return self

    def __getstate__(self) -> 'Dict[str, Any]':
        """
        Gets a dict representation of the point suitable for JSON
        transport to an HMI client. This function is specified by the
        jsonpickle library to pickle an object.

        Returns:
            dict: a dict of point properties.

        """
        d = super().__getstate__()
        d.update({'states': self.states})
        return d

    def __setstate__(self, d: 'Dict[str, Any]'):
        self.states = d['states']
        super().__setstate__(d)

    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = super()._get_yaml_dict()
        d.update(dict(states=self.states))
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointEnumeration',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        d = constructor.construct_mapping(node)
        return PointEnumeration(**d)
