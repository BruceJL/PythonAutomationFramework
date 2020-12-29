from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from typing import Callable, Dict, Any, List

logger = logging.getLogger('controller')


class PointReadOnlyAbstract(ABC):
    '''PointReadOnlyAbstract is the base type that all points - abstract or
    concrete are derived from. The functions contained in this class will be
    present for every point in the database. '''

    _observers = {}  # type: Dict[str, Callable]

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @abstractmethod
    def config(self) -> 'None':
        pass

    # value
    @property
    @abstractmethod
    def value(self):
        pass

    # next_update
    @property
    @abstractmethod
    def next_update(self) -> 'datetime':
        return datetime.max

    # hmi value
    @property
    @abstractmethod
    def hmi_value(self) -> 'str':
        pass

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
    def  last_update(self) -> 'datetime':
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

    def add_observer(
      self,
      name: 'str',
      observer: 'Callable[[str, Any], Any]') -> 'None':
        assert name is not None, (
          "No name supplied for observer added to %s" % self.description
        )
        self._observers.update({name: observer})

        logger.info("observer: %s added to point %s", name, self.name)

    def del_observer(self, name: 'str') -> 'None':
        self._observers.pop(name)
        logger.info("observer: %s removed from point %s", name, self.name)

    # Human readable value for HMI usage.
    @property
    @abstractmethod
    def human_readable_value(self) -> 'str':
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
