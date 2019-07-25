from .PointAnalogReadOnlyAbstract import PointAnalogReadOnlyAbstract
from datetime import datetime
from typing import List, Callable, Dict, Any


class PointAnalogDual(PointAnalogReadOnlyAbstract):

    def __init__(
          self,
          name: str,
          point_1: PointAnalogReadOnlyAbstract,
          point_2: PointAnalogReadOnlyAbstract,
          description: str) -> None:

        self._name = name
        self._point_1 = point_1
        self._point_2 = point_2
        self._value = 0.0  # type: float
        self._quality = False
        self._description = description
        self._last_update = datetime.now()
        self._observers = []  # type: List[Callable[[str], None]]

        self.write_request = False

        self._point_1.add_observer(self.name, self.update_value)
        self._point_2.add_observer(self.name, self.update_value)
        super().sanity_check()

    # The dict property is what is used by jsonpickle to transport the object over the network.
    def _get__dict__(self) -> 'Dict[str, Any]':
        d = dict(
          _name=self._name,
          _value=self._value,
          _point_1=self._point_1,
          _point_2=self._point_2,
          _description=self._description,
          _quality=self._quality)
        return d

    __dict__ = property(_get__dict__)

    # callback sent to points that feed this object.
    def update_value(self, name):
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

                for callback in self._observers:
                    callback(self.name)
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

    def _get_observers(self):
        return self._observers

    observers = property(_get_observers)

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
