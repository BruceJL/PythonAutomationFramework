from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
import logging
from .Observable import Observable

if TYPE_CHECKING:
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from typing import Any

logger = logging.getLogger('controller')


class PointReadOnlyAbstract(Observable, ABC):
    '''PointReadOnlyAbstract is the base type that all points - abstract or
    concrete are derived from. The functions contained in this class will be
    present for every point in the database. '''

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @abstractmethod
    def config(self) -> 'None':
        pass

    @abstractmethod
    def value(self) -> 'Any':
        pass

    # hmi value
    @property
    @abstractmethod
    def hmi_value(self) -> 'str':
        pass

    @property
    @abstractmethod
    def hmi_writeable(self) -> 'bool':
        pass

    # next_update
    @property
    @abstractmethod
    def next_update(self) -> 'datetime':
        return datetime.max

    # description
    @property
    @abstractmethod
    def description(self) -> 'str':
        pass

    # forced
    @property
    @abstractmethod
    def forced(self) -> 'bool':
        pass

    # last_update
    @property
    @abstractmethod
    def last_update(self) -> 'datetime':
        pass

    # name
    @property
    @abstractmethod
    def name(self) -> 'str':
        pass

    # quality.
    @property
    @abstractmethod
    def quality(self) -> 'bool':
        pass

    # writer
    @property
    @abstractmethod
    def writer(self) -> 'object':
        pass

    @property
    @abstractmethod
    def readonly(self) -> 'bool':
        pass

    # HMI data display width. Number of columns needed to display this info.
    @property
    @abstractmethod
    def data_display_width(self) -> 'int':
        pass

    def sanity_check(self):
        assert self.name is not None, \
          "Point defined without a name"

        assert self.description is not None, \
          "Point defined without a description"

    @property
    @abstractmethod
    def hmi_object_name(self) -> 'str':
        pass

    @property
    @abstractmethod
    def readonly_object(self) -> 'PointReadOnlyAbstract':
        pass

    @property
    @abstractmethod
    def readwrite_object(self) -> 'PointAbstract':
        return self
