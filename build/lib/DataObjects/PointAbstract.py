from abc import abstractmethod
from datetime import datetime
from .PointReadOnlyAbstract import PointReadOnlyAbstract


class PointAbstract(PointReadOnlyAbstract):

    hmi_writeable = False

    # value
    @abstractmethod
    def _get_value(self):
        pass

    @abstractmethod
    def _set_value(self, v) -> None:
        pass

    value = property(_get_value, _set_value)

    # description
    @abstractmethod
    def _get_description(self) -> str:
        pass

    @abstractmethod
    def _set_description(self, s: str):
        pass

    description = property(_get_description, _set_description)

    # forced
    @abstractmethod
    def _get_forced(self) -> bool:
        pass

    @abstractmethod
    def _set_forced(self, value):
        pass

    forced = property(_get_forced, _set_forced)

    # last_update
    @abstractmethod
    def _get_last_update(self) -> datetime:
        pass

    @abstractmethod
    def _set_last_update(self, d: datetime):
        pass

    last_update = property(_get_last_update, _set_last_update)

    @abstractmethod
    def _get_name(self):
        pass

    @abstractmethod
    def _set_name(self, name):
        pass

    name = property(_get_name, _set_name)

    # quality.
    @abstractmethod
    def _get_quality(self) -> bool:
        pass

    @abstractmethod
    def _set_quality(self, value):
        pass

    quality = property(_get_quality, _set_quality)

    # Human readable value for HMI usage.
    @property
    @abstractmethod
    def human_readable_value(self) -> str:
        pass

    # Get data display width for HMI usage
    @property
    @abstractmethod
    def data_display_width(self) -> int:
        pass

    @abstractmethod
    def _get_writer(self) -> object:
        pass

    @abstractmethod
    def _set_writer(self, w: object):
        pass

    writer = property(_get_writer, _set_writer)

    @abstractmethod
    def _get_hmi_value(self) -> str:
        pass

    @abstractmethod
    def _set_hmi_value(self, s: str):
        pass

    hmi_value = property(_get_hmi_value, _set_hmi_value)
