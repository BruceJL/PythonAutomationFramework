from datetime import datetime
from abc import ABC
from abc import abstractmethod
from typing import List
import logging
from pyAutomation.DataObjects.PointReadOnlyAbstract import PointReadOnlyAbstract
from pyAutomation.DataObjects.PointAbstract import PointAbstract


class i2cPrototype(ABC):

    def __init__(self, name: str, logger: str) -> None:
        self.device_points = []  # type: List[PointAbstract]
        self._has_write_data = False  # type: bool
        self.last_io_attempt = datetime.now()  # type: datetime.datetime
        self.is_setup = False
        self.name = name
        self.logger = logging.getLogger(logger)
        self.logger.debug("created device " + self.name + " using logger " + logger)
        self.delay_until = None

    @abstractmethod
    def read_data(self):
        pass

    @abstractmethod
    def write_data(self):
        pass

    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def config(self):
        pass

    def _get_name(self) -> str:
        return self._name

    def _set_name(self, name: str) -> None:
        self._name = name

    name = property(_get_name, _set_name)

    @property
    def interrupt_points(self) -> List[PointReadOnlyAbstract]:
        return []

    @property
    def has_write_data(self) -> bool:
        if self.delay_until is not None:
            if self.delay_until < datetime.now():
                self.delay_until = None
            else:
                return False

        if hasattr(self, '_has_write_data'):
            return self._has_write_data
        else:
            return False

    @property
    def next_update(self) -> datetime:
        if self.delay_until is not None:
            if self.delay_until < datetime.now():
                self.delay_until = None
            else:
                return self.delay_until

        next_update = datetime.max
        if self.device_points is not None:
            for p in self.device_points:
                if p is not None:
                    point_next_update = p.next_update

                    if point_next_update is None:
                        self.logger.debug(p.name + " has next update of NONE")
                        continue

                    else:
                        self.logger.debug(p.name + " has next update of: " + str(p.next_update))
                        if point_next_update < next_update:
                            next_update = point_next_update

        if datetime.max == next_update:
            next_update = None

        self.logger.debug("for: " +  self.name + " is " + str(next_update))

        return next_update
