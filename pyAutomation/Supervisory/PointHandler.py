from abc import ABC, abstractmethod
from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.Supervisory.Interruptable import Interruptable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any


class PointHandler(Interruptable, ABC):
    """This class is inherited by any class that expected to get assigned
    points from the point database. The point database will interrogate
    the class with these methods to assign points to the PointHandler.

    """

    @property
    @abstractmethod
    def _points_list(self):
        """ Returns the points list of valid points for the object. For
        logic routines, these are often static. For communications routines,
        these will largely accept all values

        """
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def get_point_access(self, name: 'str') -> 'str':
        pass

    @abstractmethod
    def get_point_type(self, name: 'str') -> 'str':
        pass

    @abstractmethod
    def add_point(
      self,
      name: 'str',
      point: 'PointAbstract',
      access: 'str',
      extra_data: 'Dict[str, str]',
    ) -> 'None':
        pass

    @abstractmethod
    def point_name_valid(self, name: 'str') -> 'bool':
        pass

    @abstractmethod
    def interrupt(self, name: 'str', reason: 'Any') -> 'None':
        pass
