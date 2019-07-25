#!/usr/bin/python3
"""
Created on Apr 16, 2016

@author: Bruce
"""

import datetime
import traceback

from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from .linuxi2c3 import IIC
from .i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler


REG_CO2 = 0x08
CMD_READ_RAM_TWO_BYTES = 0x22
CMD_WRITE_RAM_TWO_BYTES = 0x12
CMD_BACKGROUND_CALIBRATION = 0x7C06
ADDRESS = 0x68


def _validate_checksum(data):
    checksum = 0
    for i in range(0, len(data) - 1):
        checksum += data[i]
    checksum %= 256
    return checksum == data[len(data) - 1]


def _create_check_sum(data):
    checksum = 0
    for i in range(0, len(data)):
        checksum += data[i]
    checksum %= 256
    return checksum


class K30(i2cPrototype, PointHandler):

    points = {
        'point_co2_level': 'get_point_rw',
        'point_calibration_running': 'get_point_rw',
        'point_abc_period': 'get_point_rw',
    }

    parameters = {}

    def __init__(self, name: str, bus: int, logger: str):

        self.bus = bus
        self.is_setup = True
        self.read_state = 0

        self.comm_fail_alarm = Alarm(
            name=self.name + " alarm_co2_comm_fail",
            description="CO2 Sensor Communications Lost",
            on_delay=30.0,
            off_delay=0.,
            consequences="CO2 concentration cannot be measured." +
            " CO2 misting will be inhibited.",
            more_info="Unable to communicate with the K30 CO2 chip.")

        self.dev = None

        self.point_co2_level = None
        self.point_calibration_running = None
        self.point_abc_period = None
        self.consecutive_faults = 0

        super().__init__(
          name=name,
          logger=logger)

    @staticmethod
    def get_remaining_states():
        return 1

    @property
    def has_write_data(self):
        return (
          self.point_calibration_running.request_value is not None
          or self.point_abc_period.request_value is not None
        )

    def _setup(self):
        return True

    def _read_data(self):
        self.logger.debug("Entering function.")
        if self.read_state == 0:
            retry = self.read_co2_levels()
            if not retry:
                self.read_state = 1
        elif self.read_state == 1:
            retry = self.read_abc_period()
            if not retry:
                self.read_state = 0
        self.logger.debug("Leaving function.")
        return 0

    def read_co2_levels(self):
        try:
            # Open up the IIC channel
            self.dev = IIC(ADDRESS, self.bus)

            # Read from RAM (2) three bytes (3) starting at 0x0007, checksum is 0x2A) Get 5 bytes back, 10ms delay
            # between write and read.
            b = self.dev.i2c([0x23, 0x00, 0x07, 0x2A], 5, 0.01)

            if _validate_checksum(b):
                self.meter_control_byte = b[1]
                self.point_calibration_running.value = (self.meter_control_byte and 0x02) > 0
                c = [b[2], b[3]]
                self.point_co2_level.value = int.from_bytes(c, byteorder='big')
                self.comm_fail_alarm.input = False
            else:
                self.comm_fail_alarm.input = True
                self.logger.debug("K30 bad checksum.")
            self.consecutive_faults = 0

        except OSError as e:
            self.comm_fail_alarm.input = True
            self.consecutive_faults += 1
            self.logger.info("I/O fault " + str(self.consecutive_faults) + str(e))

        except Exception as e:
            self.logger.error(traceback.format_exc())

        finally:
            if self.comm_fail_alarm.active:
                self.point_co2_level.quality = False
                self.point_calibration_running.quality = False


            if self.dev is not None:
                self.dev.close()
        return 0

    def read_abc_period(self):
        retry = False
        try:
            # Open up the IIC channel
            self.dev = IIC(ADDRESS, self.bus)
            # Read from RAM (2), two bytes (2) starting at 0x40, checksum is 0x62) Get 5 bytes back, 10ms delay
            # between write and read.
            b = self.dev.i2c([0x22, 0x00, 0x40, 0x62], 4, 0.05)
            if _validate_checksum(b):
                c = [b[1], b[2]]
                self.point_abc_period.value = int.from_bytes(c, byteorder='big')
                self.comm_fail_alarm.input = False
            else:
                self.point_abc_period.quality = False
                self.comm_fail_alarm.input = True
                retry = True
        except OSError as e:
            self.logger.error("I/O error " + str(e))
            self.point_abc_period.quality = False
            retry = True
            self.comm_fail_alarm.input = True
        except Exception as e:
            self.logger.error(traceback.format_exc())
        finally:
            if self.dev is not None:
                self.dev.close()
        return retry

    def _write_data(self):
        self.logger.debug("Entering function.")
        if self.point_calibration_running.request_value:
            self.write_abc_request()
        if self.point_abc_period.request_value:
            self.write_abc_period()
        self.logger.debug("Leaving function.")

    def write_abc_request(self):
        # Baseline calibration request
        if not self.point_calibration_running.value:
            try:
                self.logger.debug("Attempting to write K30 baseline calibration request")
                self.dev = IIC(ADDRESS, self.bus)
                # self.dev.i2c([CMD_WRITE_TWO_BYTES (0x12), MEMORY_LOCATION (0x00, 0x67), CMD_BACKGROUND_CALIBRATION
                # (0x7C 0x06), Checksum],5, 0.01)
                b = self.dev.i2c([0x12, 0x00, 0x67, 0x7C, 0x06, 0xFB], 2, 0.05)
                if _validate_checksum(b):
                    # Was the write successful? see manual page 30.
                    if b[0] == 0x11:
                        self.point_calibration_running.request_value = None
                        self.logger.debug("K30 command successful.")
                    else:
                        self.logger.debug("K30 command unsuccessful.")
                else:
                    self.logger.debug("K30 write bad checksum.")
            except OSError as e:
                self.logger.info("I/O fault " + str(e))
            finally:
                self.dev.close()
        else:
            self.point_calibration_running.request_value = False

    def write_abc_period(self):
        if self.point_abc_period.request_value is not None:
            try:
                self.logger.debug("Attempting to write K30 ABC period")
                self.dev = IIC(ADDRESS, self.bus)
                # self.dev.i2c([CMD_WRITE_TWO_BYTES (0x12), MEMORY_LOCATION (0x00, 0x40), value, Checksum],5, 0.01)
                b = [0x12, 0x00, 0x40]
                b += bytearray(int(self.point_abc_period.request_value).to_bytes(2, byteorder='big'))
                b += bytearray(_create_check_sum(b).to_bytes(1, byteorder='big'))
                self.logger.debug("byte array:" + str(b))
                b = self.dev.i2c(b, 2, 0.01)
                if _validate_checksum(b):
                    # Was the write successful? see manual page 30.
                    if b[0] == 0x11:
                        self.point_abc_period.request_value = None
                        # Queue a read.
                        self.logger.info("K30 write ABC Period command successful.")
                    else:
                        self.logger.info("K30 write ABC Period command unsuccessful.")
                else:
                    self.logger.debug("K30 write ABC Period bad checksum.")
            except OSError as e:
                self.logger.info("I/O fault " + str(e))
            except Exception as e:
                self.logger.error(traceback.format_exc())
            finally:
                self.dev.close()

    def config(self):
        self.device_points = [
            self.point_co2_level,
            self.point_calibration_running,
            self.point_abc_period]
