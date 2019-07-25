"""
Created on 2017-09-05

@author: Bruce
"""

from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointReadOnly import PointReadOnly

class PointAnalogScaled(object):
    keywords = ['scaling', 'offset', 'point', 'name']

    def __init__(self, **kwargs):
        self.scaling = 1.0
        self.offset = 0.0
        self.point = None
        self.name = None

        for kw in kwargs:
            assert kw in self.keywords, \
              "Cannot assign " + str(kw) \
              + " to PointAnalogScaled, property does not exist"

            setattr(self, kw, kwargs[kw])

        assert self.point is not None, \
          "No point assigned to this PointAnalogScaled"

    # YAML representation for configuration storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = dict(
          name=self.name,
          point=self.point,
          scaling=self.scaling,
          offset=self.offset,
        )
        return d

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

    def get_readonly_object(self) -> 'PointReadOnlyAbstract':
        return self

    # TODO sloppy, fix up.
    def get_readwrite_object(self) -> 'PointAbstract':
        return self

    def get_yaml_object(self) -> 'PointAnalogScaled':
        return self

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalogScaled',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)

        return PointAnalogScaled(**value)
