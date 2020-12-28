from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from pyAutomation.DataObjects.PointAbstract import PointAbstract
    from typing import Callable, Dict

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
    @abstractmethod
    def _get_value(self):
        pass

    value = property(_get_value)

    # next_update
    def _get_next_update(self) -> 'datetime':
        return datetime.max

    next_update = property(_get_next_update)

    # hmi value
    @abstractmethod
    def _get_hmi_value(self) -> 'str':
        pass

    hmi_value = property(_get_hmi_value)

    # description
    @abstractmethod
    def _get_description(self) -> 'str':
        pass

    description = property(_get_description)

    # forced
    @abstractmethod
    def _get_forced(self) -> 'bool':
        pass

    forced = property(_get_forced)

    # last_update
    @abstractmethod
    def _get_last_update(self) -> 'datetime':
        pass

    last_update = property(_get_last_update)

    @abstractmethod
    def _get_name(self):
        pass

    name = property(_get_name)

    # quality.
    @abstractmethod
    def _get_quality(self) -> 'bool':
        pass

    quality = property(_get_quality)

    # writer
    @abstractmethod
    def _get_writer(self) -> 'object':
        pass

    writer = property(_get_writer)

    def _get_readonly(self) -> 'bool':
        return True

    readonly = property(_get_readonly)

    def add_observer(
      self,
      name: 'str',
      observer: 'Callable[[str], None]') -> 'None':
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
    def data_display_width(self) -> int:
        raise NotImplementedError("Not implemented")

    def sanity_check(self):
        assert self.name is not None, \
          "Point defined without a name"

        assert self.description is not None, \
          "Point defined without a description"

    # Get and set the requested value from non-owner processes.
    @abstractmethod
    def _get_request_value(self):
        pass

    @abstractmethod
    def _set_request_value(self, value):
        pass

    request_value = property(_get_request_value, _set_request_value)

    @abstractmethod
    def _get_hmi_object_name(self) -> 'str':
        pass

    hmi_object_name = property(_get_hmi_object_name)

    @abstractmethod
    def get_readonly_object(self) -> 'PointReadOnlyAbstract':
        pass

    @abstractmethod
    def get_readwrite_object(self) -> 'PointAbstract':
        return self
