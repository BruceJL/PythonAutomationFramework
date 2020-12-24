from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from pyAutomation.Supervisory.Interruptable import Interruptable
from datetime import datetime
from typing import List, Callable, Dict, Any


class PointAnalogDual(
  PointAnalogReadOnlyAbstract,
  Interruptable):

    def __init__(
      self,
      point_1: PointAnalogReadOnlyAbstract,
      point_2: PointAnalogReadOnlyAbstract,
      description: str
    ) -> 'None':

        self._name = None
        self._point_1 = point_1
        self._point_2 = point_2
        self._value = 0.0  # type: float
        self._quality = False
        self._description = description
        self._last_update = datetime.now()
        self._observers = {}  # type: Dict[Callable[[str], None]]

        self.write_request = False

    def config(self, n: 'str') -> 'None':
        self._name = n
        self._point_1.add_observer(self.name, self.interrupt)
        self._point_2.add_observer(self.name, self.interrupt)
        super().sanity_check()

    # callback sent to points that feed this object.
    def interrupt(self, 
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
    def _get_value(self):
        return self._value

    value = property(_get_value)

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

    def _get_forced(self) -> bool:
        return self._point_1.forced or self._point_2.forced

    forced = property(_get_forced)

    def _get_hmi_value(self) -> str:
        return str(self.value)

    hmi_value = property(_get_hmi_value)

    def _get_last_update(self) -> datetime:
        return self._last_update

    last_update = property(_get_last_update)

    def _get_quality(self):
        return self._quality

    quality = property(_get_quality)

    def add_observer(self, name: 'str', observer: 'Callable[str, None]') -> 'None':
        self._observers.update({name: observer})
        # if self._name is not None:
            # logger.info("observer: " + name + " added to point " + self.name)

    def del_observer(self, name: 'str') -> 'None':
        self._observers.pop(name)
        # logger.info("observer: " + name + " removed from point " + self.name)

    # Unit of measure
    def _get_u_of_m(self) -> str:
        return self._point_1.u_of_m

    u_of_m = property(_get_u_of_m)

    # Description
    def _get_description(self) -> str:
        return self._description

    description = property(_get_description)

    # name
    def _get_name(self):
        return self._name

    name = property(_get_name)

    # Writer
    def _get_writer(self) -> object:
        return None

    writer = property(_get_writer)

    def get_readonly_object(self) -> 'PointAnalogReadOnlyAbstract':
        return self

    def get_readwrite_object(self) -> 'PointAnalogDual':
        assert False, "Cannot get a writable object from a PointAnalogDual"

    # The dict property is what is used by jsonpickle to transport the object over the network.
    def __getstate__(self) -> 'Dict[str, Any]':
        d = {
          'name':        self._name,
          'value':       self._value,
          'quality':     self._quality,
          'description': self._description,
          'last_update': self._last_update,
          'point_1':     self._point_1,
          'point_2':     self._point_2,
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

    # Get an object suitable for storage in a yaml file.
    def _get_yamlable_object(self) -> 'PointAbstract':
        return self

    yamlable_object = property(_get_yamlable_object)

    # YAML representation for configuration storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        d = {
          'point_1':     self._point_1.yamlable_object,
          'point_2':     self._point_2.yamlable_object,
          'description': self._description,
        }
        return d

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        return dumper.represent_mapping(
          u'!PointAnalogDual',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_mapping(node, deep=True)

        p =  PointAnalogDual(
          description = value['description'],
          point_1     = value['point_1'],
          point_2     = value['point_2'],
        )

        return p
