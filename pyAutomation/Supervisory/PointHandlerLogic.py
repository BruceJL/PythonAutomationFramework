from abc import ABC, abstractmethod
from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.Supervisory.PointHandler import PointHandler
from pyAutomation.Supervisory.ConfigurationException import \
  ConfigurationException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any


class PointHandlerLogic(PointHandler, ABC):
    """This class provides a number of populated methods for PointHandlers that
    behave as logic processors (as opposed to communications routines), as they
    typically have a static point list that this accept.

    This class is inherited by any class that expected to get assigned
    points from the point database. The point database will interrogate
    the class with these methods to assign points to the PointHandler.

    """

    @property
    @abstractmethod
    def _points_list(self):
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    def get_point_access(self, name: 'str') -> 'str':
        assert self.point_name_valid(name), \
          name + " is not a valid point for " + self.name

        if 'access' in  self._points_list[name]:
            return self._points_list[name]['access']

        assert False, (f'No valid r/w property assigned to point: {name}')

    def get_point_type(self, name: 'str') -> 'str':
        assert self.point_name_valid(name), \
          name + " is not a valid point for " + self.name

        return self._points_list[name]['type']

    def add_point(
      self,
      name: 'str',
      point: 'PointAbstract',
      access: 'str',
      extra_data: 'Dict[str, str]',
    ) -> 'None':
        if name not in self._points_list:
            raise ConfigurationException(
              f"{name} is not a point in this {self.name}."
            )

        if type(point) is not self._points_list[name][type]:
            raise ConfigurationException(
              f"Wrong type of point. Expected {self._points_list[name][type]},"
              f"got {type(point)}"
            )

        if access is None or self._points_list[name]['access'] is None:
            raise ConfigurationException("No access condition specified.")

        self.__dict__[name] = point

    def point_name_valid(self, name: 'str') -> 'bool':
        return name in self._points_list

    def interrupt(self, name: 'str', reason: 'Any') -> 'None':
        self._interrupt(name, reason)
