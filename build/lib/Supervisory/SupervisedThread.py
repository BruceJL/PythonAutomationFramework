import datetime
import threading
import traceback
import time
from collections import deque
from abc import ABC, abstractmethod
from typing import Dict, Any


class SupervisedThread(ABC):

    def __init__(self, name, loop, period, logger) -> None:
        self.name = name
        self.period = period  # in microseconds

        self.logger = logger
        self.sleep_time = 0  # type: float
        self.default_next_run_time = None  # type: datetime.datetime
        self.sweep_time = -1  # type: int
        self.last_run_time = None  # type: datetime.datetime
        self.condition = threading.Condition()
        self.interrupt_request_deque = deque()
        self._quit = False
        self.terminated = False

        self.thread = threading.Thread(target=self.thread_loop, args=(loop,))

    def start(self):
        self.thread.start()

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

    def interrupt(self, name: str):
        # This method will be called by the program logic so it must block
        # as little as possible.
        self.logger.debug("Interrupt on:" + self.name)
        self.interrupt_request_deque.append(name)

        if self.condition.acquire(timeout=0):
            # Got the lock immediately. Notify the thread.
            self.condition.notify()
            self.condition.release()

    @abstractmethod
    def loop(self) -> float:
        pass

    def thread_loop(self, loop, ):
        try:
            self.logger.info("Starting Logic: " + self.name)
            self.condition.acquire()

            self.default_next_run_time = datetime.datetime.now()

            while not self._quit:

                # clear out any interrupt requests
                if 0 < len(self.interrupt_request_deque):
                    self.interrupt_request_deque.clear()

                # increment the next_run_time
                if self.period is not None:
                    self.default_next_run_time += self.period

                start_time = time.monotonic()
                self.last_run_time = datetime.datetime.now()
                # run the logic
                self.sleep_time = self.loop()
                self.sweep_time = time.monotonic() - start_time

                # setup for sleep.

                if self.sleep_time is None and self.period is not None:
                    # wait the sleep time as defined by the supervisor
                    self.sleep_time = (
                        self.default_next_run_time
                        - datetime.datetime.now()).total_seconds()

                # Check and see if there are interrupts queued (i.e. the routine got an
                # interrupt whilst it was running. If so, restart the routine.
                if 0 < len(self.interrupt_request_deque):
                    self.sleep_time = 0.0
                    self.logger.debug(self.name + " *NOT* sleeping! pending interrupts")
                    continue

                # sleep until we receive an interrupt.
                elif self.sleep_time is None:
                    self.logger.debug(self.name + " sleeping until interrupt")
                    self.condition.wait(None)

                # Got a valid sleep time?
                elif 0.0 < self.sleep_time:
                    self.logger.debug(self.name + " sleeping " + str(self.sleep_time))
                    self.condition.wait(self.sleep_time)

                else:
                    self.sleep_time = 0.0
                    self.logger.debug(self.name + " *NOT* sleeping! Got negative sleep time.")

        except Exception:
            self.logger.error(traceback.format_exc())
            self._quit = True

        finally:
            self.condition.release()
            self.logger.info("Stopping Logic: " + self.name)
            self.terminated = True

    def _get__dict__(self) -> 'Dict[str, Any]':
        return dict(
            name=self.name,
            sleep_time=self.sleep_time,
            sweep_time=self.sweep_time,
            last_run_time=self.last_run_time,
            terminated=self.terminated)

    __dict__ = property(_get__dict__)


