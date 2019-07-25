from .PointReadOnlyAbstract import PointReadOnlyAbstract
from typing import Dict, Any
from datetime import datetime
from typing import Callable, List


class PointReadOnly(PointReadOnlyAbstract):

    def __init__(self, point: PointReadOnlyAbstract) -> None:
        self._point = point

    # def __getattr__(self, attr):
    #     return getattr(self.__dict__['_point'], attr)

    # def __setattr__(self, attr, val):
    #        self._point.__dict__[attr] = val

    def _get__dict__(self) -> 'Dict[str, Any]':
        d = dict(_point=self._point)
        return d

    __dict__ = property(_get__dict__)

    def _get_name(self) -> str:
        return self._point.name

    name = property(_get_name)

    def _get_value(self):
        return self._point.value

    value = property(_get_value)

    def _get_hmi_value(self):
        return self._point.hmi_value

    def _set_hmi_value(self, v):
        self._point.hmi_value = v

    hmi_value = property(_get_hmi_value, _set_hmi_value)

    def _get_quality(self) -> bool:
        return self._point.quality

    quality = property(_get_quality)

    def _get_forced(self) -> bool:
        return self._point.forced

    forced = property(_get_forced)

    def _get_writer(self) -> object:
        return self._point.writer

    writer = property(_get_writer)

    @property
    def human_readable_value(self):
        return self._point.human_readable_value

    @property
    def data_display_width(self) -> int:
        return self._point.data_display_width

    def _get_description(self) -> str:
        return self._point.description

    description = property(_get_description)

    def _get_last_update(self) -> datetime:
        return self._point.last_update

    last_update = property(_get_last_update)

    def _get_observers(self) -> 'List[Callable[[str], None]]':
        return self._point.observers

    observers = property(_get_observers)

    def _get_hmi_object_name(self) -> str:
        return self._point.hmi_object_name

    hmi_object_name = property(_get_hmi_object_name)
