""""
Created on Apr 16, 2016

@author: Bruce
"""

from .Point import Point
from .PointSaveable import PointSaveable
from typing import Dict, Any
from .PointReadOnlyAbstract import PointReadOnlyAbstract
from .PointReadOnly import PointReadOnly


class PointEnumeration(Point, PointSaveable):

    def __init__(self, **kwargs) -> None:
        self.states = []
        self._value = 0
        super().__init__(**kwargs)

    def _get_keywords(self):
        return super().keywords + ['states']

    keywords = property(_get_keywords)

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)

    def _get__dict__(self) -> 'Dict[str, Any]':
        d = super().__dict__
        d.update(dict(states=self.states))
        return d

    __dict__ = property(_get__dict__)

    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = super()._get_yaml_dict()
        d.update(dict(states=self.states))
        return d

    # human readable value
    @property
    def human_readable_value(self):
        return self.states[self._value]

    # hmi_value
    def _get_hmi_value(self):
        return self.value

    def _set_hmi_value(self, v: str):
        if v in self.states:
            super()._set_hmi_value(v)
        else:
            raise Exception(
                "Tried to set " + self.description + " to a state of " + v +
                " which is not a valid state.")

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # value
    def _get_value(self) -> object:
        return self.states[super().value]

    def _set_value(self, v):
        if v in self.states:
            super()._set_value(self.states.index(v))
        else:
            raise Exception(
                "Tried to set " + self.description + " to a state of " + str(v) +
                " which is not a valid state.")

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

    def get_yaml_object(self) -> 'PointEnumeration':
        return self

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointEnumeration',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)

        return PointEnumeration(**value)
