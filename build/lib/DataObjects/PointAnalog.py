import logging
from .PointAnalogAbstract import PointAnalogAbstract
from .Point import Point
from typing import Dict, Any, List

logger = logging.getLogger('controller')


class PointAnalog(Point, PointAnalogAbstract):

    def _get_keywords(self) -> 'List[str]':
        return super().keywords + ['u_of_m']

    keywords = property(_get_keywords)

    def __init__(self, **kwargs) -> None:
        super().__init__()
        self._u_of_m = None  # type: str
        self._value = 0.0  # type: float
        # self.deadband = 0.0  # type: float

        for kw in kwargs:
            if kw in self.keywords:
                setattr(self, kw, kwargs[kw])
            else:
                raise Exception(
                    "Cannot assign " + str(kw) +
                    " to PointAnalog, property does not exist")
        self.sanity_check()

    # dict object used to convert the object to JSON

    def _get__dict__(self) -> Dict[str, Any]:
        d = super().__dict__
        d.update(dict(u_of_m=self.u_of_m))
        return d

    __dict__ = property(_get__dict__)

    # human readable value
    @property
    def human_readable_value(self) -> str:
        return str(round(self._value, 2))

    # data display width
    @property
    def data_display_width(self) -> int:
        return 8

    def _set_hmi_value(self, v: str):
        super()._set_hmi_value(float(v))

    def _get_hmi_value(self):
        return super()._get_hmi_value()

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # HMI window type
    @property
    def hmi_object_name(self) -> str:
        return "PointAnalogWindow"

    def _get_u_of_m(self) -> str:
        return self._u_of_m

    def _set_u_of_m(self, s):
        self._u_of_m = s

    u_of_m = property(_get_u_of_m, _set_u_of_m)

