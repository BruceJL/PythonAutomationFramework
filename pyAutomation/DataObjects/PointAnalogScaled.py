from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointReadOnly import PointReadOnly
import logging
from typing import Callable

logger = logging.getLogger('controller')


class PointAnalogScaled(PointAnalogReadOnlyAbstract):
    keywords = [
      'scaling',
      'offset',
      'point',
    ]

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

    def config(self, n: 'str') -> 'None':
        logger.info("point " + n + " name assigned.")
        self.sanity_check()
        self._name = n

    def sanity_check(self) -> None:
        assert self.point is not None, \
          "No point assigned to this PointAnalogScaled"

    def _get_name(self) -> 'str':
        return self._name

    name = property(_get_name)

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

    quality = property(_get_quality, _set_quality)

    def _get_u_of_m(self) -> 'str':
        return self.point.u_of_m

    u_of_m = property(_get_u_of_m)

    def _get_value(self) -> 'float':
        return (self.point.value - self.offset) / self.scaling

    def _set_value(self, value: float) -> 'None':
        self.point.value = value * self.scaling + self.offset

    value = property(_get_value, _set_value)

    def _get_writer(self):
        return self.point.writer

    def _set_writer(self, w) -> 'None':
        self.point.writer = w

    writer = property(_get_writer, _set_writer)

    def _get_next_update(self):
        return self.point.next_update

    next_update = property(_get_next_update)

    def _get_hmi_value(self) -> 'str':
        return str(self.value)

    hmi_value = property(_get_hmi_value)

    def _get_data_display_width(self) -> 'int':
        return len(hmi_value)

    data_display_width = property(_get_data_display_width)

    def _get_last_update(self):
        return self.point.last_update

    last_update = property(_get_last_update)

    def hmi_object_name(self) -> 'str':
        return "PointAnalogScaledWindow"

    def _get_hmi_value(self) -> 'str':
        return self.hmi_value

    hmi_value = property(_get_hmi_value)

    def _get_human_readable_value(self) -> 'str':
        return self.hmi_value

    human_readable_value = property(_get_human_readable_value)

    def add_observer(self, name: 'str', observer: 'Callable[str,None]') -> 'None':
        self.point.add_observer(name, observer)

    def del_observer(self, name: 'str') -> 'None':
        self.point.del_observer(name)

    def get_readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return PointReadOnly(self)

    def get_readwrite_object(self) -> 'PointAnalogScaled':
        return self

    # Get an object suitable for storage in a yaml file.
    def _get_yamlable_object(self) -> 'PointAbstract':
        return self

    yamlable_object = property(_get_yamlable_object)

    # YAML representation for configuration storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
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
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node)

        return PointAnalogScaled(**value)
