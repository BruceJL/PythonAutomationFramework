"""
Created on Apr 14, 2016

@author: Bruce
"""

import logging

from .Point import Point
from typing import List, Dict, Any

logger = logging.getLogger('controller')


class PointDiscrete(Point):

    def _get_keywords(self) -> List[str]:
        return super()._get_keywords() + ['on_state_description', 'off_state_description']

    keywords = property(_get_keywords)

    def __init__(self, **kwargs):
        self.on_state_description = "ON"
        self.off_state_description = "OFF"
        super().__init__()
        for kw in kwargs:
            if kw in self.keywords:
                setattr(self, kw, kwargs[kw])
            else:
                raise Exception("Cannot assign " + str(kw) + " to PointDiscrete, property does not exist")
        self.sanity_check()

    def _get__dict__(self) -> 'Dict[str, Any]':
        d = super().__dict__
        d.update(dict(on_state_description=self.on_state_description,
                      off_state_description=self.off_state_description))
        return d

    __dict__ = property(_get__dict__)

    # value accessed through HMI
    def _get_hmi_value(self) -> str:
        return super()._get_hmi_value()

    def _set_hmi_value(self, v: str):
        if not isinstance(v, str):
            raise ValueError('Supply argument %s is not a string' % v)
        if v == "True":
            x = True
        else:
            x = False
        super()._set_hmi_value(x)

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # human readable value
    @property
    def human_readable_value(self) -> str:
        if self.hmi_value:
            return self.on_state_description
        else:
            return self.off_state_description

    # data display width
    @property
    def data_display_width(self) -> int:
        i = len(self.off_state_description)
        if len(self.on_state_description) > i:
            i = len(self.off_state_description)
        assert isinstance(i, int)
        return i

    # HMI window type
    @property
    def hmi_object_name(self) -> str:
        return "PointDiscreteWindow"
