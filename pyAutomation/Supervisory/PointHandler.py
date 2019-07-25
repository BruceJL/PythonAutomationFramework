from abc import ABC, abstractmethod
from pyAutomation.DataObjects.Point import Point

class PointHandler(ABC):

    def get_point_access(self, name: str) -> str:
        assert self.point_name_valid(name), \
          name + " is not a valid point for " + self.name

        if 'access' in  self._points_list[name]:
            return self._points_list[name]['access']
        else:
            return None

    def get_point_type(self, name: str) -> str:
        assert self.point_name_valid(name), \
          name + " is not a valid point for " + self.name

        return self._points_list[name]['type']

    def add_point(self, name: str, point: Point, access: str):
        assert name in _points_list, \
          "No such point in this routine."

        assert type(point) is _points_list[name][type], \
          "Wrong type of point."

        assert access is not None or _points_list[name]['access'] is not None, \
          "No access condition specified."

        self.__dict__[name] = point

    def point_name_valid(self, name: str) -> bool:
        return name in self._points_list
