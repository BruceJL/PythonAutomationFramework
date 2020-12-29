from .PointAnalogReadOnly import PointAnalogReadOnly
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointAnalogAbstract import PointAnalogAbstract

import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict, Any, List

logger = logging.getLogger('controller')


class PointAnalogScaled(PointAnalogAbstract):
    _keywords = [
      'scaling',
      'offset',
      'point',
    ]  # type: List[str]

    def __init__(self, **kwargs):
        self.scaling = 1.0
        self.offset = 0.0
        self.point = None
        self._name = None
        self._observers = {}

        for kw in kwargs:
            assert kw in self.keywords, \
              "Cannot assign " + str(kw) \
              + " to PointAnalogScaled, property does not exist"
            setattr(self, kw, kwargs[kw])

    def config(self) -> 'None':
        self.sanity_check()

    def sanity_check(self) -> None:
        assert self.point is not None, \
          "No point assigned to this PointAnalogScaled"

    def _get_description(self) -> 'str':
        return self.point.description

    description = property(_get_description)

    def _get_forced(self) -> 'bool':
        return self.point.forced

    forced = property(_get_forced)

    def _get_quality(self) -> 'bool':
        return self.point.quality

    def _set_quality(self, q: 'bool') -> 'None':
        self.point.quality = q

    def _get_value(self) -> 'float':
        return (self.point.value - self.offset) / self.scaling

    def _set_value(self, value: float) -> 'None':
        self.point.value = value * self.scaling + self.offset

    def _get_writer(self):
        return self.point.writer

    def _set_writer(self, w) -> 'None':
        self.point.writer = w

    writer = property(_get_writer, _set_writer)

    def _get_next_update(self):
        return self.point.next_update

    next_update = property(_get_next_update)

    def _get_data_display_width(self) -> 'int':
        return len(self.hmi_value)

    def _get_last_update(self):
        return self.point.last_update

    last_update = property(_get_last_update)

    def _get_hmi_value(self) -> 'str':
        return self.hmi_value

    hmi_value = property(_get_hmi_value)

    def _get_human_readable_value(self) -> 'str':
        return self.hmi_value

    @property
    def readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return PointAnalogReadOnly(self)

    @property
    def readwrite_object(self) -> 'PointAnalogScaled':
        return self

    # HMI object name
    def _get_hmi_object_name(self) -> 'str':
        return "PointAnalogWindow"

    # YAML representation for configuration storage.
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = dict(
          point=self.point,
          scaling=self.scaling,
          offset=self.offset,
        )
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalogScaled',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)

        return PointAnalogScaled(**value)
