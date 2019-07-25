import logging
import threading
import time
import typing
from .SupervisedThread import SupervisedThread

if typing.TYPE_CHECKING:
    from DataObjects.Alarm import Alarm

logger = logging.getLogger('alarms')


class AlarmHandler(SupervisedThread):

    def __init__(self, logger, name, period):

        # this condition controls access to the list of active alarms.
        self.active_alarm_list_condition = threading.Condition()

        # alarm_cleanup condition is used to control access to active alarm_timer_remove_list.
        self.alarm_timer_list_remove_condition = threading.Condition()

        # alarm_cleanup condition is used to control access to active alarm_timer_remove_list.
        self.alarm_timer_list_add_condition = threading.Condition()

        # flag used to indicate that we need to restart the thread.
        self.restart_flag_condition = threading.Condition()

        self.active_alarm_timer_list = []
        self.active_alarm_timer_remove_list = []
        self.active_alarm_timer_add_list = []
        self.active_alarm_list = []
        self.next_alarm = None
        self.active_alarm_timer_list_count = 0  # type: int

        super().__init__(
            name=name,
            logger=logger,
            period=period,
            loop=self.loop
        )

    def add_active_alarm(self, a: 'Alarm'):
        # This method will be called by the program logic so it must block
        # as little as possible.
        with self.active_alarm_list_condition:
            if a not in self.active_alarm_list:
                logger.info("Adding " + a.name)
                self.active_alarm_list.append(a)

    def remove_active_alarm(self, a: 'Alarm'):
            # This method will be called by the program logic so it must block
        # as little as possible.
        with self.active_alarm_list_condition:
            logger.info("Removing " + a.name)
            self.active_alarm_list.remove(a)

        logger.info("Active alarm list contains:")
        for a in self.active_alarm_list:
            logger.info(a.name)

    def add_alarm_timer(self, a: 'Alarm'):
        # This method will be called by the program logic so it must block
        # as little as possible.
        with self.alarm_timer_list_add_condition:
            self.active_alarm_timer_list.append(a)

        # Run the loop again.
        self.interrupt(name="AlarmHandler")

    def remove_alarm_timer(self, a: 'Alarm'):
        # This method will be called by the program logic so it must block
        # as little as possible.
        with self.alarm_timer_list_remove_condition:
            self.active_alarm_timer_remove_list.append(a)

        # Run the loop again.
        self.interrupt(name="AlarmHandler")

    def count_alarm_timer_list(self) -> int:
        with self.alarm_timer_list_add_condition:
            return len(self.active_alarm_timer_list)

    def loop(self):
        # process the removal list.
        with self.alarm_timer_list_remove_condition:
            for a in self.active_alarm_timer_remove_list:
                self.active_alarm_timer_list.remove(a)
            self.active_alarm_timer_remove_list.clear()

        # process the add list.
        with self.alarm_timer_list_add_condition:
            for a in self.active_alarm_timer_add_list:
                self.active_alarm_timer_list.append(a)
            self.active_alarm_timer_add_list.clear()

        # count the alarm lists.
        self.active_alarm_timer_list_count = len(self.active_alarm_timer_list)

        sleep_time = None
        for alarm in self.active_alarm_timer_list:
            if alarm.wake_time is not None:
                t = alarm.wake_time - time.monotonic()
                if t <= 0:
                    alarm.evaluate()
                elif sleep_time is None or t < sleep_time:
                    sleep_time = t

        return sleep_time
