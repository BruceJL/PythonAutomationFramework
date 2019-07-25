"""
Created on 2017-09-05

@author: Bruce
"""


class PointAnalogScaled(object):
    keywords = ['scaling', 'offset', 'point']

    def __init__(self, **kwargs):
        self.scaling = 1.0
        self.offset = 0.0
        self.point = None
        for kw in kwargs:
            if kw in self.keywords:
                setattr(self, kw, kwargs[kw])
            else:
                raise Exception(
                    "Cannot assign " + str(kw) + " to PointAnalogScaled, property does not exist")
        if self.point is None:
            raise Exception("No point assigned to this PointAnalogScaled")

    # access the point from I/O drivers

    @property
    def value(self) -> float:
        return (self.point.value - self.offset) / self.scaling

    @value.setter
    def value(self, value: float):
        self.point.value = value * self.scaling + self.offset

    # quality
    @property
    def quality(self):
        return self.point.quality

    @quality.setter
    def quality(self, v: bool):
        self.point.quality = v

    @property
    def next_update(self):
        return self.point.next_update
