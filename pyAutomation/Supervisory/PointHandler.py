from abc import ABC
from pyAutomation.DataObjects.Point import Point

class PointHandler(ABC):
    """This class is inherited by any class that expected to get assigned
    points from the point database. The point database will interrogate
    the class with these methods."""

    @property
    def _points_list(self):
        raise NotImplementedError

    @property
    def name(self):
        raise NotImplementedError

    def get_point_access(self, name: 'str') -> 'str':
        assert self.point_name_valid(name), \
          name + " is not a valid point for " + self.name

        if 'access' in  self._points_list[name]:
            return self._points_list[name]['access']

        return None

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
          "{} is not a point in this {}.".format(name, self.name)

        assert type(point) is self._points_list[name][type], \
          "Wrong type of point. Expected {}, got {}".format(
            self._points_list[name][type], type(point))

        assert access is not None \
          or self._points_list[name]['access'] is not None, \
          "No access condition specified."

        self.__dict__[name] = point

    def point_name_valid(self, name: 'str') -> 'bool':
        return name in self._points_list
