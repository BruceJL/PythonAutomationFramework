"""
Created on Apr 16, 2016

@author: Bruce
"""

import time
import logging
from typing import Dict
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
import threading

logger = logging.getLogger('controller')


class InductiveLoad(object):

    inrush_active = {}  # type: Dict[str, float]
    thread_condition = threading.Condition()

    def __init__(
            self,
            description: str,
            inrush_delay: float,
            cool_down_delay: float,
            point_run: PointDiscrete,
            inrush_circuit: str) -> None:

        self.description = description
        self.mode = "OFF"  # type: str
        self.inrush_delay = inrush_delay
        self.cool_down_delay = cool_down_delay
        self.point_run = point_run  # type: PointDiscrete
        self.start_time = None  # type: float
        self.stop_time = None  # type: float
        self.last_run_period = 0   # type: float
        self.last_off_period = 0  # type: float
        self.timer = None  # type: float
        self.request = False  # type: bool
        self.inrush_circuit = inrush_circuit

        InductiveLoad.thread_condition.acquire()
        if self.inrush_circuit not in InductiveLoad.inrush_active:
            InductiveLoad.inrush_active[self.inrush_circuit] = 0
        InductiveLoad.thread_condition.release()

    def run(self, request: bool) -> None:
        self.request = request

    def evaluate(self) -> float:
        InductiveLoad.thread_condition.acquire()
        if "OFF" == self.mode or "WAITING" == self.mode:
            if self.request:
                if 0 == InductiveLoad.inrush_active[self.inrush_circuit]:
                    logger.info(self.description + " -> INRUSH")
                    self.mode = "INRUSH"
                    self.timer = time.monotonic()
                    self.start_time = time.monotonic()
                    if self.stop_time is not None:
                        self.last_off_period = self.start_time - self.stop_time
                    InductiveLoad.inrush_active[self.inrush_circuit] = self.inrush_delay
                else:
                    if "WAITING" != self.mode:
                        self.mode = "WAITING"
                        logger.info(self.description + " -> WAITING")

        elif self.mode == "INRUSH":
            if time.monotonic() - self.timer > self.inrush_delay:
                logger.info(self.description + " -> ON")
                self.mode = "ON"
                InductiveLoad.inrush_active[self.inrush_circuit] = 0
            else:
                InductiveLoad.inrush_active[self.inrush_circuit] = \
                    time.monotonic() - self.timer

        elif self.mode == "ON":
            if not self.request:
                logger.info(self.description + " -> COOLDOWN")
                self.mode = "COOLDOWN"
                self.timer = time.monotonic()
                self.stop_time = time.monotonic()
                self.last_run_period = self.stop_time - self.start_time

        elif self.mode == "COOLDOWN":
            if time.monotonic() - self.timer > self.cool_down_delay:
                logger.info(self.description + " -> OFF")
                self.mode = "OFF"
        InductiveLoad.thread_condition.release()

        if self.mode == "OFF":
            self.point_run.value = False
        elif self.mode == "INRUSH":
            self.point_run.value = True
        elif self.mode == "ON":
            self.point_run.value = True
        elif self.mode == "COOLDOWN":
            self.point_run.value = False
        elif self.mode == "WAITING":
            self.point_run.value = False
        else:
            self.point_run.value = False

        return self.sleep_time

    @property
    def is_on(self) -> bool:
        return self.point_run.value

    @property
    def run_timer(self) -> float:
        if "ON" == self.mode:
            return time.monotonic() - self.start_time
        else:
            return 0

    @property
    def sleep_time(self) -> float:
        if(
          "COOLDOWN" == self.mode
          or self.mode == "INRUSH"):
            return time.monotonic() - self.timer

        elif(
          "OFF" == self.mode
          or "ON" == self.mode):
            return None

        elif "WAITING" == self.mode:
            return self.inrush_active[self.inrush_circuit]
