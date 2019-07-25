""""
Created on Apr 16, 2016

@author: Bruce
"""

import logging
from .Point import Point
from typing import Dict, Any

logger = logging.getLogger('controller')


class PointEnumeration(Point):

    def _get_keywords(self):
        return super().keywords + ['states']

    keywords = property(_get_keywords)

    def __init__(self, **kwargs):
        self.states = []
        super().__init__()
        for kw in kwargs:
            if kw in self.keywords:
                setattr(self, kw, kwargs[kw])
            else:
                raise Exception("Cannot assign " + str(kw) + " to PointEnumeration, property does not exist")
        self._value = 0
        self.sanity_check()

    def _get__dict__(self) -> 'Dict[str, Any]':
        d = super().__dict__
        d.update(dict(states=self.states))
        return d

    __dict__ = property(_get__dict__)

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
