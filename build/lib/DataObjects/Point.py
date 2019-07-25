import logging
from datetime import datetime, timedelta
from .PointAbstract import PointAbstract
from abc import abstractmethod
from typing import Dict, TYPE_CHECKING, Any, Callable, List

if TYPE_CHECKING:
    from DataObjects.Alarm import Alarm

logger = logging.getLogger('controller')

global_points = {}  # type: Dict[str, PointAbstract]


class Value(object):

    def __init__(self) -> None:
        self._value = None

    @property
    def float(self) -> float:
        return float(self._value)

    @float.setter
    def float(self, f: float):
        self._value = f

    @property
    def int(self) -> int:
        return int(self._value)

    @int.setter
    def int(self, i: int):
        self._value = i

    @property
    def str(self) -> str:
        return str(self._value)

    @str.setter
    def str(self, s: str):
        self._value = s


class Point(PointAbstract):

    def __init__(self) -> None:
        super().__init__()
        self._name = ""
        self._description = "No description"  # type: str
        self._writer = None   # type: object  # object that is able to write to this point.

        # point will accept requested values from non-owner processes.
        self.requestable = False  # type: bool

        # Point has a pending write to a device
        self._request_value = None  # type: object

        # Point is in a forced state (i.e. the value is only writable from the HMI
        self._forced = False  # type: bool

        # the time the point was last updated.
        self._last_update = datetime.now()  # type: datetime

        # point quality alarm
        self.quality_alarm = None  # type: Alarm

        # point can be edited by HMI
        self.hmi_writeable = False  # type: bool

        # Quality of the point
        self._quality = False  # type: bool

        # The value being requested for this point
        self.write_request = None  # type: object

        global_points[self.name] = self
        self.update_period = None  # type: timedelta

        self._value = False  # type: object

        # Objects that are interested in the point
        self._observers = []  # type: List[Callable[[str], None]]

    def _get__dict__(self) -> 'Dict[str, Any]':
        return dict(
            name=self._name,
            description=self.description,
            _value=self._value,
            requestable=self.requestable,
            _request_value=self._request_value,
            forced=self._forced,
            last_update=self._last_update,
            hmi_writeable=self.hmi_writeable,
            _quality=self._quality)

    __dict__ = property(_get__dict__)

    _keywords = [
        'name',
        'description',
        'requestable',
        'hmi_writeable',
        '_value',
        'update_period']

    def _get_keywords(self) -> List[str]:
        return self._keywords

    keywords = property(_get_keywords)

    # description
    def _get_description(self) -> str:
        return self._description

    def _set_description(self, d: str) -> None:
        self._description = d

    description = property(_get_description, _set_description)

    # name
    def _get_name(self) -> str:
        return self._name

    def _set_name(self, name):
        if hasattr(self, "name") and "" != self._name:
            del global_points[self.name]

        self._name = name

        if "" != self._name:
            global_points[self.name] = self

    # name is access by the sub classes, so we cannot use the property decorator
    name = property(_get_name, _set_name)

    # observers
    def _get_observers(self) -> List[Callable[[str], None]]:
        return self._observers

    observers = property(_get_observers)

    # value
    # Used to access to the point from the owner process.
    def _get_value(self) -> object:
        if self._quality:
            return self._value
        else:
            return 0

    def _set_value(self, v):
        if not self.forced:
            self._quality = True
            self.last_update = datetime.now()
            if self._value != v:
                self._value = v
                self.write_request = True

                for callback in self.observers:
                    callback(self.name)

    value = property(_get_value, _set_value)

    # last update
    def _get_last_update(self) -> datetime:
        return self._last_update

    def _set_last_update(self, d: datetime):
        self._last_update = d

    last_update = property(_get_last_update, _set_last_update)

    # forced
    def _get_forced(self) -> bool:
        return self._forced

    def _set_forced(self, value: bool) -> None:
        if not hasattr(self, "_forced"):
            self._forced = value
            self._last_update = datetime.now()
        elif self._forced != value:
            self._forced = value
            self._last_update = datetime.now()

        # if the point is no longer forced, re-run the writer to get an updated value.
        if not self._forced:
            if self._writer is not None:
                self._writer.interrupt(self.name)


    forced = property(_get_forced, _set_forced)

    # The time that the point should be updated next.
    def _get_next_update(self) -> datetime:
        if self.update_period is not None:
            return self._last_update + self.update_period
        else:
            return datetime.max

    next_update = property(_get_next_update)

    # values from the HMI
    def _get_hmi_value(self) -> str:
        return self.value

    def _set_hmi_value(self, value: str):
        # Note that the behaviour changes depending upon if the point is forced or not.
        # A forced point is written directly to, an unforced point has a entry made in the
        # request field.
        if self._forced:
            if self.value != value:
                logger.debug(
                    "Doing a forced write of " + str(value) + " to "
                    + self.description)
                self.forced_value = value
                self._last_update = datetime.now()
                assert self.value == value, "Forcing " + value + " to " \
                                            + self.description + " failed."
            else:
                logger.debug("But " + self.description + " is already "
                             + str(value) + " so no action was taken.")

        # Queue a write of the point if it's an R/W point
        elif self.hmi_writeable:  # and self.requestable:
            logger.debug(
                "HMI request_value of " + str(value) + " written to "
                + self.description)
            if self.requestable:
                # This point is managed by a thread, so submit it to the thread for handling.
                self.request_value = value
            else:
                # This point is not managed by a process, so allow a value to be written to it.
                self.value = value
        else:
            raise Exception(
                "HMI tried to write to: " + self.description
                + " but it's not forced, hmi_writeable, or requestable")

    # hmi_value is access by the sub classes, so we cannot use the property decorator
    hmi_value = property(_get_hmi_value, _set_hmi_value)

    # The Hmi is allowed to edit the point
    @property
    def hmi_editable(self):
        return self.hmi_writeable or self.forced

    # forced_value - mechanism for writing forces on values that are stored
    # managled internally.
    @property
    def forced_value(self):
        return self._value

    @forced_value.setter
    def forced_value(self, value):
        self._value = value

    # Get and set the requested value from non-owner processes.
    @property
    def request_value(self):
        if self.requestable:
            return self._request_value
        else:
            raise Exception(
                "Logic tried to read the request value of "
                + self.description + " which does not support requests.")

    @request_value.setter
    def request_value(self, value):
        if self.requestable:
            self._request_value = value

            if self.writer is not None:
                # Interrupt the thread that owns this point so it can decide
                # what to do with the request.
                self._writer.interrupt(self.name)
        else:
            raise Exception(
                "Logic tried to write a request value to "
                + self.description + " which does not support requests")

    # Get and set the owner process
    def _get_writer(self):
        return self._writer

    def _set_writer(self, w):
        if self._writer is None:
            self._writer = w
        elif w is None:
            self._writer = None
        else:
            raise Exception(
                "Tried to assign two writer values to Point "
                + self.description + " but it's already " + self._writer.name + "!")

    writer = property(_get_writer, _set_writer)

    # Used to access point quality.
    def _get_quality(self) -> bool:
        return self._quality

    def _set_quality(self, value) -> None:
        if not self._forced and self._quality != value:
            # logger.debug("Updating quality of " + self.description + " to " + str(value))
            self._quality = value
            self._last_update = datetime.now()

    quality = property(_get_quality, _set_quality)

    # Human readable value for HMI usage.
    @property
    def human_readable_value(self) -> str:
        return str(self._value)

    # Get data display width for HMI usage
    @property
    @abstractmethod
    def data_display_width(self) -> int:
        pass
