from abc import ABC
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointAbstract import PointAbstract


class PointAnalogAbstract(PointAbstract, PointAnalogReadOnlyAbstract, ABC):
    pass
