from abc import ABC
from pyAutomation.DataObjects.Point import Point
from pyAutomation.Supervisory.Interruptable import Interruptable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any


class PointHandler(Interruptable, ABC):
    """This class is inherited by any class that expected to get assigned
    points from the point database. The point database will interrogate
    the class with these methods."""

    @property
    def _points_list(self):
        pass

    @property
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
      point: 'Point',
      access: 'str',
      extra_data: 'Dict[str, str]',
    ) -> None:
        assert name in self._points_list, \
          f"{name} is not a point in this {self.name}."

        assert type(point) is self._points_list[name][type], \
          f"Wrong type of point. Expected {self._points_list[name][type]},"
          f"got {type(point)}"

        assert access is not None \
          or self._points_list[name]['access'] is not None, \
          "No access condition specified."

        self.__dict__[name] = point

    def point_name_valid(self, name: 'str') -> 'bool':
        return name in self._points_list

    def interrupt(self, name: 'str', reason: 'Any') -> 'None':
        self._interrupt(name, reason)
