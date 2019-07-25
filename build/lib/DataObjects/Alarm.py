"""
Created on Apr 16, 2016

@author: Bruce
"""
import datetime
import logging
import smtplib
import time
import traceback
import threading
from typing import TYPE_CHECKING, Dict, List, Callable, Any
from smtplib import SMTPException
from email.mime.text import MIMEText

if TYPE_CHECKING:
    from Supervisory.AlarmHandler import AlarmHandler

logger = logging.getLogger('alarms')

mailhost = "cartman"
mailport = 587
local_hostname = "greenthumb"
mail_sender = "noreply@greenthumb"
mail_receivers = "aero@1045.ca"
global_alarms = {}  # type: Dict['str', 'Alarm']


class Alarm(object):
    keywords = [
        'name',
        'description',
        'on_delay',
        'off_delay',
        'more_info',
        'consequences']

    alarm_handler = None

    @staticmethod
    def set_alarm_handler(handler: 'AlarmHandler'):
        Alarm.alarm_handler = handler

    def assign_vars(self, kwargs, keywords) -> None:
        if "description" not in kwargs:
            raise Exception("Alarm defined without a description!")
        if "name" not in kwargs:
            raise Exception("Alarm defined without a name")
        for kw in kwargs:
            if kw in keywords:
                setattr(self, kw, kwargs[kw])
            else:
                raise Exception("Cannot assign " + str(kw) + " to Alarm, property does not exist")

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __init__(self, **kwargs: object) -> None:
        """
        @keyword description: alarm description
        @keyword on_delay: delay before alarm is raised
        @keyword off_delay: delay before alarm is lowered
        """
        self._name = ""
        self.description = "Unnamed alarm"  # type: str

        # The value set by logic to indicating an alarm condition
        self._input = False  # type: bool

        # The value which allows the operator to suppress the alarm
        self.blocked = False  # type: bool

        # Indicates that the alarm has been ack'd by the operator
        self.acknowledged = True  # type: bool

        # Interlock value
        self.enabled = True  # type: bool

        # description of the bad things that will happen if this alarm is not addressed.
        self.consequences = "None"  # type: str

        # Additional info for this alarm
        self.more_info = "None"  # type: str

        # The time that the alarm was put into ALARM
        self._activation_time = None  # type: datetime.datetime

        # The time that the alarm was reset
        self._is_reset_time = None  # type: datetime.datetime

        # The current state of the alarm.
        self._state = "OFF"  # type: str

        # Current timer value.
        self._timer = None  # type: float

        # The delay before the alarm is acted upon by logic
        self.on_delay = 0.0  # type: float

        # The delay before the alarm is marked as reset when the input is lowered.
        self.off_delay = 0.0  # type: float

        self._writer = None  # type: object

        # events that will be run on change of state this alarm.
        self.observers = []  # type: List[Callable[[str], None]]

        self.assign_vars(kwargs, self.keywords)

    # The dict property is used to wrap up the object for transport over JSON.
    def _get__dict__(self) -> 'Dict[str, Any]':
        return dict(name=self._name,
                    description=self.description,
                    _input=self._input,
                    blocked=self.blocked,
                    acknowledged=self.acknowledged,
                    enabled=self.enabled,
                    consequences=self.consequences,
                    more_info=self.more_info,
                    _state=self._state,
                    _timer=self._timer,
                    on_delay=self.on_delay,
                    off_delay=self.off_delay,
                    _activation_time=self._activation_time,
                    _is_reset_time=self._is_reset_time)

    __dict__ = property(_get__dict__)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if hasattr(self, "name") and "" != self._name:
            del global_alarms[self._name]
        self._name = name
        if "" != self._name:
            global_alarms[self._name] = self

    @property
    def status_string(self) -> str:
        return "{} {} {}".format(str(self._activation_time), self.description, self.alarm_state)

    @property
    def state(self) -> str:
        return self._state

    @property
    def data_display_width(self) -> int:
        # returns the length of the longest possible string.
        # Used by the HMI
        return len("ACKNOWLEDGED")

    # Get the time.monotonic() where the alarm should be evaluated for a state
    # change, only makes sense when we're waiting on a on/off timer.
    def _get_wake_time(self) -> float:
        if "ON_DELAY" == self._state:
            return self.on_delay + self._timer
        elif "OFF_DELAY" == self._state:
            return self.off_delay + self._timer
        else:
            return float('inf')

    wake_time = property(_get_wake_time)

    @property
    def alarm_state(self) -> str:
        if self.blocked:
            return "BLOCKED"  # ALARM BLOCKED
        if not self.active and self.acknowledged:
            return "NORMAL"  # "ALARM NORMAL"
        elif self.active and not self.acknowledged:
            return "ACTIVE"  # "ALARM ACTIVE"
        elif self.active and self.acknowledged:
            return "ACKNOWLEDGED"  # "ALARM ACKNOWLEDGED"
        elif not self.active and not self.acknowledged:
            return "RESET"  # "ALARM RESET"
        else:
            return "LOGIC FAULT"

    @staticmethod
    def send_email(message) -> None:
        try:
            smtp_obj = smtplib.SMTP(mailhost, mailport, local_hostname)
            smtp_obj.sendmail(message['From'], message['To'], str(message))
            smtp_obj.quit()
            logger.info("Successfully sent email")
        except SMTPException:
            logger.error(traceback.format_exc())
            logger.error("Error: unable to send email: " + str(message))

    def notify_email(self, verb) -> None:
        message = MIMEText(
            "Alarm: {} {} \n"
            "Consequences: {} \n"
            "More info: {}".format(
                self.description,
                verb,
                self.consequences,
                self.more_info))

        message['Subject'] = self.description + " alarm"
        message['From'] = mail_sender
        message['To'] = mail_receivers

        # sending e-mail is slow. Do it in another thread.
        t = threading.Thread(target=self.send_email, args=(message,))
        t.start()

    def _set_input(self, b: bool):
        if self._input != b:
            self._input = b
            self.evaluate()

    def _get_input(self):
        return self._input

    input = property(_get_input, _set_input)

    def acknowledge(self) -> None:
        self.acknowledged = True
        logger.info("Acknowledging " + self.name)
        if not self.active:
            try:
                Alarm.alarm_handler.remove_active_alarm(self)
            except ValueError:
                logger.error("Tried to acknowledge " + self.description + " but it's not an active alarm")

    # The logic run every sweep to determine the state of the alarm.
    def evaluate(self) -> None:
        # We don't want to have the routine notify all the observers mid evaluation
        # as that could trigger another evaluation before this one is done.

        notify = False  # flag to notify observers
        if self._state == "OFF":
            if self.input and self.enabled:
                if self.on_delay > 0.0:
                    self._state = "ON_DELAY"
                    logger.debug("Alarm " + self.name + " OFF->ON_DELAY")
                    self._timer = time.monotonic()
                    Alarm.alarm_handler.add_alarm_timer(self)
                else:
                    logger.info("Alarm " + self.name + " OFF->ALARM")
                    self._state = "NEW_ALARM"

        # ON_DELAY is used to prevent an alarm from latching in too quickly. This is
        # generally used to prevent alarm chatter.
        if self._state == "ON_DELAY":
            if not self.input or not self.enabled:
                self._state = "OFF"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm " + self.name + " ON_DELAY->OFF")
            elif time.monotonic() - self._timer >= self.on_delay:
                self._state = "NEW_ALARM"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.info("Alarm " + self.name + " ON_DELAY->ALARM")

        # NEW_ALARM is a transitory state, setup is done and then the alarm immediatly
        # changes to the ALARM state.
        if self._state == "NEW_ALARM":
            self._state = "ALARM"
            notify = True
            if not self.blocked:
                self.acknowledged = False

            Alarm.alarm_handler.add_active_alarm(self)
            self._activation_time = datetime.datetime.now()
            self.notify_email("activated")

        # The ALARM state.
        if self._state == "ALARM":
            if not self.input or not self.enabled:
                if self.off_delay > 0.0:
                    self._state = "OFF_DELAY"
                    self._timer = time.monotonic()
                    Alarm.alarm_handler.add_alarm_timer(self)
                    logger.debug("Alarm " + self.name + " ALARM->OFF_DELAY")
                else:
                    self._state = "ALARM_RESET"
                    self.notify_email("reset")
                    logger.info("Alarm " + self.name + " ALARM->OFF")

        # OFF_DELAY is used to prevent the alarm from clearing too quickly.
        # This is a tool to reduce alarm chatter.
        if self._state == "OFF_DELAY":
            if self.input and self.enabled:
                self._state = "ALARM"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.debug("Alarm " + self.name + " OFF_DELAY->ALARM")
            elif time.monotonic() - self._timer >= self.off_delay:
                self._state = "ALARM_RESET"
                Alarm.alarm_handler.remove_alarm_timer(self)
                logger.info("Alarm " + self.name + " OFF_DELAY->OFF")
                self.notify_email("reset")

        # ALARM_RESET is a transitory state. Cleans up and returns to the OFF state.
        if self._state == "ALARM_RESET":
            notify = True
            self._state = "OFF"
            self._is_reset_time = datetime.datetime.now()
            if self.acknowledged:
                Alarm.alarm_handler.remove_active_alarm(self)

        if notify:
            self._notify_observers()

    def _notify_observers(self):
        for callback in self.observers:
            callback(self.name)

    @property
    def active(self):
        return self._state == "ALARM" or self._state == "OFF_DELAY"

    @property
    def alarm(self):
        return self.active and not self.blocked

    @property
    def writer(self):
        return self._writer

    @writer.setter
    def writer(self, value):
        if self._writer is None:
            self._writer = value
        elif value is None:
            self._writer = None
        else:
            raise Exception("Tried to assign two writer values to " + self.description + " !")

    @property
    def hmi_object_name(self) -> str:
        return "AlarmWindow"
