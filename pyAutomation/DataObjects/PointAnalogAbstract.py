from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointAbstract import PointAbstract
from abc import abstractmethod


class PointAnalogAbstract(PointAbstract, PointAnalogReadOnlyAbstract):

    @abstractmethod
    def _get_u_of_m(self) -> str:
        pass

    @abstractmethod
    def _set_u_of_m(self, s):
        pass

    u_of_m = property(_get_u_of_m, _set_u_of_m)

