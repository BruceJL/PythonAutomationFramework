import datetime
import dateutil.parser
import logging
import smtplib
import time
import traceback
from typing import TYPE_CHECKING, Dict, List, Callable, Any

if TYPE_CHECKING:
    from Supervisory.AlarmHandler import AlarmHandler

logger = logging.getLogger('alarms')

global_alarms = {}  # type: Dict['str', 'Alarm']


class Alarm(object):
    """
    Represents an alarm object, which is an event which requires intervention
    to prevent damage.
    """
    keywords = [
      'description',
      'on_delay',
      'off_delay',
      'more_info',
      'consequences'
    ]

    # notifiers are global alarm watchers for all alarms. They are used for
    # logging and remote alarm notification (e.g. email).
    alarm_notifiers = [] # type: List[Callable[[str], None]]

    alarm_handler = None

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __init__(self, **kwargs: object) -> None:
        """
        The constructor for Alarm class.

        Parameters:
          description (str): A human readable string  detailing the alarm
            condition
          on_delay (float): The time in seconds that the alarm input must
            be active, before it is considered to be a valid alarm.
          off_delay (float): The time in seconds that the alarm must be
            inactive, before it is considered to be a reset alarm.
          consequences (str): The consequences of not responding to this
            alarm in a timely manner.
          more_info (str): Additional information helpful in rectifing the
            alarm condition (e.g. links to: drawings, manuals, or procedures)
        """

        # alarm name in the global alarm dict.
        self._name = ""

        self.description = "Unnamed alarm"  # type: str
        #  Human friendly description

        # The value set by logic to indicating an alarm condition
        self._input = False  # type: bool

        # The value which allows the operator to suppress the alarm
        self.blocked = False  # type: bool

        # Indicates that the alarm has been ack'd by the operator
        self.acknowledged = True  # type: bool

        # Interlock value
        self.enabled = True  # type: bool

        # description of the bad things that will happen if this alarm is not
        # addressed.
        self.consequences = "None"  # type: str

        # Additional info for this alarm
        self.more_info = "None"  # type: str

        self._activation_time = datetime.datetime.now(datetime.timezone.utc)  # type: datetime.datetime
        # The time that the alarm was put into ALARM

        # The time that the alarm was reset
        self._is_reset_time = datetime.datetime.now(datetime.timezone.utc)  # type: datetime.datetime

        # The current state of the alarm.
        # Valid states are: OFF, ON_DELAY, ALARM, OFF_DELAY
        self._state = "OFF"  # type: str

        # Current timer value.
        self._timer = None  # type: float

        # The delay before the alarm is acted upon by logic
        self.on_delay = 0.0  # type: float

        # The delay before the alarm is marked as reset when the input is lowered.
        self.off_delay = 0.0  # type: float

        self._writer = None  # type: object

        # events that will be run on change of state this alarm.
        self._observers = {}  # type: Dict[Callable[[str], None]]

        for kw in kwargs:
            assert kw in self.keywords, \
                "Cannot assign value of '" + kwargs[kw] +  "' to '" \
                + str(kw) + "' property of Alarm, property does not exist"
            setattr(self, kw, kwargs[kw])

    def config(self, n: 'str') -> 'None':
        """
        Sets the name of the alarm as it appears in the global alarm database.

        Parameters:
        n (str): name of the alarm

        """
        self._name = n

    def _get_name(self):
        """ Returns the name of the object with some error checking. """
        assert self._name is not None, \
          "No name has been assigned"
        return self._name

    def _set_name(self, name):
        """ sets the name of the object with some error checking. Likely depreciated """
        try:
            if(self._name is None):
                self._name = name
            else:
                assert self._name == "", \
                  "Alarm has already been assigned a name."
                self._name = name
        except AttributeError:
            self._name = name

    name = property(_get_name, _set_name)

    @property
    def status_string(self) -> str:
        """
        Returns a human readable alarm status string suitable for display on
        an alarm annuciator.

        """
        return "{} {} {}".format(str(self._activation_time), self.description, self.alarm_state)

    @property
    def state(self) -> str:
        """ Gets the state of the alarm. """

        return self._state

    @property
    def data_display_width(self) -> int:
        """
        Gets the number of characters required to display the human
        readable representation of the alarm.
        """
        # returns the length of the longest possible string.
        # Used by the HMI
        return len("ACKNOWLEDGED")

    # Get the time.monotonic() where the alarm should be evaluated for a state
    # change, only makes sense when we're waiting on a on/off timer.
    def _get_wake_time(self) -> float:
        """
        Gets the amount of time from now that the alarm should be re-evaluated
        at. Used by the alarm handler to calculate it's wake up time.

        """
        if "ON_DELAY" == self._state:
            return self.on_delay + self._timer
        elif "OFF_DELAY" == self._state:
            return self.off_delay + self._timer
        else:
            return float('inf')

    wake_time = property(_get_wake_time)

    @property
    def alarm_state(self) -> str:
        """ Gets the human readable state of the alarm. """
        if self.blocked:
            return "BLOCKED"       # ALARM BLOCKED
        if not self.active and self.acknowledged:
            return "NORMAL"        # "ALARM NORMAL"
        elif self.active and not self.acknowledged:
            return "ACTIVE"        # "ALARM ACTIVE"
        elif self.active and self.acknowledged:
            return "ACKNOWLEDGED"  # "ALARM ACKNOWLEDGED"
        elif not self.active and not self.acknowledged:
            return "RESET"         # "ALARM RESET"
        else:
            return "LOGIC FAULT"

    def _set_input(self, b: bool):
        """ Sets the input value of the alarm. """
        if self._input != b:
            self._input = b
            self.evaluate()

    def _get_input(self):
        """ Gets the input value of the alarm. """
        return self._input

    input = property(_get_input, _set_input)

    def acknowledge(self) -> None:
        """ Marks the alarm as acknowledged. """
        self.acknowledged = True
        logger.info("Acknowledging " + self.name)
        if not self.active:
            try:
                Alarm.alarm_handler.remove_active_alarm(self)
            except ValueError:
                logger.error("Tried to acknowledge " + self.description + " but it's not an active alarm")


    def evaluate(self) -> None:
        """
        Evaluates the state of the alarm based upon the input and the time that
        the input was changed. This logic is called whenever the value of the
        input is changed, or the alarm is re-evalutated by the alarm
        supervisor.

        """
        notify = False  # flag to notify logic observers

        # We don't want to have the routine notify all the observers mid
        # evaluation as that could trigger another evaluation before this one is
        # done.
        if self._state == "OFF":
            if self.input and self.enabled:
                if self.on_delay > 0.0:
                    self._state = "ON_DELAY"
                    logger.debug("Alarm: " + self.name + " OFF->ON_DELAY")
                    self._timer = time.monotonic()
                    Alarm.alarm_handler.add_alarm_timer(self)
                else:
                    logger.debug("Alarm: " + self.name + " OFF->ALARM")
                    self._state = "NEW_ALARM"

        # ON_DELAY is used to prevent an alarm from latching in too quickly.
        # This is generally used to prevent alarm chatter.
        if self._state == "ON_DELAY":
            if not self.input or not self.enabled:
                self._state = "OFF"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm: " + self.name + " ON_DELAY->OFF")
            elif time.monotonic() - self._timer >= self.on_delay:
                self._state = "NEW_ALARM"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm: " + self.name + " ON_DELAY->ALARM")

        # NEW_ALARM is a transitory state, setup is done and then the alarm
        # immediately changes to the ALARM state.
        if self._state == "NEW_ALARM":
            self._state = "ALARM"
            notify = True
            if not self.blocked:
                self.acknowledged = False

            Alarm.alarm_handler.add_active_alarm(self)
            self._activation_time = datetime.datetime.now(datetime.timezone.utc)

            # fire off any remote notification if any
            for notifier in Alarm.alarm_notifiers:
                notifier.notify(self, "activated")

        # The ALARM state.
        if self._state == "ALARM":
            if not self.input or not self.enabled:
                if self.off_delay > 0.0:
                    self._state = "OFF_DELAY"
                    self._timer = time.monotonic()
                    Alarm.alarm_handler.add_alarm_timer(self)
                    logger.debug("Alarm: " + self.name + " ALARM->OFF_DELAY")
                else:
                    self._state = "ALARM_RESET"
                    logger.debug("Alarm: " + self.name + " ALARM->OFF")

                    # fire off any remote notification if any
                    for notifier in Alarm.alarm_notifiers:
                        notifier.notify(self, "reset")

        # OFF_DELAY is used to prevent the alarm from clearing too quickly.
        # This is a tool to reduce alarm chatter.
        if self._state == "OFF_DELAY":
            if self.input and self.enabled:
                self._state = "ALARM"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm: " + self.name + " OFF_DELAY->ALARM")
            elif time.monotonic() - self._timer >= self.off_delay:
                self._state = "ALARM_RESET"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm: " + self.name + " OFF_DELAY->OFF")

                # fire off any remote notification if any
                for notifier in Alarm.alarm_notifiers:
                    notifier.notify(self, "reset")

        # ALARM_RESET is a transitory state. Cleans up and returns to the OFF
        # state.
        if self._state == "ALARM_RESET":
            notify = True
            self._state = "OFF"
            self._is_reset_time = datetime.datetime.now(datetime.timezone.utc)
            if self.acknowledged:
                Alarm.alarm_handler.remove_active_alarm(self)

        if notify:
            self._notify_observers()

    def _notify_observers(self):
        """
        Notifies all interested routines that there has been a change in the
        output state of this alarm.

        """
        assert self.name is not None, \
          "Alarm: " + self.description + " defined without name."

        for key, callback in self._observers.items():
            logger.debug("firing callback for " + key + " from " + self.name)
            callback(name=self.name)

    def add_observer(
      self,
      name: 'str',
      observer: 'Callable[str, None]') -> 'None':
        """
        Adds an interested routine to this alarm's observer list. This routine
        will be notified whenever this alarm goes from active to inactive or
        vise-versa.
        """

        self._observers.update({name: observer})
        if self._name is not None:
            logger.info("Observer: " + name + " added to point " + self.name)

    def del_observer(self, name: 'str') -> 'None':
        """ Removes an interseted routine from this alarm's observer list. """
        self._observers.pop(name)
        logger.info("Observer: " + name + " removed from point " + self.name)


    def sanity_check(self):
        """
        Verifies that the alarm's configuration is complete. Throws
        AssertionErrors if the alarm is not setup properly.

        """
        assert "name" in kwargs, \
            "Alarm defined without a name"

        assert "description" in kwargs, \
            "Alarm defined without a description!"

    @property
    def active(self):
        """ Gets the active state of the alarm. """
        return self._state == "ALARM" or self._state == "OFF_DELAY"

    @property
    def alarm(self):
        """
        Gets the annuciator state of the alarm. i.e. should it be displayed on
        an annunciator.
        """
        return self.active and not self.blocked

    @property
    def writer(self):
        """
        Gets the writer for this alarm. The writer is the only object allowed to
        update the input value of the alarm.
        """
        return self._writer

    @writer.setter
    def writer(self, value):
        """ Sets the writer for this alarm. """
        if self._writer is None:
            self._writer = value
        elif value is None:
            self._writer = None
        else:
            raise Exception("Tried to assign two writer values to " + self.description + " !")

    @property
    def hmi_object_name(self) -> str:
        """
        produces a string naming the class used to display this object on the
        HMI.

        """
        return "AlarmWindow"

    def __getstate__(self) -> 'Dict[str, Any]':
        """
        Gets a dict representation of the alarm suitable for JSON
        transport to an HMI client. This function is specified by the
        jsonpickle library to pickle an object.

        Returns:
            dict: a dict of alarm properties.

        """
        d= dict(
          name=self._name,
          description=self.description,
          #_input=self._input,
          blocked=self.blocked,
          acknowledged=self.acknowledged,
          enabled=self.enabled,
          consequences=self.consequences,
          more_info=self.more_info,
          state=self._state,
          timer=self._timer,
          on_delay=self.on_delay,
          off_delay=self.off_delay,
          activation_time=self._activation_time.isoformat(),
          is_reset_time=self._is_reset_time.isoformat(),
        )
        return d

    def __setstate__(self, d) -> 'None':
        """
        Creates an alarm object from a dict representation. This function
        is specified by the jsonpickle library to unpickle an object.

        Parameters:
            dict: JSON dict of alarm properties.

        """
        self._name        = d['name']
        self.description  = d['description']
        self.blocked      = d['blocked']
        self.acknowledged = d['acknowledged']
        self.enabled      = d['enabled']
        self.consequences = d['consequences']
        self.more_info    = d['more_info']
        self._state       = d['state']
        self._timer       = d['timer']
        self.on_delay     = d['on_delay']
        self.off_delay    = d['off_delay']
        self._activation_time = dateutil.parser.parse(d['activation_time'])
        self._is_reset_time   = dateutil.parser.parse(d['is_reset_time'])

    def _get_yaml_dict(self) -> 'Dict[str, Any]':
        """
        Creates a dict representation of the object suitable for YAML storage in
        a configuration file.

        Returns:
            dict: a dict of alarm properties.

        """
        return dict(
          description=self.description,
          consequences=self.consequences,
          more_info=self.more_info,
          on_delay=self.on_delay,
          off_delay=self.off_delay,
        )

    # used to produce a yaml representation for config storage.
    @classmethod
    def to_yaml(cls, dumper, node):
        """
        Gets a representation of this alarm suitable for storage in a yaml file.
        YAML files are used for storing the alarm when stopping and starting then
        process supervisor.

        """

        return dumper.represent_mapping(
          u'!Alarm',
          node._get_yaml_dict())

    @classmethod
    def from_yaml(cls, constructor, node):
        """
        Creates an alarm based upon a YAML representation of the alarm.

        """
        value = constructor.construct_mapping(node)
        return Alarm(**value)
