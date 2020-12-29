from .PointReadOnlyAbstract import PointReadOnlyAbstract
from .PointAbstract import PointAbstract
from pyAutomation.Supervisory.Interruptable import Interruptable
from typing import Dict, Any
from datetime import datetime


class PointReadOnly(PointReadOnlyAbstract):

    def __init__(self, point: PointReadOnlyAbstract) -> None:
        self._point = point

    def __getstate__(self) -> 'Dict[str, Any]':
        d = dict(point=self._point)
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> None:
        self._point = d['point']

    def config(self) -> None:
        pass

    def _get_name(self) -> str:
        return self._point.name

    name = property(_get_name)

    def _get_value(self):
        return self._point.value

    value = property(_get_value)

    def _get_hmi_writeable(self):
        return self._point.hmi_writeable

    hmi_writeable = property(_get_hmi_writeable)

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

    def _get_human_readable_value(self):
        return self._point.human_readable_value

    def _get_data_display_width(self) -> 'int':
        return self._point.data_display_width

    def _get_description(self) -> 'str':
        return self._point.description

    description = property(_get_description)

    def _get_last_update(self) -> datetime:
        return self._point.last_update

    last_update = property(_get_last_update)

    # point observers
    def add_observer(
      self,
      name: 'str',
      observer: 'Interruptable[str, None]'
    ) -> 'None':
        self._point.add_observer(name, observer)

    def del_observer(self, name: 'str') -> 'None':
        self._point.del_observer(name)

    # HMI object name
    def _get_hmi_object_name(self) -> str:
        return self._point.hmi_object_name

    # Return a pointer to a read only instance of this object
    @property
    def readonly_object(self) -> 'PointReadOnlyAbstract':
        return self

    # Return a pointer to a read/write instance of this object.
    @property
    def readwrite_object(self) -> 'PointAbstract':
        return self._point.get_readwrite_object()

    def _get_request_value(self) -> 'str':
        return self._point.request_value

    def _set_request_value(self, value) -> 'None':
        self._point.request_value = value
