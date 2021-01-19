from .PointAnalogReadOnly import PointAnalogReadOnly
from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointAnalogAbstract import PointAnalogAbstract
from .PointConfigurationError import PointConfigurationError
from .PointAbstract import PointAbstract

import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict, Any, List

logger = logging.getLogger('controller')


class PointAnalogScaled(
    PointAnalogAbstract,
):
    keywords = [
      'scaling',
      'offset',
      'point',
      'readonly'
    ]  # type: List[str]

    scaling = 1.0  # type: float
    offset = 0.0  # type: float
    _point = None  # type: PointAnalogAbstract
    _name = None  # type: str
    _readonly = False  # type: bool

    def __init__(
      self,
      scaling: 'float',
      offset: 'float',
      point: 'PointAbstract',
      readonly: 'bool',
    ):
        self.scaling = scaling
        self.offset = offset
        self._point = point
        self._readonly = readonly

        if self._readonly:
            self._point.writer = self

    def config(self) -> 'None':
        pass

    def sanity_check(self) -> None:
        assert self._point is not None, \
          "No point assigned to this PointAnalogScaled"

    @property
    def name(self) -> 'str':
        return self._name

    @name.setter
    def name(self, name: 'str') -> 'None':
        self._name = name

    @property
    def u_of_m(self) -> 'str':
        return "counts"

    @property
    def description(self) -> 'str':
        return self._point.description

    @property
    def readonly(self) -> 'bool':
        return self._readonly

    @property
    def forced(self) -> 'bool':
        return self._point.forced

    @property
    def quality(self) -> 'bool':
        return self._point.quality

    @quality.setter
    def quality(self, q: 'bool') -> 'None':
        self._point.quality = q

    @property
    def value(self) -> 'float':
        return (self._point.value - self.offset) / self.scaling

    @value.setter
    def value(self, value: 'float') -> 'None':
        self._point.value = value * self.scaling + self.offset

    @property
    def writer(self):
        return self._point.writer

    @writer.setter
    def writer(self, w) -> 'None':
        self._point.writer = w

    @property
    def next_update(self):
        return self._point.next_update

    @property
    def data_display_width(self) -> 'int':
        return len(self.hmi_value)

    @property
    def last_update(self):
        return self._point.last_update

    @property
    def hmi_value(self) -> 'str':
        return str(self._point.hmi_value)

    @property
    def readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return PointAnalogReadOnly(self)

    @property
    def readwrite_object(self) -> 'PointAnalogScaled':
        if self.readonly:
            assert PointConfigurationError(
                f"point {self._name} cannot be written to as it is marked "
                f"read only. To change it's value, write to {self._point.name}."
            )
        return self

    # HMI object name
    @property
    def hmi_object_name(self) -> 'str':
        return "PointAnalogWindow"

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = {
          'point': self._point,
          'scaling': self.scaling,
          'offset': self.offset,
          'readonly': self.readonly_object,
        }
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        self._point = d['point']
        self.scaling = d['scaling']
        self.offset = d['offset']
        self._readonly = d['readonly']

    # YAML representation for configuration storage.
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = dict(
          point=self._point,
          scaling=self.scaling,
          offset=self.offset,
          readonly=self._readonly
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
