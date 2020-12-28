from abc import abstractmethod, ABC
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

from .PointReadOnlyAbstract import PointReadOnlyAbstract

logger = logging.getLogger('controller')


class PointAbstract(PointReadOnlyAbstract, ABC):
    ''' Extends the PointAbstract method and provides additional writing methods
    such that a concrete read/write point can be derived from this class '''

    # name of the point in the global point dict.
    _name = None

    # Quality of the point
    _quality = False  # type: bool

    # Current value of the point.
    _value = None

    # the time the point should be next updated.
    _next_update = datetime.now()  # type: datetime

    # human readable description of the point
    _description = "No description"

    # the time the point was last updated.
    _last_update = datetime.now()  # type: datetime

    # object that is able to write to this point.
    _writer = None  # type: object

    # value being requested of the point by a non-owner process
    _request_value = None  # type: object

    # point will accept requested values from non-owner processes.
    requestable = False  # type: bool

    # should the value of this point persist past a restart?
    retentive = False

    # Point is in a forced state (i.e. the value is only writable from
    # the HMI/Programmer)
    _forced = False  # type: bool

    # point can be requested by HMI
    hmi_writeable = False  # type: bool

    # This value is queued to be written to a remote device.
    write_request = None  # type: object

    # How often the point value should be refreshed.
    update_period = None  # type: timedelta

    _keywords = [
      'description',
      'requestable',
      'retentive',
      'hmi_writeable',
      'value',
      'update_period'
    ]

    def __init__(self, **kwargs: 'str') -> 'None':

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

    # object configuration keywords.
    def _get_keywords(self) -> List[str]:
        return self._keywords

    keywords = property(_get_keywords)

    # value
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
                        assert self.name is not None, (
                          f'{self.description} attempted callback without '
                          f'identifer.'
                        )

                        assert self.name != '', (
                          f'{self.description} attempted callback without '
                          f'identifer.'
                        )

                        for callback in self._observers.values():
                            callback(
                              name=self._writer.name + "  > " + self.name
                            )

            except AttributeError:
                self._value = v

    value = property(_get_value, _set_value)

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

    # Get the read/write property of this point.
    def _get_readonly(self) -> 'bool':
        return False

    readonly = property(_get_readonly)

    # The Hmi is allowed to edit the point
    @property
    def hmi_editable(self):
        return self.hmi_requestable or self.forced

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

    next_update = property(
        fget=_get_next_update,
        fset=_set_next_update,
    )

    #  description
    def _get_description(self) -> str:
        return self._description

    def _set_description(self, d: str) -> None:
        self._description = d

    description = property(_get_description, _set_description)

    # Human readable value for HMI usage.
    @property
    def human_readable_value(self) -> 'str':
        if self._value is not None:
            return str(self._value)
        else:
            return "***"

    #  forced
    def _get_forced(self) -> bool:
        return self._forced

    def _set_forced(self, value: bool) -> None:
        if not hasattr(self, "_forced"):
            self._forced = value
            self._last_update = datetime.now()
        elif self._forced != value:
            self._forced = value
            self._last_update = datetime.now()
        if self._forced is False:
            # Fire the writer to reset the point to its correct value.
            if self.writer is not None:
                self.writer.interrupt(
                  name = self.name + " unforced",
                  reason = self,
                )

    forced = property(_get_forced, _set_forced)

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

    # name
    def _get_name(self) -> 'str':
        assert self._name is not None, \
          "name is not populated for '" + self.description + "'."
        return self._name

    def _set_name(self, name: 'str') -> 'None':
        assert name is None, ("Cannot reassign name of already named point: "
        + f"{self._name}")
        self._name = name

    name = property(_get_name, _set_name)

    # Used to access point quality.
    def _get_quality(self) -> bool:
        return self._quality

    def _set_quality(self, value) -> 'None':
        if not self._forced and self._quality != value:
            self._quality = value
            self._last_update = datetime.now()

    quality = property(_get_quality, _set_quality)

    # Get and set the requested value from non-owner processes.
    def _get_request_value(self):
        assert self.requestable,\
          "Logic tried to read the request value of " \
          + self.description + " which does not support requests."
        return self._request_value

    def _set_request_value(self, value):
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

    request_value = property(_get_request_value, _set_request_value)

    @property
    def editable_value(self) -> 'str':
        return str(self._value)

    # Get data display width for HMI usage
    @property
    @abstractmethod
    def data_display_width(self) -> 'int':
        pass

    # HMI values
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
