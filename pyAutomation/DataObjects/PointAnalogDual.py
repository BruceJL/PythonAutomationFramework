from datetime import datetime
from typing import Dict, Any, Callable

from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from .PointReadOnlyAbstract import PointReadOnlyAbstract
from pyAutomation.Supervisory.Interruptable import Interruptable


class PointAnalogDual(
  PointReadOnlyAbstract,
  PointAnalogReadOnlyAbstract,
  Interruptable,
):

    _name = None  # type: str
    _value = 0.0  # type: float
    _quality = False  # type: bool
    _last_update = datetime.now()
    _observers = {}  # type: Dict[str, Callable]
    write_request = False

    def __init__(
      self,
      point_1: 'PointAnalogReadOnlyAbstract',
      point_2: 'PointAnalogReadOnlyAbstract',
      description: 'str'
    ) -> 'None':

        self._point_1 = point_1
        self._point_2 = point_2
        self._description = description

    def config(self) -> 'None':
        self._point_1.add_observer(self.name, self.interrupt)
        self._point_2.add_observer(self.name, self.interrupt)
        super().sanity_check()

    # callback sent to points that feed this object.
    def interrupt(
      self,
      name: 'str',
      reason: 'Any',
    ):
        i = 0.0
        j = 0.0
        if self._point_1.quality:
            i += self._point_1.value
            j += 1.0
            if self._point_1.last_update > self._last_update:
                self._last_update = self._point_1.last_update
        if self._point_2.quality:
            i += self._point_2.value
            j += 1.0
            if self._point_2.last_update > self._last_update:
                self._last_update = self._point_2.last_update
        if j > 0.0:
            value = i / j

            self._quality = True
            if self._value != value:
                self._value = value
                self.write_request = True

                for callback in self._observers.values():
                    callback(name + ">" + self.name)
        else:
            self._quality = False

    # get the engineering units value
    @property
    def value(self) -> 'Any':
        return self._value

    # human readable value
    @property
    def human_readable_value(self):
        return str(round(self._value, 2))

    # data display width
    @property
    def data_display_width(self) -> int:
        return 8

    # HMI window type
    @property
    def hmi_object_name(self) -> str:
        # TODO make a PointAnalogDualWindow
        return "PointAnalogDualWindow"

    @property
    def forced(self) -> bool:
        return self._point_1.forced or self._point_2.forced

    @property
    def hmi_value(self) -> str:
        return str(self.value)

    @property
    def last_update(self) -> 'datetime':
        return self._last_update

    @property
    def next_update(self) -> 'datetime':
        if self._point_1.next_update > self._point_2.next_update:
            return self._point_2.next_update
        else:
            return self._point_1.next_update

    @property
    def readonly(self) -> 'bool':
        return True

    @property
    def quality(self):
        return self._quality

    # Unit of measure
    @property
    def u_of_m(self) -> str:
        return self._point_1.u_of_m

    # Description
    @property
    def description(self) -> str:
        return self._description

    # name
    @property
    def name(self) -> 'str':
        return self._name

    @name.setter
    def name(self, value) -> 'None':
        self._name = value

    # Writer
    @property
    def writer(self) -> object:
        return None

    @property
    def readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return self

    @property
    def readwrite_object(self) -> 'PointAnalogDual':
        assert False, "Cannot get a writable object from a PointAnalogDual"

    # The dict property is what is used by jsonpickle to transport the object
    # over the network.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = {
          'name': self._name,
          'value': self._value,
          'quality': self._quality,
          'description': self._description,
          'last_update': self._last_update,
          'point_1': self._point_1,
          'point_2': self._point_2,
        }
        return d

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        self._name        = d['name']
        self._value       = d['value']
        self._description = d['description']
        self._last_update = d['last_update']
        self._quality     = d['quality']
        self._point_1     = d['point_1']
        self._point_2     = d['point_2']

    # YAML representation for configuration storage.
    @property
    def yaml_dict(self) -> 'Dict[str, Any]':
        d = {
          'point_1': self._point_1,
          'point_2': self._point_2,
          'description': self._description,
        }
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalogDual',
          node.yaml_dict)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node, deep=True)

        p = PointAnalogDual(
          description = value['description'],
          point_1     = value['point_1'],
          point_2     = value['point_2'],
        )

        return p
