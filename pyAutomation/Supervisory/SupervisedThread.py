import datetime
import threading
import traceback
import time
from collections import deque
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
from pyAutomation.Supervisory.Interruptable import Interruptable


class SupervisedThread(Interruptable, ABC):

    def __init__(self, name: str, loop, period, logger: str) -> None:
        self._name = name
        self.period = period  # in microseconds
        self._logger = logging.getLogger(logger)

        self.sleep_time = 0                # type: 'float'
        self.default_next_run_time = None  # type: 'datetime.datetime'
        self.sweep_time = -1               # type: 'int'
        self.last_run_time = None          # type: 'datetime.datetime'
        self.terminated = False            # type 'bool'
        self._quit = False                 # type 'bool'
        self.condition = threading.Condition()
        self.interrupt_request_deque = deque()
        self.thread = threading.Thread(target=self.thread_loop, args=(loop,))
        self.type = "Control"

    def start(self):
        self.thread.start()

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name

    name = property(_get_name, _set_name)

    def _get_logger(self):
        return self._logger

    logger = property(_get_logger)

    @staticmethod
    def get_lowest_sleep_time(f1: float, f2: float) -> float:
        if f1 is None and f2 is None:
            return None
        elif f1 is None:
            return f2
        elif f2 is None:
            return f1
        elif f1 < f2:
            return f1
        else:
            return f2

    def quit(self):
        self._quit = True
        self.interrupt("Quitting!")

    def interrupt(self, name: 'str'):
        # This method will be called by the program logic so it must block
        # as little as possible.

        assert self.name is not None, \
          'Thread has no name defined.'

        assert name is not None, \
          'Caller has no name defined.'

        self.logger.debug("Interrupt on: %s from %s", self.name, name)
        self.interrupt_request_deque.append(name)

        if self.condition.acquire(timeout=0):
            # Got the lock immediately. Notify the thread.
            self.condition.notify()
            self.condition.release()

    @abstractmethod
    def config(self, data: 'dict') -> None:
        pass

    @abstractmethod
    def loop(self) -> 'float':
        pass

    def thread_loop(self, loop, ):
        try:
            self.logger.info("Starting thread_loop for: %s", self.name)
            self.condition.acquire()

            self.default_next_run_time = datetime.datetime.now()

            while not self._quit:

                # clear out any interrupt requests
                if 0 < len(self.interrupt_request_deque):
                    self.interrupt_request_deque.clear()

                # increment the next_run_time
                if self.period is not None:
                    self.default_next_run_time \
                        += datetime.timedelta(seconds=self.period)

                start_time = time.monotonic()
                self.last_run_time = datetime.datetime.now()
                # run the logic
                self.logger.debug("Running thread: %s", self._name)
                self.sleep_time = self.loop()
                self.logger.debug("Done thread: %s", self._name)
                self.sweep_time = time.monotonic() - start_time

                # setup for sleep.

                if self.sleep_time is None and self.period is not None:
                    # wait the sleep time as defined by the supervisor
                    self.logger.debug(
                      "%s returned a null sleep time, using default sleep" \
                      + "time of %s", self.name, self.period
                    )
                    self.sleep_time = (
                      self.default_next_run_time
                      - datetime.datetime.now()).total_seconds()

                # Check and see if there are interrupts queued (i.e. the routine got an
                # interrupt whilst it was running. If so, restart the routine.
                if 0 < len(self.interrupt_request_deque):
                    self.sleep_time = 0.0
                    self.logger.debug(
                      "%s *NOT* sleeping! pending interrupts",
                      self.name)
                    continue

                # sleep until we receive an interrupt.
                elif self.sleep_time is None:
                    self.logger.debug(
                      "%s sleeping until interrupt", self.name)
                    self.condition.wait(None)

                # Got a valid sleep time?
                elif 0.0 < self.sleep_time:
                    self.logger.debug(
                      "%s sleeping %s",
                      self.name,
                      self.sleep_time,
                    )
                    self.condition.wait(self.sleep_time)

                else:
                    self.logger.debug(
                      "%s *NOT* sleeping! Got a sleep time of %s.",
                      self.name,
                      self.sleep_time
                    )
                    self.sleep_time = 0.0

        except Exception:
            self.logger.error(traceback.format_exc())
            self._quit = True

        finally:
            self.condition.release()
            self.logger.info("Stopping Logic: %s", self.name)
            self.terminated = True

    # values for live object data for transport over JSON to the HMI.
    # N.B. these need to be regular dicts, as the HMI doesn't know about
    # the induvidual processes, and SupervisedThread is abstract.
    @property
    def pickle_dict(self) -> 'Dict[str, Any]':
        return {
          'name': self._name,
          'sleep_time': self.sleep_time,
          'sweep_time': self.sweep_time,
          'last_run_time': self.last_run_time,
          'terminated': self.terminated,
        }

    # values for live object data for transport over JSON.
    def __getstate__(self) -> 'Dict[str, Any]':
        return {
          'name': self._name,
          'sleep_time': self.sleep_time,
          'sweep_time': self.sweep_time,
          'last_run_time': self.last_run_time,
          'terminated': self.terminated,
        }

    def __setstate__(self, d: 'Dict[str, Any]') -> 'None':
        self._name = d['name']
        self.sleep_time = d['sleep_time']
        self.sweep_time = d['sweep_time']
        self.last_run_time = d['last_run_time']
        self.terminated = d['terminated']
