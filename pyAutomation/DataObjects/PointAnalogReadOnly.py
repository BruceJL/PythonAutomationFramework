from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from typing import Dict, Any
    from .PointAnalogAbstract import PointAnalogAbstract


class PointAnalogReadOnly(PointAnalogReadOnlyAbstract):

    def __init__(self, point: 'PointAnalogReadOnlyAbstract') -> None:
        self._point = point

    def config(self) -> None:
        pass

    @property
    def name(self) -> str:
        return self._point.name

    @property
    def value(self):
        return self._point.value

    @property
    def hmi_writeable(self):
        return self._point.hmi_writeable

    @property
    def hmi_value(self):
        return self._point.hmi_value

    @hmi_value.setter
    def hmi_value(self, v):
        self._point.hmi_value = v

    @property
    def quality(self) -> bool:
        return self._point.quality

    @property
    def forced(self) -> bool:
        return self._point.forced

    @property
    def writer(self) -> object:
        return self._point.writer

    @property
    def human_readable_value(self):
        return self._point.human_readable_value

    @property
    def data_display_width(self) -> int:
        return self._point.data_display_width

    @property
    def description(self) -> str:
        return self._point.description

    @property
    def last_update(self) -> datetime:
        return self._point.last_update

    @property
    def u_of_m(self) -> 'str':
        return self._point.u_of_m

    @property
    def request_value(self) -> 'str':
        return self._point.request_value

    @request_value.setter
    def request_value(self, value) -> 'None':
        self._point.request_value = value

    # Return a pointer to a read only instance of this object
    @property
    def readonly_object(self) -> 'PointAnalogReadOnly':
        return self

    # Return a pointer to a read/write instance of this object.
    @property
    def readwrite_object(self) -> 'PointAnalogAbstract':
        return self._point.readwrite_object()

    @property
    def hmi_object_name(self):
        return self._point.hmi_object_name

    @property
    def next_update(self):
        return self._point.next_update

    @property
    def readonly(self):
        return True

    # The dict property is what is used by jsonpickle to transport the object
    # over the network.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = dict(point=self._point)
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> None:
        self._point = d['point']

    # YAML representation for configuration storage.
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = {
          'point': self._point,
        }
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalogReadOnly',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node, deep=True)

        p = PointAnalogReadOnly(
          point = value['point'],
         )

        return p
