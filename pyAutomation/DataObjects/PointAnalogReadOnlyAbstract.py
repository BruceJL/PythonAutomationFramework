from abc import ABC, abstractmethod
from .PointReadOnlyAbstract import PointReadOnlyAbstract


class PointAnalogReadOnlyAbstract(PointReadOnlyAbstract, ABC):

    # unit of measure
    @abstractmethod
    def _get_u_of_m(self) -> str:
        pass

    u_of_m = property(_get_u_of_m)
