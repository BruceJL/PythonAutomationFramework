from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Callable


class PointReadOnlyAbstract(ABC):

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    # value
    @abstractmethod
    def _get_value(self):
        pass

    value = property(_get_value)

    # next_update
    def _get_next_update(self) -> datetime:
        return datetime.max

    next_update = property(_get_next_update)

    # hmi value
    @abstractmethod
    def _get_hmi_value(self) -> str:
        pass

    hmi_value = property(_get_hmi_value)

    # description
    @abstractmethod
    def _get_description(self) -> str:
        pass

    description = property(_get_description)

    # forced
    @abstractmethod
    def _get_forced(self) -> bool:
        pass

    forced = property(_get_forced)

    # last_update
    @abstractmethod
    def _get_last_update(self) -> datetime:
        pass

    last_update = property(_get_last_update)

    @abstractmethod
    def _get_name(self):
        pass

    name = property(_get_name)

    # quality.
    @abstractmethod
    def _get_quality(self) -> bool:
        pass

    quality = property(_get_quality)

    # writer
    @abstractmethod
    def _get_writer(self) -> object:
        pass

    writer = property(_get_writer)

    # observers
    @abstractmethod
    def _get_observers(self) -> 'List[Callable[[str], None]]':
        pass

    observers = property(_get_observers)

    # Human readable value for HMI usage.
    @property
    @abstractmethod
    def human_readable_value(self) -> str:
        pass

    # HMI data display width. Number of columns needed to display this info.
    @property
    @abstractmethod
    def data_display_width(self) -> int:
        pass

    def sanity_check(self):
        if self.name == "":
            raise ValueError("Point name is blank")

    @property
    @abstractmethod
    def hmi_object_name(self) -> str:
        pass