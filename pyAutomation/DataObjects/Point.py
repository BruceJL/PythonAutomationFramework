import logging
from datetime import datetime, timedelta
from pyAutomation.DataObjects.PointAbstract import PointAbstract
from abc import abstractmethod, ABC
from typing import Dict, TYPE_CHECKING, Any, Callable, List

if TYPE_CHECKING:
    from pyAutomation.DataObjects.Alarm import Alarm

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


class Point(PointAbstract, ABC):

    def __init__(self, **kwargs: object) -> None:

        # human readable description of the point
        self._description = "No description"

        # name of the point in the global point dict.
        self._name = None

        # object that is able to write to this point.
        self._writer = None  # type: object

        # point will accept requested values from non-owner processes.
        self.requestable = False  # type: bool

        # value being requested of the point by a non-owner process
        self._request_value = None  # type: object

        # Point is in a forced state (i.e. the value is only writable from
        # the HMI)
        self._forced = False  # type: bool

        # the time the point was last updated.
        self._last_update = datetime.now()  # type: datetime

        # the time the point should be next updated.
        self.next_update = datetime.now()  # type: datetime

        # should this point persist past a restart?
        self.retentive = False

        # point quality alarm
        self.quality_alarm = None  # type: Alarm

        # point can be edited by HMI
        self.hmi_writeable = False  # type: bool

        # Quality of the point
        self._quality = False  # type: bool

        # The value being requested for this point
        self.write_request = None  # type: object

        # How often the point value should be refreshed.
        self.update_period = None  # type: timedelta

        # The value of the point
        self._value = False  # type: object

        # Objects that are interested in the point
        self._observers = {}  # type: Dict[Callable[[str], None]]

        if 'update_period' in kwargs:
            s = kwargs['update_period']
            if s is not None:
                assert isinstance(s, float),\
                    "invalid update period: " + str(s) \
                    + " supplied for " + kwargs['description']
                t = timedelta(seconds=s)
                kwargs['update_period'] = t

        for kw in kwargs:
            assert kw in self.keywords, \
                "Cannot assign property '" + str(kw) \
                + "' to object " + type(self).__name__ \
                + ", property does not exist"

            setattr(self, kw, kwargs[kw])
            logger.info("assinging property of %s to %s", kwargs[kw], kw)

        logger.info("point '%s'  created.", self.description)

    def config(self, n: 'str') -> 'None':
        # assert n.find('.') == -1, \
        #     "illegal character (.) found in point name: " + n

        logger.info("point %s name assigned.", n)
        self._name = n
        self.sanity_check()

    _keywords = [
      'description',
      'requestable',
      'retentive',
      'hmi_writeable',
      'value',
      'update_period'
    ]

    @abstractmethod
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
        assert self._name is not None, \
          "name is not populated for '" + self.description + "'."
        return self._name

    name = property(_get_name)

    def add_observer(
      self,
      name: 'str',
      observer: 'Callable[str, None]') -> 'None':
        self._observers.update({name: observer})
        if self._name is not None:
            logger.info("observer: %s added to point %s", name, self.name)

    def del_observer(self, name: 'str') -> 'None':
        self._observers.pop(name)
        logger.info("observer: %s removed from point %s", name, self.name)

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
            try:
                if self.update_period is not None\
                  and self.update_period > timedelta.min:
                    while self.next_update < datetime.now():
                        self.next_update += self.update_period
            except AttributeError:
                self.update_period = None

            try:
                if self._value != v:
                    self._value = v
                    self.write_request = True

                    # don't fire callbacks unless it's coming from a valid
                    # thread. (i.e. we're currently starting up.)

                    if self._writer is not None:
                        assert self.name is not None,\
                            self.description \
                            + " attempted callback without identifer."

                        assert self.name != '',\
                            self.description \
                            + " attempted callback without identifer."

                        for callback in self._observers.values():
                            callback(
                              name=self._writer.name + "  > " + self.name
                            )

            except AttributeError:
                self._value = v

    value = property(_get_value, _set_value)

    # last update
    def _get_last_update(self) -> datetime:
        try:
            return self._last_update
        except AttributeError:
            self._last_update = datetime.now()
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
        if self._forced == False:
            # Fire the writer to reset the point to its correct value.
            if self.writer is not None:
                self.writer.interrupt(
                  name = self.name + " unforced",
                  reason = self,
                )

    forced = property(_get_forced, _set_forced)

    # The time that the point should be updated next.
    def _get_next_update(self) -> datetime:
        try:
            if self.update_period is not None:
                return self._next_update
            else:
                return datetime.max
        except AttributeError:
            return datetime.max

    def _set_next_update(self, nu) -> None:
        self._next_update = nu

    next_update = property(_get_next_update, _set_next_update)

    def _get_readonly(self) -> 'bool':
        return False

    readonly = property(_get_readonly)

    # HMI Stuff
    # values from the HMI
    def _get_hmi_value(self) -> str:
        return self.value

    def _set_hmi_value(self, value: str):
        # Note that the behaviour changes depending upon if the point is
        # forced or not. A forced point is written directly to, an unforced
        # point has a entry made in the request field.
        if self._forced:
            if self.value != value:
                logger.error(
                  "Doing a forced write of %s to %s", value, self.description)
                self.forced_value = value
                self._last_update = datetime.now()
                assert self.value == value, \
                    "Forcing " + value + " to " + self.description + " failed."
            else:
                logger.error(
                  "But %s is already %s so no action was taken.",
                  self.description, value)

        # Queue a write of the point if it's an R/W point
        elif self.hmi_writeable:  # and self.requestable:
            logger.info(
              "HMI request_value of %s written to %s", value, self.description)

            if self.requestable:
                # This point is managed by a thread, so submit it to the
                # thread for handling.
                self.request_value = value
            else:
                # This point is not managed by a process, so allow a value to
                # be written to it.
                self.value = value
        else:
            assert False,\
                "HMI tried to write to: " + self.description \
                + " but it's not forced, hmi_writeable, or requestable"

    # hmi_value is access by the sub classes, so we cannot use the property
    # decorator
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
        assert self.requestable,\
          "Logic tried to read the request value of " \
          + self.description + " which does not support requests."
        return self._request_value

    @request_value.setter
    def request_value(self, value):
        assert self.requestable,\
          "Logic tried to write the request value of " \
          + self.description + " which does not support requests."
        self._request_value = value

        if self.writer is not None:
            # Interrupt the thread that owns this point so it can decide
            # what to do with the request.
            self.writer.interrupt(
              name=self.name,
              reason=self,
            )

    # Get and set the owner process
    def _get_writer(self):
        return self._writer

    def _set_writer(self, w):
        assert w is not None,\
           "Tried to assign a null writer to " + self.description

        assert self._writer is None, \
          "Tried to assign " + w.name + " as the writer to point " \
          + self.name + " (" + self.description + ") " \
          + "but it's already claimed by " + self._writer.name + "!"

        self._writer = w

    writer = property(_get_writer, _set_writer)

    # Used to access point quality.
    def _get_quality(self) -> bool:
        return self._quality

    def _set_quality(self, value) -> 'None':
        if not self._forced and self._quality != value:
            self._quality = value
            self._last_update = datetime.now()

    quality = property(_get_quality, _set_quality)

    # Human readable value for HMI usage.
    @property
    def human_readable_value(self) -> 'str':
        if self._value is not None:
            return str(self._value)
        else:
            return "***"

    @property
    def editable_value(self) -> 'str':
        return str(self._value)

    @abstractmethod
    def data_display_width(self) -> int:
        raise NotImplementedError("Not implemented")

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        return dict(
            name=self._name,
            description=self.description,
            value=self._value,
            requestable=self.requestable,
            # _request_value=self._request_value,
            forced=self._forced,
            last_update=self._last_update,
            hmi_writeable=self.hmi_writeable,
            quality=self._quality,
        )

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        self._name = d['name']
        self.description = d['description']
        self._value = d['value']
        self.requestable = d['requestable']
        self._forced = d['forced']
        self._last_update = d['last_update']
        self.hmi_writeable = d['hmi_writeable']
        self._quality = d['quality']

    # used to produce a yaml representation for config storage.
    def _get_yaml_dict(self) -> 'Dict[str, Any]':

        if self.update_period is not None:
            s = self.update_period.total_seconds()
        else:
            s = None

        d = dict(
          requestable=self.requestable,
          retentive=self.retentive,
          hmi_writeable=self.hmi_writeable,
          update_period=s,
          description=self.description,
        )
        if self.retentive:
            d.update(dict(value=self._value))
        return d
